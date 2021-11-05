import os


def hide_launcher():
    os.system("i3-msg '[title=launcher] move scratchpad'")
