import os


def is_mac():
    import platform

    return platform.system() == "Darwin"


def is_archlinux():
    return 0 == os.system("uname -r | grep -i ARCH")
