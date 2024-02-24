import os
from concurrent.futures import ThreadPoolExecutor

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
