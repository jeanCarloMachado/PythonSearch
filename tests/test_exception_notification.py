from python_search.error.exception import notify_exception


def test_notify_exception_skips_missing_error_panel(monkeypatch):
    notifications = []

    monkeypatch.setattr(
        "python_search.apps.notification_ui.send_notification",
        notifications.append,
    )
    monkeypatch.setattr("python_search.error.exception.shutil.which", lambda cmd: None)
    system_calls = []
    monkeypatch.setattr(
        "python_search.error.exception.os.system",
        lambda cmd: system_calls.append(cmd),
    )

    @notify_exception()
    def raises():
        raise ValueError("boom")

    try:
        raises()
    except ValueError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("Expected ValueError")

    assert notifications == ["Exception boom"]
    assert system_calls == []
