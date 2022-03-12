from search_run.apps.terminal import Terminal


def send_notification(message, urgent=False):
    cmd = f'notify-send "{message}"'
    return Terminal.run_command(cmd)
