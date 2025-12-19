from subprocess import Popen

from python_search.host_system.system_paths import SystemPaths


class Actions:
    """
    Handles various actions that can be performed on search entries and queries.

    This class provides methods for running entries, editing them, copying values
    to clipboard, and performing web searches. All operations are executed
    asynchronously using subprocess.Popen.
    """

    def run_key(self, key: str) -> None:
        """
        Execute a command associated with the given key.

        Args:
            key: The identifier for the entry to run
        """
        command = f'{SystemPaths.BINARIES_PATH}/run_key "{key}" &>/dev/null'
        Popen(command, stdout=None, stderr=None, shell=True)

    def edit_key(self, key: str, block: bool = False) -> None:
        """
        Open the entry editor for the specified key.

        Args:
            key: The identifier for the entry to edit
            block: Whether to block execution (currently unused)
        """
        cmd = (
            f"/opt/miniconda3/envs/python312/bin/entries_editor "
            f'edit_key "{key}" &>/dev/null'
        )
        Popen(cmd, stdout=None, stderr=None, shell=True)

    def copy_entry_value_to_clipboard(self, entry_key: str) -> None:
        """
        Copy the value of an entry to the system clipboard.

        Args:
            entry_key: The identifier for the entry whose value should be copied
        """
        command = (
            f"{SystemPaths.BINARIES_PATH}/share_entry "
            f'share_only_value "{entry_key}" &>/dev/null'
        )
        Popen(command, stdout=None, stderr=None, shell=True)

    def search_in_google(self, query: str) -> None:
        """
        Perform a Google search with the given query.

        Sets the query in clipboard and triggers a Google search action.

        Args:
            query: The search query to execute
        """
        command = (
            f'{SystemPaths.BINARIES_PATH}/clipboard set_content "{query}" && '
            f"{SystemPaths.BINARIES_PATH}/run_key "
            f'"search in google using clipboard content" &>/dev/null'
        )
        Popen(command, stdout=None, stderr=None, shell=True)
