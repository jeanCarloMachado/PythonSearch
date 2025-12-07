

from python_search.host_system.windows_focus import Focus


def test_focus():
    result  = Focus().focus_window("Cursor", "Untitled")
    
    assert result