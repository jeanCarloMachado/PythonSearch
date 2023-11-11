from typing import Union
from python_search.environment import is_mac


def chomp(x):
    """remove special chars from end of string"""
    if x.endswith("\r\n"):
        return x[:-2]
    if x.endswith("\n") or x.endswith("\r"):
        return x[:-1]
    return x


class Clipboard:
    def get_content(self, source="--primary") -> str:
        """
        Accepted values are --primary and --clipboard
        """

        cmd = f"xsel {source} --output"
        if is_mac():
            cmd = "pbpaste"

        import subprocess

        result = subprocess.getoutput(cmd)
        result = chomp(result)

        return result

    def set_content(
        self, content: Union[str, None] = None, enable_notifications=True, notify=False
    ):
        """
        Put a string in the clipboard.
        If no string is provided it tries to fetch it from stdin
        :param content:
        :param enable_notifications:
        :return:
        """

        if not content:
            import sys

            data = sys.stdin.readlines()
            content = "".join(data)

        if not content:
            raise Exception("Tryring to set empty to clipboard")

        if type(content) != str:
            raise Exception("Tryring to set a non string to clipboard")

        # overrides previous content
        with open("/tmp/clipboard_content", "w") as f:
            f.write(content)

        clipboard_cmd = "xsel --clipboard --primary --input"
        if is_mac():
            clipboard_cmd = "pbcopy"

        cmd = f"cat /tmp/clipboard_content | {clipboard_cmd}"

        from subprocess import PIPE, Popen

        with Popen(cmd, stdout=PIPE, stderr=None, shell=True) as process:
            output = process.communicate()[0].decode("utf-8")
            if process.returncode != 0:
                raise Exception("Failed to copy to clipboard " + output)

        if enable_notifications or notify:
            from python_search.apps.notification_ui import send_notification

            send_notification(f"Content copied: {content}")


def main():
    import fire

    fire.Fire(Clipboard)


if __name__ == "__main__":
    main()
