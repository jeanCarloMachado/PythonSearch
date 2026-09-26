"""Module responsible for the logic of editing entry files"""

import logging
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import List, Optional

from python_search.apps.terminal import get_terminal, KittyTerminal
from python_search.apps.terminator_terminal import TerminatorTerminal
from python_search.core_entities import Key


class EntriesEditor:
    """
    Open an ide to edit the entries
    """

    def __init__(self, configuration=None):
        if not configuration:
            from python_search.configuration.loader import ConfigurationLoader

            configuration = ConfigurationLoader().load_config()
        self.configuration = configuration

        # Ensure ripgrep is available for file searching
        self._search_cmd = self._get_search_command()

    def _get_search_command(self) -> str:
        """
        Ensure ripgrep is available for file searching.
        """
        return shutil.which("rg") or "/opt/homebrew/bin/rg"

    def _build_search_command(self, key: str) -> List[str]:
        """
        Build the ripgrep command that finds where the key is declared as a dict key, e.g. `"key": {`.
        """
        project_root = self.configuration.get_project_root()
        pattern = "^\\s*[\"']" + re.escape(key) + "[\"']\\s*:"
        return [self._search_cmd, "-n", "-i", "--type", "py", "--sort", "path", pattern, project_root]

    def edit_key(self, key_expr: str):
        """
        Edits the configuration files by searching the text
        """

        key = str(Key.from_fzf(key_expr))
        print(f"Editing key {key}")
        if not key:
            self.edit_default()
            return

        if not len(key):
            print("Editing default")
            self.edit_default()
            return

        # needs to be case-insensitive search
        cmd = self._build_search_command(key)
        logging.info(f"Command: {cmd}")
        # rg exits with 1 when nothing matches
        result_shell = subprocess.run(cmd, capture_output=True, text=True).stdout

        if not result_shell:
            print("Could not find match edit main file, output: ", result_shell)
            self.edit_default()
            return

        file, line, *_ = result_shell.split(":")
        print(f"Editing file and line {file}, {line}")

        self._edit_file(file, int(line))

    def delete_key(self, key_expr: str):
        """
        Delete one entry via LLM (OpenAI): ripgrep → shell edit → compile + entry-count check.
        Opens a new Kitty window with progress; use git restore on failure.

        Search UI: Ctrl+D on a selected row — control character, like Tab for edit (see SearchTerminalUi).
        """
        key = str(Key.from_fzf(key_expr))
        print(f"Deleting key {key!r} (LLM-assisted)")
        if not key or not len(key):
            print("No key to delete.")
            return

        project_root = self.configuration.get_project_root()
        py = sys.executable
        fd, script_path = tempfile.mkstemp(suffix=".sh", text=True)
        os.close(fd)
        try:
            with open(script_path, "w", encoding="utf-8") as sf:
                q_script = shlex.quote(script_path)
                q_root = shlex.quote(project_root)
                q_py = shlex.quote(py)
                q_key = shlex.quote(key)
                sf.write(
                    "#!/bin/bash\n"
                    "set -e\n"
                    "cleanup() { rm -f " + q_script + "; }\n"
                    "trap cleanup EXIT\n"
                    f"cd {q_root}\n"
                    f"exec {q_py} -m python_search.entry_capture.llm_delete_entry {q_key}\n"
                )
            os.chmod(script_path, stat.S_IRWXU)
        except OSError:
            try:
                os.unlink(script_path)
            except OSError:
                pass
            raise

        terminal = get_terminal()
        inner = f"bash {shlex.quote(script_path)}"
        terminal_cmd = terminal.wrap_cmd_into_terminal(inner, title="Python Search: delete entry (LLM)")
        logging.info("Terminal delete_key: %s", terminal_cmd)
        os.system(terminal_cmd)

    def edit_default(self):
        self._edit_file(f"{self.configuration.get_project_root()}/entries_main.py", line=None)

    # Editor-specific window settings (squared window for editing)
    EDITOR_WIDTH = "100c"
    EDITOR_HEIGHT = "40c"
    EDITOR_FONT_SIZE = 14

    def _edit_file(self, file_name: str, line: Optional[int] = 30, dry_run=False):
        """
        edit a configuration file given the name and line
        """

        editor_cmd = f"cd {self.configuration.get_project_root()} && {self._get_open_text_editor_command(file_name, line)}"

        terminal = get_terminal()
        if isinstance(terminal, TerminatorTerminal):
            # opens as a tab in the running Terminator window
            cmd = terminal.wrap_cmd_into_terminal(
                editor_cmd, title="Python Search: edit entries", hold_terminal_open_on_end=False
            )
        else:
            kitty = KittyTerminal()
            # Use editor-specific window size instead of generic terminal params
            editor_params = (
                f" {kitty.GLOBAL_TERMINAL_PARAMS} "
                f" -o initial_window_width={self.EDITOR_WIDTH} "
                f" -o initial_window_height={self.EDITOR_HEIGHT} "
                f" -o font_size={self.EDITOR_FONT_SIZE} "
            )
            cmd = f" {kitty.get_kitty_cmd()} {editor_params} bash -c '{editor_cmd}'"
        print(cmd)

        if dry_run:
            logging.info(f"Command to edit file: {cmd}")
            return

        os.system(cmd)

    def _get_open_text_editor_command(self, file, line):
        # vim only supported
        if line is None:
            return f"vim {file}"
        return f"vim {file} +{line}"


def main():
    import fire

    fire.Fire(EntriesEditor)


if __name__ == "__main__":
    main()
