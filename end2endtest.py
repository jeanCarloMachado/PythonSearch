#!/usr/bin/env python3
import os

class End2End:
    """
    """
    def run(self):
        self._cleanup()
        self._run_shell("pip install python-search")
        self._run_shell("python_search new_project /tmp/test1")
        self._run_shell("python_search search")

    def cleanup(self):
        self._run_shell("rm -rf /tmp/test1 2>/dev/null")
        self._run_shell('echo "$HOME/projects/PySearchEntries" > $HOME/.config/python_search/current_project')

    def _run_shell(self, cmd):
        os.system(cmd)


if __name__ == "__main__":
    import fire

    fire.Fire(End2End)
