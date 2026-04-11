"""Module responsible for the logic of editing entry files"""

import logging
import os
import shlex
import stat
import subprocess
import sys
import tempfile
from typing import Optional

from python_search.apps.terminal import KittyTerminal
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
        return "/opt/homebrew/bin/rg"

    def _build_search_command(self, key: str) -> str:
        """
        Build the ripgrep search command.
        """
        project_root = self.configuration.get_project_root()
        return f"/opt/homebrew/bin/rg -n -i --type py '{key}' {project_root} || true"

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
        result_shell = subprocess.check_output(cmd, shell=True, text=True)

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

        terminal = KittyTerminal()
        inner = f"bash {shlex.quote(script_path)}"
        kitty_cmd = terminal.wrap_cmd_into_terminal(inner, title="Python Search: delete entry (LLM)")
        logging.info("Kitty delete_key: %s", kitty_cmd)
        os.system(kitty_cmd)

    def edit_default(self):
        terminal = KittyTerminal()
        editor_params = (
            f" {terminal.GLOBAL_TERMINAL_PARAMS} "
            f" -o initial_window_width={self.EDITOR_WIDTH} "
            f" -o initial_window_height={self.EDITOR_HEIGHT} "
            f" -o font_size={self.EDITOR_FONT_SIZE} "
        )
        os.system(
            f"{terminal.get_kitty_cmd()} {editor_params} vim '{self.configuration.get_project_root()}/entries_main.py'"
        )

    # Editor-specific window settings (squared window for editing)
    EDITOR_WIDTH = "100c"
    EDITOR_HEIGHT = "40c"
    EDITOR_FONT_SIZE = 14

    def _edit_file(self, file_name: str, line: Optional[int] = 30, dry_run=False):
        """
        edit a configuration file given the name and line
        """

        # @ todo make this editor generic

        terminal = KittyTerminal()
        # Use editor-specific window size instead of generic terminal params
        editor_params = (
            f" {terminal.GLOBAL_TERMINAL_PARAMS} "
            f" -o initial_window_width={self.EDITOR_WIDTH} "
            f" -o initial_window_height={self.EDITOR_HEIGHT} "
            f" -o font_size={self.EDITOR_FONT_SIZE} "
        )
        cmd: str = (
            f" {terminal.get_kitty_cmd()} {editor_params} "
            f"bash -c 'cd {self.configuration.get_project_root()} && "
            f"{self._get_open_text_editor_command(file_name, line)}'"
        )
        print(cmd)

        if dry_run:
            logging.info(f"Command to edit file: {cmd}")
            return

        os.system(cmd)

    def _get_open_text_editor_command(self, file, line):
        # vim only supported
        return f"vim {file} +{line}"


def main():
    import fire

    fire.Fire(EntriesEditor)


if __name__ == "__main__":
    main()
