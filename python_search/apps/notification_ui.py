def send_notification(message: str):
    """
    Sends a system notification. Raises if the notifier is missing or fails.
    """
    import shutil
    import subprocess

    from python_search.environment import is_mac

    if is_mac():
        clean = message.replace("'", "").replace('"', "")
        cmd = ["osascript", "-e", f'display notification "{clean}"']
    else:
        notify_send = shutil.which("notify-send") or "/usr/bin/notify-send"
        cmd = [notify_send, "python search", message]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    if result.returncode != 0:
        raise Exception(f"Notification failed ({' '.join(cmd[:1])}): {result.stderr.strip()}")


def main():
    import fire

    fire.Fire(send_notification)


if __name__ == "__main__":
    main()
