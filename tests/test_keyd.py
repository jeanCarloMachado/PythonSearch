from unittest.mock import patch

from python_search.shortcut.keyd import Keyd


def _run(config_text, tmp_path):
    config = tmp_path / "default.conf"
    config.write_text(config_text)
    keyd = Keyd()
    keyd.CONFIG = str(config)
    with patch("python_search.shortcut.keyd.subprocess.run") as run:
        run.return_value.returncode = 0
        mapped = keyd.ensure("capslock", "C-A-M-space")
    written = [c for c in run.call_args_list if c.args[0][:2] == ["sudo", "tee"]]
    return mapped, written[0].kwargs["input"] if written else None


def test_adds_caps_lock_under_main(tmp_path):
    mapped, written = _run("[ids]\n*\n\n[main]\n\n[meta]\nc = C-insert\n", tmp_path)

    assert mapped
    assert written == "[ids]\n*\n\n[main]\ncapslock = C-A-M-space\n\n[meta]\nc = C-insert\n"


def test_leaves_existing_mapping_alone(tmp_path):
    mapped, written = _run("[main]\ncapslock = C-A-M-space\n", tmp_path)

    assert mapped
    assert written is None


def test_adds_right_command_next_to_caps_lock(tmp_path):
    config = tmp_path / "default.conf"
    config.write_text("[main]\ncapslock = C-A-M-space\n")
    keyd = Keyd()
    keyd.CONFIG = str(config)
    with patch("python_search.shortcut.keyd.subprocess.run") as run:
        run.return_value.returncode = 0
        assert keyd.ensure("rightmeta", "C-A-M-r")

    assert run.call_args_list[0].kwargs["input"] == "[main]\nrightmeta = C-A-M-r\ncapslock = C-A-M-space\n"
