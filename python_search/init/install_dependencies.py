import os

from python_search.environment import is_mac, is_archlinux, is_debian_based


class InstallDependencies:
    """
    Install dependencies that cannot be served via pip
    """

    def install_all(self):
        """
        Install all dependencies to make python search work
        """

        self._install_fzf()
        self._install_kitty()
        self._install_ack()
        self._install_tk()
        self._install_zsh_mac()
        self._install_shortcut_mac()
        self._install_wctrl()
        self._install_xsel()

        print(
            """
Installation successful!
        """
        )

    def _install_ack(self):
        print("Installing ack")
        if is_mac():
            self._install_brew_if_not_present()
            os.system("brew install ack")
        if is_debian_based():
            os.system("sudo apt-get install ack")
        else:
            print(
                "Dont know how to install ack for your platform, please do so manually"
            )

    def _install_tk(self):
        if is_mac():
            os.system("brew install python-tk")
        if is_archlinux():
            os.system("sudo pacman -S tk")

    def _install_zsh_mac(self):
        if not is_mac():
            return

        os.system("brew install zsh")

    def _install_shortcut_mac(self):
        if not is_mac():
            return

        os.system("brew install icanhazshortcut")

        HOME = os.environ["HOME"]
        # the branch to download the files from
        branch = "main"

        print("Downloading keyboard config ")
        self.download_file(
            f"https://raw.githubusercontent.com/jeanCarloMachado/PythonSearch/{branch}/docs/config.ini.part1",
            f"{HOME}/.config/iCanHazShortcut/config.ini.part1",
        )

        print("Downloading bom script ")
        self.download_file(
            f"https://raw.githubusercontent.com/jeanCarloMachado/PythonSearch/{branch}/add_bom_to_file.sh",
            "/usr/local/bin/add_bom_to_file.sh",
        )
        os.system("chmod +x /usr/local/bin/add_bom_to_file.sh")

    def download_file(self, url, destination):
        print(f"Downloading file from '{url}' into '{destination}'")
        os.system(f"curl {url} --output {destination}")

    def _install_fzf(self):
        print("Checking fzf")

        if is_debian_based():
            os.system("sudo apt-get install fzf")
            return

        print("Installing fzf manually")

        HOME = os.environ["HOME"]
        if os.path.exists(f"{HOME}/.fzf/"):
            print("Fzf already installed!, will reinstall..")
            os.system(f"rm -rf {HOME}/.fzf/")

        print("Looks like kitty is not installed in your platform. ")
        os.system(
            f""" git clone --depth 1 https://github.com/junegunn/fzf.git {HOME}/.fzf ; yes | {HOME}/.fzf/install """
        )

    def _install_brew_if_not_present(self):
        print("Brew checking...")
        if self._exists("brew"):
            print("Brew already installed!")
            return

        print("Installing brew for you...")
        os.system(
            '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        )

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

        if is_debian_based():
            os.system("sudo apt-get install kitty")
            return

        print("Installing kitty manually via curl")
        os.system(
            "curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin"
        )

        # sets a light theme in kitty
        os.system("kitty +kitten themes --reload-in=all One Half Light")

    def _install_wctrl(self):
        if is_archlinux():
            os.system("sudo pacman -S wmctrl")

        if is_debian_based():
            os.system("sudo apt-get install wmctrl")

    def _install_xsel(self):
        if is_debian_based():
            os.system("sudo apt-get install xsel")
        if is_archlinux():
            os.system("sudo pacman -S xsel")
