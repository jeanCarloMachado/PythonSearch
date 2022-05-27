from search_run.interpreter.cmd import CmdEntry


def send_notification(message):
    """ Sends a system notification and sanitizes in case of special chars """
    clean = message.replace("'", '')
    cmd = f"notify-send '{clean}'"
    CmdEntry({'cmd': cmd}).interpret_default()
