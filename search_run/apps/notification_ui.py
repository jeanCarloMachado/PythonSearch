
def send_notification(message : str):
    from search_run.environment import is_mac
    """Sends a system notification and sanitizes in case of special chars"""
    clean = message.replace("'", "")
    cmd = f"notify-send '{clean}'"

    if is_mac():
        cmd = f"""osascript -e 'display notification "{clean}"'"""

    from search_run.interpreter.cmd import CmdEntry
    CmdEntry({"cmd": cmd}).interpret_default()
