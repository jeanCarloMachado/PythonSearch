import subprocess
import sys
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

from python_search.entry_capture import llm_delete_entry as lde


def test_count_entries_via_loader_merged_keys(tmp_path, monkeypatch):
    """EntriesLoader count includes keys from ** merges; AST static count does not."""
    monkeypatch.setenv("PS_ENTRIES_HOME", str(tmp_path))
    sys.modules.pop("entries_main", None)
    em = tmp_path / "entries_main.py"
    em.write_text(
        textwrap.dedent(
            """
            from python_search.configuration.configuration import PythonSearchConfiguration

            entries = {
                "fixed": {"cmd": "echo a"},
                **{f"dyn {i}": {"cmd": "echo x"} for i in range(3)},
            }
            config = PythonSearchConfiguration(entries=entries)
            """
        ),
        encoding="utf-8",
    )
    rt = lde.count_entries_via_loader()
    assert rt == 4
    src = em.read_text(encoding="utf-8")
    ast_n, _ = lde.count_static_string_keys_in_entries_dict(src)
    assert ast_n == 1


def test_count_static_string_keys_simple():
    src = textwrap.dedent(
        """
        entries = {
            "a": {"cmd": "x"},
            "b": {"cmd": "y"},
        }
        x = 1
        """
    )
    n, star = lde.count_static_string_keys_in_entries_dict(src)
    assert n == 2
    assert star is False


def test_count_static_string_keys_with_star_unpack():
    src = textwrap.dedent(
        """
        entries = {
            "a": 1,
            **other,
        }
        """
    )
    n, star = lde.count_static_string_keys_in_entries_dict(src)
    assert n == 1
    assert star is True


def test_count_static_string_keys_missing():
    src = "foo = {}\n"
    n, star = lde.count_static_string_keys_in_entries_dict(src)
    assert n is None


def test_pick_primary_entry_file_prefers_entries_main():
    paths = ["/proj/foo.py", "/proj/entries_main.py", "/proj/bar.py"]
    assert lde.pick_primary_entry_file(paths).endswith("entries_main.py")
    assert lde.pick_primary_entry_file(["/a/z.py", "/a/b.py"]) == "/a/b.py"


def test_find_entries_dict_entry_line_span_multiline_value():
    src = textwrap.dedent(
        """
        # header
        entries = {
            "short": {"cmd": "x"},
            "long": {
                "cmd": "y",
                "url": "https://example.com",
            },
        }
        """
    )
    lo, hi = lde.find_entries_dict_entry_line_span(src, "long")
    lines = src.splitlines()
    assert 1 <= lo <= hi <= len(lines)
    excerpt = "\n".join(lines[lo - 1 : hi])
    assert '"long"' in excerpt
    assert "example.com" in excerpt
    assert '"short"' not in excerpt


def test_build_openai_context_snippet_is_subset_not_whole_file(tmp_path):
    filler = "\n".join([f"# line {i}" for i in range(60)])
    body = textwrap.dedent(
        """
        entries = {
            "target": {"cmd": "echo hi"},
            "other": {"cmd": "echo no"},
        }
        """
    )
    src = filler + "\n" + body
    p = tmp_path / "entries_main.py"
    p.write_text(src, encoding="utf-8")
    snip, lo, hi, n = lde.build_openai_context_snippet(src, "target", str(p), pad=2)
    assert n == len(src.splitlines())
    assert len(snip.splitlines()) < n
    assert '"target"' in snip
    assert "entries = {" in snip


def test_run_delete_key_flow_mocked_openai(tmp_path, monkeypatch):
    monkeypatch.setenv("PS_ENTRIES_HOME", str(tmp_path))
    sys.modules.pop("entries_main", None)
    em = tmp_path / "entries_main.py"
    em.write_text(
        textwrap.dedent(
            """
            from python_search.configuration.configuration import PythonSearchConfiguration

            entries = {
                "drop_me": {"cmd": "echo drop"},
                "keep_me": {"cmd": "echo keep"},
            }
            config = PythonSearchConfiguration(entries=entries)
            """
        ),
        encoding="utf-8",
    )

    def fake_openai(**kwargs):
        return {
            "tool": "perl",
            "perl_program": r's/"drop_me"\s*:\s*\{[^}]*\},?\s*//',
        }

    class Cfg:
        def get_project_root(self):
            return str(tmp_path)

    ok = lde.run_delete_key_flow(
        "drop_me",
        configuration=Cfg(),
        openai_fn=fake_openai,
    )
    assert ok
    out = em.read_text(encoding="utf-8")
    assert "drop_me" not in out
    assert "keep_me" in out
    compile(out, str(em), "exec")


def test_run_delete_key_flow_retries_after_sed_nonzero(tmp_path, monkeypatch):
    """BSD sed stderr (e.g. bad `d` line) triggers OpenAI repair with hint; second plan applies."""
    monkeypatch.setenv("PS_ENTRIES_HOME", str(tmp_path))
    sys.modules.pop("entries_main", None)
    em = tmp_path / "entries_main.py"
    em.write_text(
        textwrap.dedent(
            """
            from python_search.configuration.configuration import PythonSearchConfiguration

            entries = {
                "drop_me": {"cmd": "echo drop"},
                "keep_me": {"cmd": "echo keep"},
            }
            config = PythonSearchConfiguration(entries=entries)
            """
        ),
        encoding="utf-8",
    )

    calls: list[str] = []

    def fake_openai(**kwargs):
        hint = kwargs.get("extra_user_hint") or ""
        calls.append(hint)
        if len(calls) == 1:
            return {"tool": "sed", "sed_script": "1d trailing_garbage"}
        return {
            "tool": "perl",
            "perl_program": r's/"drop_me"\s*:\s*\{[^}]*\},?\s*//',
        }

    class Cfg:
        def get_project_root(self):
            return str(tmp_path)

    ok = lde.run_delete_key_flow(
        "drop_me",
        configuration=Cfg(),
        openai_fn=fake_openai,
    )
    assert ok
    assert len(calls) == 2
    assert "FAILED" in calls[1] and "stderr" in calls[1]
    out = em.read_text(encoding="utf-8")
    assert "drop_me" not in out
    assert "keep_me" in out


def test_delete_key_help_command_returns_output():
    cmd = [
        "python",
        "-m",
        "python_search.entry_capture.entries_editor",
        "delete_key",
        "--help",
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    help_out = result.stderr + result.stdout
    assert "delete_key" in help_out
