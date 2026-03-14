import os
import sys


def _read_python_search_path() -> str:
    config_file = os.path.expanduser("~/.config/python_search/config")
    if not os.path.isfile(config_file):
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w") as f:
            f.write("# PythonSearch configuration\n")
            f.write("# PYTHON_SEARCH_PATH=<absolute path to your PythonSearch repo>\n")
        raise RuntimeError(
            f"Config file created at {config_file} but PYTHON_SEARCH_PATH is not set.\n"
            f"Please add the following line to {config_file}:\n"
            f"  PYTHON_SEARCH_PATH=<absolute path to your PythonSearch repo>"
        )
    with open(config_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith("PYTHON_SEARCH_PATH="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value
    raise RuntimeError(
        f"PYTHON_SEARCH_PATH is not set in {config_file}.\n"
        f"Please add the following line:\n"
        f"  PYTHON_SEARCH_PATH=<absolute path to your PythonSearch repo>"
    )


class SystemPaths:
    PYTHON_SEARCH_PATH = _read_python_search_path()

    KITTY_BINNARY = "/opt/homebrew/bin/kitty"
    VIM_BINNARY = "/usr/bin/vim"

    @staticmethod
    def get_python_executable_path() -> str:
        """Returns the directory path containing the current Python executable."""
        return os.path.dirname(sys.executable)

    @staticmethod
    def get_binary_full_path(binary_name: str) -> str:
        """Returns the full path of a binary in the Python executable folder."""
        return os.path.join(os.path.dirname(sys.executable), binary_name)
