import os
from concurrent.futures import ThreadPoolExecutor


class Focus:

    def focus_register_new(self):
        result = os.system("""
        osascript -e 'tell application "System Events" to tell process "python3"
                set frontmost to true
                windows where title contains "Register New"
                if result is not {} then perform action "AXRaise" of item 1 of result
end tell' 
        """)

        return True if result == 0 else False

    def async_focus_register_new(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.focus_register_new)
        return future



if __name__ == "__main__":
    import fire
    fire.Fire(Focus)
