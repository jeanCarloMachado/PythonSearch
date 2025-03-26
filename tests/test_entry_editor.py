

import os

from python_search.entry_capture.entries_editor import EntriesEditor


def test_ack():
    assert os.system(f"{EntriesEditor.ACK_PATH} --help") == 0