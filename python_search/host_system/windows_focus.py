import os
from concurrent.futures import ThreadPoolExecutor


class Focus:

    def focus_register_new(self):
        return self.focus_window("python3", "Register New")


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
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.focus_register_new)
        return future



if __name__ == "__main__":
    import fire
    fire.Fire(Focus)
