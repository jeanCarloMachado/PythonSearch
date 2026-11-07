import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from python_search.environment import is_mac


class Focus:
    def focus_register_new(self):
        result = os.system(
            """
        osascript -e 'tell application "System Events" to tell process "python3"
                set frontmost to true
                windows where title contains "Register New"
                if result is not {} then perform action "AXRaise" of item 1 of result
end tell'
        """
        )

        return True if result == 0 else False

    def focus_window(self, app, title):
        """
        Focuses on a window with the given app and title
        """
        if app == "Google Chrome" and is_mac():
            return self._focus_mac_chrome_window(title)

        cmd = f"""
        osascript -e '
        tell application "System Events"
            tell application process "{app}"
                perform action "AXRaise" of (first window whose name contains "{title}")
                set frontmost to true
            end tell
        end tell
        '
            """
        result = os.system(cmd)
        print(f" trying to focus {result}")

        return True if result == 0 else False

    def _focus_mac_chrome_window(self, title) -> bool:
        """
        Uses Chrome's own scripting rather than System Events, which needs an Accessibility
        grant that shortcuts run by Karabiner don't have. Returns False only when no window
        matches: a failed script raises, so it can't be mistaken for a missing window.
        Matches the tab title because Chrome truncates the middle of window titles here.
        Addresses Chrome by pid: when an automation Chrome (e.g. Playwright) runs from the
        same bundle, "Google Chrome" by name can resolve to it, find no windows, and every
        shortcut then opens a duplicate window.
        """
        pid = self._main_mac_chrome_pid()
        if pid is None:
            return False

        script = f"""
        const chrome = Application({pid});
        const title = {json.dumps(title)};
        const match = chrome.windows().find(w => w.activeTab().title().includes(title));
        if (match) {{
            match.index = 1;
            chrome.activate();
            "focused";
        }} else {{
            "not found";
        }}
        """
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Could not focus Chrome window: {result.stderr}")

        return result.stdout.strip() == "focused"

    @staticmethod
    def _main_mac_chrome_pid() -> Optional[int]:
        """The user's Chrome: the main binary running without a custom --user-data-dir."""
        binary = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        processes = subprocess.run(
            ["ps", "-axo", "pid=,command="], capture_output=True, text=True, check=True
        ).stdout
        for line in processes.splitlines():
            pid, _, command = line.strip().partition(" ")
            is_chrome = command == binary or command.startswith(binary + " ")
            if is_chrome and "--user-data-dir" not in command:
                return int(pid)
        return None

    def async_focus_register_new(self):
        if not is_mac():
            print("MacOS not detected, won't try to focus")
            return False
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.focus_register_new)
        return future


if __name__ == "__main__":
    import fire

    fire.Fire(Focus)
