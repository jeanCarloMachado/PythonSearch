from typing import Optional

from python_search.apps.window_manager import WindowManager
from python_search.environment import is_mac


class HideWindow:
    def hide(self, title: Optional[str] = None):
        """hide the search launcher -i2 specific"""
        if is_mac():
            import os

            os.system(
                """osascript -e 'tell application "System Events" to keystroke "h" using command down'"""
            )
            return
        WindowManager().hide_window(title)
