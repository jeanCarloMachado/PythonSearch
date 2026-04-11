"""
LLM-assisted deletion of a single entry from Python Search entry sources.

Flow: ripgrep-scoped files → ``EntriesLoader.count_entries_from_disk()`` (reload + same dict as
Search UI) → OpenAI returns a short sed/perl snippet → apply → compile → ``EntriesLoader``
before/after delta (same as Search UI; no AST count fallback) → git restore hint on failure.

Set ``PYTHONSEARCH_DELETE_DEBUG=1`` for extra logs (ripgrep paths, OpenAI JSON preview).
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

MAX_SOURCE_BYTES = int(os.environ.get("PYTHONSEARCH_DELETE_MAX_SOURCE_BYTES", str(2 * 1024 * 1024)))
APPLY_TIMEOUT_SEC = 120
PERL_PROGRAM_MAX_LEN = 8000
SED_SCRIPT_MAX_LEN = 8000
# Lines of context before/after the AST span of the entry (1-based file lines).
DEFAULT_CONTEXT_PAD = int(os.environ.get("PYTHONSEARCH_DELETE_CONTEXT_PAD", "4"))
# When AST cannot find the key, rg hint line ± this window (lines).
FALLBACK_CONTEXT_BEFORE = int(os.environ.get("PYTHONSEARCH_DELETE_FALLBACK_BEFORE", "30"))
FALLBACK_CONTEXT_AFTER = int(os.environ.get("PYTHONSEARCH_DELETE_FALLBACK_AFTER", "80"))
DEBUG_VERBOSE = os.environ.get("PYTHONSEARCH_DELETE_DEBUG", "").lower() in ("1", "true", "yes")
# Max characters of sed/perl payload to print (rest truncated).
APPLY_LOG_PAYLOAD_MAX = int(os.environ.get("PYTHONSEARCH_DELETE_LOG_PAYLOAD_MAX", "8000"))
# OpenAI follow-ups after sed/perl exits non-zero (attempts after the first apply).
TOOL_ERROR_REPAIR_ATTEMPTS = max(0, int(os.environ.get("PYTHONSEARCH_DELETE_TOOL_ERROR_RETRIES", "2")))


class ApplyToolError(Exception):
    """sed/perl exited non-zero; carries process output for logging and LLM repair."""

    def __init__(
        self,
        message: str,
        *,
        tool: str,
        returncode: int,
        stderr: str = "",
        stdout: str = "",
    ):
        super().__init__(message)
        self.tool = tool
        self.returncode = returncode
        self.stderr = stderr or ""
        self.stdout = stdout or ""


def _debug(msg: str) -> None:
    if DEBUG_VERBOSE:
        print(f"[llm_delete][debug] {msg}", flush=True)


def _rg_binary() -> str:
    return shutil.which("rg") or "/opt/homebrew/bin/rg"


def rg_list_py_files_containing(project_root: str, key: str) -> list[str]:
    """Return sorted unique absolute paths of .py files under project_root mentioning key."""
    rg = _rg_binary()
    try:
        out = subprocess.check_output(
            [rg, "-l", "-i", "--type", "py", key, project_root],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return []
        raise
    paths = [os.path.abspath(p.strip()) for p in out.splitlines() if p.strip()]
    return sorted(set(paths))


def count_static_string_keys_in_entries_dict(source: str) -> tuple[Optional[int], bool]:
    """
    Count top-level string keys in the module-level `entries = { ... }` dict literal.
    Returns (count or None if not found / not a dict literal, has_star_unpack).
    """
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "entries":
                if not isinstance(node.value, ast.Dict):
                    return None, False
                d = node.value
                count = 0
                has_star = False
                for k in d.keys:
                    if k is None:
                        has_star = True
                        continue
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        count += 1
                return count, has_star
    return None, False


def count_entries_via_loader() -> Optional[int]:
    """
    How many entries exist, using EntriesLoader / ConfigurationLoader (not AST or raw file reads).
    """
    try:
        from python_search.search.entries_loader import EntriesLoader

        return EntriesLoader.count_entries_from_disk()
    except Exception as e:
        _debug(f"EntriesLoader count failed: {e!r}")
        return None


def _ast_line_span(node: ast.AST) -> tuple[int, int]:
    """1-based inclusive (start_line, end_line) for a node."""
    start = getattr(node, "lineno", 1) or 1
    end = getattr(node, "end_lineno", None) or start
    return start, end


def find_entries_dict_entry_line_span(source: str, entry_key: str) -> Optional[tuple[int, int]]:
    """
    Return (first_line, last_line) inclusive for the key/value pair in top-level
    `entries = { ... }` whose string key equals entry_key. None if not found.
    """
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "entries":
                if not isinstance(node.value, ast.Dict):
                    return None
                d = node.value
                for k, v in zip(d.keys, d.values):
                    if k is None or v is None:
                        continue
                    if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                        continue
                    if k.value != entry_key:
                        continue
                    k0, k1 = _ast_line_span(k)
                    v0, v1 = _ast_line_span(v)
                    return min(k0, v0), max(k1, v1)
    return None


def rg_first_line_matching_substring(file_path: str, substring: str) -> Optional[int]:
    """First 1-based line number where substring appears (fixed string)."""
    rg = _rg_binary()
    try:
        out = subprocess.check_output(
            [rg, "-n", "--max-count", "1", "--fixed-strings", substring, file_path],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return None
        raise
    line = out.strip().splitlines()[0] if out.strip() else ""
    if not line:
        return None
    # ripgrep: path:line:content (split only first two colons)
    parts = line.split(":", 2)
    if len(parts) < 3:
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def build_openai_context_snippet(
    source: str,
    entry_key: str,
    file_path: str,
    *,
    pad: int = DEFAULT_CONTEXT_PAD,
) -> tuple[str, int, int, int]:
    """
    Build a minimal source excerpt for the LLM: the entry's AST span plus padding.
    Returns (snippet, snippet_first_line, snippet_last_line, file_line_count).
    """
    lines = source.splitlines()
    n = len(lines)
    span = find_entries_dict_entry_line_span(source, entry_key)
    if span is not None:
        pair_lo, pair_hi = span
        lo = max(1, pair_lo - pad)
        hi = min(n, pair_hi + pad)
        reason = "ast_entry_span"
    else:
        # e.g. key only in a ** spread — use first occurrence of quoted key in file
        needle = json.dumps(entry_key)
        hint = rg_first_line_matching_substring(file_path, needle)
        if hint is None:
            needle_alt = f'"{entry_key}"'
            hint = rg_first_line_matching_substring(file_path, needle_alt)
        if hint is None:
            lo, hi = 1, n
            reason = "full_file_fallback"
        else:
            lo = max(1, hint - FALLBACK_CONTEXT_BEFORE)
            hi = min(n, hint + FALLBACK_CONTEXT_AFTER)
            reason = "rg_fallback"

    print(
        f"[llm_delete] OpenAI context lines {lo} to {hi} of {n} ({reason})",
        **{"flush": True},
    )

    snippet = "\n".join(lines[lo - 1 : hi])
    return snippet, lo, hi, n


def pick_primary_entry_file(paths: list[str]) -> Optional[str]:
    """Prefer entries_main.py if present; else first lexicographically sorted path."""
    if not paths:
        return None
    paths = sorted(set(paths))
    for p in paths:
        if p.endswith("entries_main.py") or p.endswith("/entries_main.py"):
            return p
    return paths[0]


def print_git_restore_hint(paths: list[str], project_root: str) -> None:
    rels = []
    for p in paths:
        try:
            rels.append(os.path.relpath(p, project_root))
        except ValueError:
            rels.append(p)
    print("\nTo revert changes, from the project root run:\n", file=sys.stderr)
    args = " ".join(shlex.quote(r) for r in rels)
    print(f"  git restore -- {args}\n", file=sys.stderr)


def _forbidden_in_perl(program: str) -> Optional[str]:
    if len(program) > PERL_PROGRAM_MAX_LEN:
        return "perl program too long"
    banned = [
        "`",
        "system",
        "exec",
        "qx/",
        "qx'",
        'qx"',
        "open(",
        "readpipe",
        "fork",
        "syscall",
        "eval {",
        "<<",
    ]
    low = program.lower()
    for b in banned:
        if b.lower() in low:
            return f"forbidden fragment in perl program: {b!r}"
    if re.search(r"^\s*\|\s*", program, re.M):
        return "leading pipe in perl program"
    return None


def _forbidden_in_sed_script(script: str) -> Optional[str]:
    if len(script) > SED_SCRIPT_MAX_LEN:
        return "sed script too long"
    for line in script.splitlines():
        stripped = line.strip()
        if stripped.startswith("!"):
            return "sed script line starts with !"
    return None


def _call_openai_delete_plan(
    *,
    entry_key: str,
    relative_path: str,
    context_snippet: str,
    snippet_line_start: int,
    snippet_line_end: int,
    file_line_count: int,
    extra_user_hint: str = "",
) -> dict[str, Any]:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    system = (
        "You output a single JSON object only. The user will delete ONE dict entry from a Python "
        "file that defines `entries = { ... }` for Python Search.\n"
        'The human-readable entry key string is given; remove only that `"key": { ... },` item.\n'
        "You only see a LINE RANGE excerpt of the file; sed/perl still runs on the FULL file on disk. "
        "Use 1-based LINE NUMBERS that refer to the REAL file (same numbering as in a normal editor), "
        "not relative to the excerpt. The user message states which absolute line range the excerpt covers.\n"
        "Do NOT return full file contents or file paths. The shell will set PS_DELETE_FILE to the "
        "absolute path; you must not embed other paths.\n"
        'Either return {"tool":"sed","sed_script":"..."} where sed_script is a BSD sed program '
        "suitable for: sed -i '' -f <script> \"$PS_DELETE_FILE\" (macOS requires the empty string "
        "after -i). Prefer line addresses using ABSOLUTE file line numbers when you use line ranges.\n"
        "BSD sed -f rules: ONE sed command per line in the script file. "
        "Do not put `d` and another command on the same line — that causes "
        "'extra characters at the end of d command'. No GNU-specific extensions.\n"
        'Or return {"tool":"perl","perl_program":"..."} for: perl -0777 -i -pe \'PROGRAM\' "$PS_DELETE_FILE" '
        "when the value block is multiline. The PROGRAM is only the -pe argument body.\n"
        "Prefer the smallest change that removes exactly that entry and preserves valid Python."
    )
    user = (
        f"Entry key to remove (exact dict key string): {json.dumps(entry_key)}\n"
        f"File (relative to project): {relative_path}\n"
        f"The file has {file_line_count} lines total.\n"
        f"The excerpt below is lines {snippet_line_start} to {snippet_line_end} inclusive "
        f"(absolute 1-based line numbers in the file).\n"
        "```python\n" + context_snippet + "\n```\n" + extra_user_hint
    )
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )
    text = resp.choices[0].message.content or "{}"
    _debug(f"OpenAI raw JSON ({len(text)} chars): {text[:3000]}{'…' if len(text) > 3000 else ''}")
    return json.loads(text)


def _log_apply_payload(tool: str, payload: str, abs_path: str, sed_script_path: Optional[str]) -> None:
    shown = payload
    if len(shown) > APPLY_LOG_PAYLOAD_MAX:
        shown = shown[:APPLY_LOG_PAYLOAD_MAX] + "\n... [truncated for log; see sed file path above if sed]"
    print(f"[llm_delete] --- about to run {tool} on {abs_path} ---", flush=True)
    if tool == "sed" and sed_script_path:
        argv = ["sed", "-i", "", "-f", sed_script_path, abs_path]
        print(f"[llm_delete] argv: {shlex.join(argv)}", flush=True)
        print(f"[llm_delete] sed script path: {sed_script_path}", flush=True)
        print("[llm_delete] sed script body:", flush=True)
        print("---- begin sed_script ----", flush=True)
        print(shown, flush=True)
        print("---- end sed_script ----", flush=True)
    elif tool == "perl":
        argv = ["perl", "-0777", "-i", "-pe", payload, abs_path]
        print(f"[llm_delete] argv: {shlex.join(argv)}", flush=True)
        print("[llm_delete] perl -pe program:", flush=True)
        print("---- begin perl_program ----", flush=True)
        print(shown, flush=True)
        print("---- end perl_program ----", flush=True)
    else:
        print(
            f"[llm_delete] payload ({tool})" + ":\n" + shown,
            **{"flush": True},
        )


def _apply_tool(tool: str, payload: str, abs_path: str, project_root: str) -> None:
    env = os.environ.copy()
    env["PS_DELETE_FILE"] = abs_path
    if tool == "sed":
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sed", delete=False, encoding="utf-8") as tf:
            tf.write(payload)
            sedf = tf.name
        try:
            _log_apply_payload("sed", payload, abs_path, sedf)
            r = subprocess.run(
                ["sed", "-i", "", "-f", sedf, abs_path],
                cwd=project_root,
                env=env,
                timeout=APPLY_TIMEOUT_SEC,
                capture_output=True,
                text=True,
            )
            out = (r.stdout or "").strip()
            err = (r.stderr or "").strip()
            if out:
                print("[llm_delete] sed stdout:\n" + out, flush=True)
            if err:
                print("[llm_delete] sed stderr:\n" + err, flush=True)
            if r.returncode != 0:
                raise ApplyToolError(
                    f"sed exited with code {r.returncode}",
                    tool="sed",
                    returncode=r.returncode,
                    stderr=r.stderr or "",
                    stdout=r.stdout or "",
                )
            print("[llm_delete] sed finished OK (exit 0)", flush=True)
        finally:
            try:
                os.unlink(sedf)
            except OSError:
                pass
    elif tool == "perl":
        err = _forbidden_in_perl(payload)
        if err:
            raise ValueError(err)
        _log_apply_payload("perl", payload, abs_path, None)
        r = subprocess.run(
            ["perl", "-0777", "-i", "-pe", payload, abs_path],
            cwd=project_root,
            env=env,
            timeout=APPLY_TIMEOUT_SEC,
            capture_output=True,
            text=True,
        )
        out = (r.stdout or "").strip()
        perr = (r.stderr or "").strip()
        if out:
            print("[llm_delete] perl stdout:\n" + out, flush=True)
        if perr:
            print("[llm_delete] perl stderr:\n" + perr, flush=True)
        if r.returncode != 0:
            raise ApplyToolError(
                f"perl exited with code {r.returncode}",
                tool="perl",
                returncode=r.returncode,
                stderr=r.stderr or "",
                stdout=r.stdout or "",
            )
        print("[llm_delete] perl finished OK (exit 0)", flush=True)
    else:
        raise ValueError(f"unknown tool: {tool!r}")


def _tool_payload_from_plan(plan: dict[str, Any]) -> tuple[str, str]:
    """Validate plan JSON and return (tool, payload). Raises ValueError with reason."""
    tool = plan.get("tool")
    if tool not in ("sed", "perl"):
        raise ValueError(f"invalid or missing tool: {tool!r}")
    if tool == "sed":
        sed_script = plan.get("sed_script") or plan.get("script") or ""
        if not isinstance(sed_script, str):
            raise ValueError("sed_script must be a string")
        serr = _forbidden_in_sed_script(sed_script)
        if serr:
            raise ValueError(f"unsafe sed script: {serr}")
        return tool, sed_script
    payload = plan.get("perl_program") or plan.get("program") or ""
    if not isinstance(payload, str) or not payload.strip():
        raise ValueError("perl_program must be a non-empty string")
    perr = _forbidden_in_perl(payload)
    if perr:
        raise ValueError(f"unsafe perl: {perr}")
    return tool, payload


def _tool_error_repair_hint(err: ApplyToolError) -> str:
    stderr_block = err.stderr or "(empty)"
    stdout_block = err.stdout or "(empty)"
    return (
        f"The {err.tool} command FAILED on disk.\n"
        f"exit_code = {err.returncode}\n\n"
        "stderr:\n" + stderr_block + "\n\nstdout:\n" + stdout_block + "\n\n"
        "Return a corrected JSON only.\n"
        "For BSD/macOS sed -f: each line of sed_script is ONE command; "
        "never append another command after `d` on the same line (that triggers "
        "'extra characters at the end of d command').\n"
        "If sed is unreliable, use tool perl with a perl_program instead.\n"
    )


def _validate_and_compile(path: str) -> None:
    with open(path, encoding="utf-8", errors="replace") as f:
        src = f.read()
    ast.parse(src)
    compile(src, path, "exec")


def run_delete_key_flow(
    entry_key: str,
    *,
    configuration=None,
    expected_deleted: int = 1,
    openai_fn: Optional[Callable[..., dict[str, Any]]] = None,
) -> bool:
    """
    Run the full delete pipeline. Returns True on success.
    `openai_fn` is injectable for tests (same signature as _call_openai_delete_plan kwargs).
    """
    if not entry_key or not entry_key.strip():
        print("No entry key provided.", file=sys.stderr)
        return False

    if configuration is None:
        from python_search.configuration.loader import ConfigurationLoader

        configuration = ConfigurationLoader().load_config()

    project_root = os.path.abspath(configuration.get_project_root())
    touched: list[str] = []

    print(f"[llm_delete] project_root = {project_root}", flush=True)
    print(f"[llm_delete] entry_key = {entry_key!r}", flush=True)

    paths = rg_list_py_files_containing(project_root, entry_key)
    if not paths:
        print("No .py files matched ripgrep for this key.", file=sys.stderr)
        return False

    print(f"[llm_delete] ripgrep: {len(paths)} .py file(s) mention this key", flush=True)
    _debug("ripgrep paths:\n  " + "\n  ".join(paths[:50]) + ("…" if len(paths) > 50 else ""))

    target = pick_primary_entry_file(paths)
    if not target or not target.startswith(project_root):
        print("Could not pick a target file under project root.", file=sys.stderr)
        return False

    if not os.path.isfile(target):
        print(f"Target is not a file: {target}", file=sys.stderr)
        return False

    size = os.path.getsize(target)
    if size > MAX_SOURCE_BYTES:
        print(f"File too large ({size} bytes), max {MAX_SOURCE_BYTES}.", file=sys.stderr)
        return False

    with open(target, encoding="utf-8", errors="replace") as f:
        before_source = f.read()

    line_count = len(before_source.splitlines())
    print(
        f"[llm_delete] target file lines = {line_count} " f"bytes = {len(before_source.encode('utf-8'))}",
        flush=True,
    )

    # Row count = same as Search UI via EntriesLoader only (no AST fallback for validation).
    rt_before = count_entries_via_loader()
    if rt_before is None:
        print(
            "Cannot count entries: EntriesLoader failed; need a working entries config to validate deletes.",
            file=sys.stderr,
        )
        return False

    print(
        f"[llm_delete] entries_loader_count_before = {rt_before} "
        f"(EntriesLoader.count_entries_from_disk — same as Search UI)",
        flush=True,
    )

    rel = os.path.relpath(target, project_root)
    snippet, snip_lo, snip_hi, n_lines = build_openai_context_snippet(before_source, entry_key, target)
    caller = openai_fn or _call_openai_delete_plan

    print(
        f"[llm_delete] calling OpenAI model = " f"{os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')!r}",
        flush=True,
    )
    plan: dict[str, Any]
    try:
        plan = caller(
            entry_key=entry_key,
            relative_path=rel,
            context_snippet=snippet,
            snippet_line_start=snip_lo,
            snippet_line_end=snip_hi,
            file_line_count=n_lines,
        )
    except Exception as e:
        print(f"OpenAI / planning failed: {e}", file=sys.stderr)
        return False

    _debug(f"parsed plan keys: {list(plan.keys())}")
    try:
        tool_cur, payload_cur = _tool_payload_from_plan(plan)
    except ValueError as ve:
        print(str(ve), file=sys.stderr)
        return False

    print(f"[llm_delete] step: apply tool = {tool_cur!r}", flush=True)
    touched.append(target)

    last_tool_err: Optional[ApplyToolError] = None
    for attempt in range(TOOL_ERROR_REPAIR_ATTEMPTS + 1):
        if attempt > 0:
            assert last_tool_err is not None
            msg = (
                f"[llm_delete] step: restore file + OpenAI repair after {last_tool_err.tool} "
                f"failure (attempt {attempt + 1} of {TOOL_ERROR_REPAIR_ATTEMPTS + 1})"
            )
            print(msg, flush=True)
            with open(target, "w", encoding="utf-8") as wf:
                wf.write(before_source)
            try:
                plan_fix = caller(
                    entry_key=entry_key,
                    relative_path=rel,
                    context_snippet=snippet,
                    snippet_line_start=snip_lo,
                    snippet_line_end=snip_hi,
                    file_line_count=n_lines,
                    extra_user_hint=_tool_error_repair_hint(last_tool_err),
                )
            except Exception as e2:
                print(f"OpenAI tool-repair failed: {e2}", file=sys.stderr)
                print_git_restore_hint(touched, project_root)
                return False
            try:
                tool_cur, payload_cur = _tool_payload_from_plan(plan_fix)
            except ValueError as ve:
                print(str(ve), file=sys.stderr)
                print_git_restore_hint(touched, project_root)
                return False

        try:
            _apply_tool(tool_cur, payload_cur, target, project_root)
            break
        except ApplyToolError as e:
            last_tool_err = e
            msg = f"[llm_delete] {e.tool} failed: exit {e.returncode} ({e})"
            print(msg, file=sys.stderr)
            if attempt >= TOOL_ERROR_REPAIR_ATTEMPTS:
                print_git_restore_hint(touched, project_root)
                return False

    try:
        print("[llm_delete] step: ast.parse + compile() on edited file", flush=True)
        _validate_and_compile(target)
        print("[llm_delete] compile OK", flush=True)
    except SyntaxError as e:
        print(f"Syntax error after edit: {e}", file=sys.stderr)
        print("[llm_delete] attempting one OpenAI repair round…", flush=True)
        try:
            plan2 = caller(
                entry_key=entry_key,
                relative_path=rel,
                context_snippet=snippet,
                snippet_line_start=snip_lo,
                snippet_line_end=snip_hi,
                file_line_count=n_lines,
                extra_user_hint=f"Previous edit caused SyntaxError: {e}. Return a corrected JSON.\n",
            )
        except Exception as e2:
            print(f"OpenAI retry failed: {e2}", file=sys.stderr)
            print_git_restore_hint(touched, project_root)
            return False
        try:
            tool2, p2 = _tool_payload_from_plan(plan2)
        except ValueError as ve:
            print(str(ve), file=sys.stderr)
            print_git_restore_hint(touched, project_root)
            return False
        try:
            print("[llm_delete] step: restore file from memory + retry apply", flush=True)
            with open(target, "w", encoding="utf-8") as wf:
                wf.write(before_source)
            try:
                _apply_tool(tool2, p2, target, project_root)
            except ApplyToolError as te:
                print(
                    f"[llm_delete] syntax-repair apply failed: {te.tool} exit {te.returncode}",
                    file=sys.stderr,
                )
                if te.stderr.strip():
                    print(te.stderr, file=sys.stderr)
                print_git_restore_hint(touched, project_root)
                return False
            print("[llm_delete] step: compile after retry", flush=True)
            _validate_and_compile(target)
            print("[llm_delete] compile OK after retry", flush=True)
        except Exception as e3:
            print(f"Retry apply/compile failed: {e3}", file=sys.stderr)
            print_git_restore_hint(touched, project_root)
            return False

    print("[llm_delete] step: validate entry count after edit (EntriesLoader only)", flush=True)
    rt_after = count_entries_via_loader()
    if rt_after is None:
        print(
            "After edit: EntriesLoader count failed; cannot validate delete.",
            file=sys.stderr,
        )
        print_git_restore_hint(touched, project_root)
        return False

    print(f"[llm_delete] entries_loader_count_after = {rt_after}", flush=True)
    delta = rt_before - rt_after
    msg = f"[llm_delete] validation: EntriesLoader delta = {delta} " f"(expected {expected_deleted})"
    print(msg, flush=True)
    if delta != expected_deleted:
        print(
            f"EntriesLoader entry count delta {delta} != expected {expected_deleted}.",
            file=sys.stderr,
        )
        print_git_restore_hint(touched, project_root)
        return False

    print("[llm_delete] success. Reload the search UI (] or \\) to refresh entries.", flush=True)
    return True


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(
            "usage: python -m python_search.entry_capture.llm_delete_entry <entry_key>",
            file=sys.stderr,
        )
        return 2
    key = argv[0]
    ok = run_delete_key_flow(key)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
