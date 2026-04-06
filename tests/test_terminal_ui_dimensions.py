from unittest.mock import patch
import os

from python_search.search.search_ui.terminal_ui import SearchTerminalUi


def test_display_rows_expand_to_fill_large_terminal_height():
    ui = SearchTerminalUi.__new__(SearchTerminalUi)

    with patch("python_search.search.search_ui.terminal_ui.shutil.get_terminal_size") as mock_size:
        mock_size.return_value = os.terminal_size((120, 22))

        assert ui._calculate_optimal_display_rows() == 20


def test_display_rows_keep_small_terminal_safe():
    ui = SearchTerminalUi.__new__(SearchTerminalUi)

    with patch("python_search.search.search_ui.terminal_ui.shutil.get_terminal_size") as mock_size:
        mock_size.return_value = os.terminal_size((120, 10))

        assert ui._calculate_optimal_display_rows() == 7
