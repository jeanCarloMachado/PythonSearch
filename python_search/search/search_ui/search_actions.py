from subprocess import Popen

from python_search.host_system.system_paths import SystemPaths


class Actions:
    def search_in_google(self, query):
        Popen(
            f'{SystemPaths.BINARIES_PATH}/clipboard set_content "{query}"  && {SystemPaths.BINARIES_PATH}/run_key "search in google using clipboard content" &>/dev/null',
            stdout=None,
            stderr=None,
            shell=True,
        )

    def copy_entry_value_to_clipboard(self, entry_key):
        Popen(
            f'{SystemPaths.BINARIES_PATH}/share_entry share_only_value "{entry_key}" &>/dev/null',
            stdout=None,
            stderr=None,
            shell=True,
        )

    def edit_key(self, key, block=False):

        Popen(
            f'{SystemPaths.BINARIES_PATH}/entries_editor edit_key "{key}" &>/dev/null',
            stdout=None,
            stderr=None,
            shell=True,
        )

    def run_key(self, key: str) -> None:
        command = f'{SystemPaths.BINARIES_PATH}/run_key "{key}" &>/dev/null'
        Popen(command, stdout=None, stderr=None, shell=True)
