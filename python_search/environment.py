import os


def is_mac():
    import platform

    return platform.system() == "Darwin"


def is_archlinux():
    return 0 == os.system("uname -r | grep -i ARCH")


def is_debian_based():
    return 0 == os.system("cat /etc/*release | grep -i  debian")


def is_linux():
    return 0 == os.system("cat /etc/*release | grep -i  linux")
