import os

from python_search.environment import is_mac

class InstallDependencies:
    def install_all(self):
        """
        Install all depenenceis to make python search work
        """

        self._install_fzf()
        self._install_kitty()
        self._install_ack()
        self._install_tk_mac()

    def _install_ack(self):
        print("Installing ack")
        if is_mac():
            self._install_brew_if_not_present()
            os.system("brew install ack")
        else:
            print(
                "Dont know how to install ack for your platform, please do so manually"
            )

    def _install_tk_mac(self):

        if not is_mac():
            return

        os.system("brew install python-tk")


    def _install_fzf(self):
        print("Installing FZF")

        if self._exists("fzf"):
            return

        print("Looks like kitty is not installed in your platform. ")
        if is_mac():
            self._install_brew_if_not_present()
            os.system("brew install fzf")
        else:
            print(
                "Dont know how to install fzf for your platform, please do so manually"
            )

    def _install_brew_if_not_present(self):
        if self._exists("brew"):
            print("Brew already installed!")
            return

        print("Installing brew for you...")
        os.system('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')

    def _exists(self, cmd: str):
        result = os.system(f"which {cmd} >/dev/null")
        if result == 0:
            print(f"Great, you have {cmd} alread installed")
            return True
        return False

    def _install_kitty(self):
        if self._exists("kitty"):
            return

        print(
            "Looks like kitty is not installed in your platform. Installing it for you..."
        )
        os.system(
            "curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin"
        )

        # sets a light theme in kitty
        os.system("kitty +kitten themes --reload-in=all One Half Light")
