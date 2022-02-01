
from search_run.apps.terminal import Terminal


def send_notification(message, urgent=False):
    cmd = f"notify-send '{message}'"
    if urgent:
        cmd = f"{cmd} -u critical"
    return Terminal.run_command(cmd)
