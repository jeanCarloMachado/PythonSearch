from grimoire.shell import shell
from grimoire.string import chomp, remove_new_lines

from python_search.environment import is_mac


class Clipboard:
    def get_content(self, source="--primary"):
        """
        Accepted values are --primary and --clipboard
        """

        cmd = f"xsel {source} --output"
        if is_mac():
            cmd = "pbpaste"

        result = shell.run_with_result(cmd)
        result = chomp(result)

        return result

    def get_content_preview(self):
        content = self.get_content()
        content = content.strip(" \t\n\r")
        content = remove_new_lines(content)
        content_len = len(content)
        desized_preview_size = 10
        size_of_preview = (
            desized_preview_size if desized_preview_size < content_len else content_len
        )

        final_content = content[0:size_of_preview]
        suffix = " ..." if len(content) > size_of_preview else ""
        return f"{final_content}{suffix}"

    def set_content(self, content: str, enable_notifications=True):
        """
        Put a string in the clibboard
        :param content:
        :param enable_notifications:
        :return:
        """

        def shellquote(s):
            return "'" + s.replace("'", "'\\''") + "'"

        sanitized = shellquote(content)

        clipboard_cmd = "xsel --clipboard --primary --input"
        if is_mac():
            clipboard_cmd = "pbcopy"

        cmd = f"echo {sanitized} | {clipboard_cmd}"

        if enable_notifications:
            from python_search.apps.notification_ui import send_notification

            send_notification(f"Content copied: {sanitized}")

        return shell.run(cmd)


def main():
    import fire

    fire.Fire(Clipboard)


if __name__ == "__main__":
    main()
