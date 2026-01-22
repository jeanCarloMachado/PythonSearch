import os
import sys


class SystemPaths:
    # override this in new system installations
    PERSONAL_MONOREPO_PATH = "/Users/jeanmachado/code_projects/PersonalMonorepo"
    PYTHON_SEARCH_PATH = "/Users/jean.machado@getyourguide.com/prj/PythonSearch"

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