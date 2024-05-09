from subprocess import Popen


class Actions:
    def search_in_google(self, query):
        Popen(
            f'clipboard set_content "{query}"  && run_key "search in google using clipboard content" &>/dev/null',
            stdout=None,
            stderr=None,
            shell=True,
        )

    def copy_entry_value_to_clipboard(self, entry_key):
        Popen(
            f'share_entry share_only_value "{entry_key}" &>/dev/null',
            stdout=None,
            stderr=None,
            shell=True,
        )

    def edit_key(self, key):
        Popen(
            f'entries_editor edit_key "{key}"  &>/dev/null',
            stdout=None,
            stderr=None,
            shell=True,
        )

    def run_key(self, key):
        command = f'run_key "{key}" &>/dev/null'
        Popen(command, stdout=None, stderr=None, shell=True)
