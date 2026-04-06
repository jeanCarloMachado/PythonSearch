from unittest.mock import patch
import os

from python_search.host_system.display_detection import AdaptiveWindowSizer, DisplayInfo
from python_search.search.search_ui.terminal_ui import SearchTerminalUi


def test_display_rows_stay_compact_on_large_terminal_height():
    ui = SearchTerminalUi.__new__(SearchTerminalUi)

    with patch("python_search.search.search_ui.terminal_ui.shutil.get_terminal_size") as mock_size:
        mock_size.return_value = os.terminal_size((120, 22))

        assert ui._calculate_optimal_display_rows() == 9


def test_display_rows_keep_small_terminal_safe():
    ui = SearchTerminalUi.__new__(SearchTerminalUi)

    with patch("python_search.search.search_ui.terminal_ui.shutil.get_terminal_size") as mock_size:
        mock_size.return_value = os.terminal_size((120, 10))

        assert ui._calculate_optimal_display_rows() == 7


def test_adaptive_window_height_is_capped_on_large_display():
    class FakeDisplayDetector:
        def get_display_info(self):
            return DisplayInfo(width=3840, height=2160, dpi=96.0, scale_factor=1.0)

    width, height = AdaptiveWindowSizer(FakeDisplayDetector()).get_adaptive_window_size()

    assert width == "172c"
    assert height == "12c"
