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
        self._install_ripgrep()
        self._install_tk()
        self._install_zsh_mac()
        self._install_wctrl()
        self._install_xsel()
        self._install_ripgrep()

        print(
            """
Installation successful!
        """
        )

    def _install_ripgrep(self):
        print("Installing ripgrep (rg) - fast file search tool")
        if is_mac():
            self._install_brew_if_not_present()
            os.system("brew install ripgrep")
        elif is_debian_based():
            os.system("sudo apt-get install ripgrep")
        elif is_archlinux():
            os.system("sudo pacman -S ripgrep")
        else:
            print("Don't know how to install ripgrep for your platform, " "please install manually")
            print("Visit: https://github.com/BurntSushi/ripgrep#installation")

    def _install_tk(self):
        if is_mac():
            os.system("brew install python-tk")
        if is_archlinux():
            os.system("sudo pacman -S tk")

    def _install_zsh_mac(self):
        if not is_mac():
            return

        os.system("brew install zsh")

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
        cmd = (
            f"git clone --depth 1 https://github.com/junegunn/fzf.git "  # noqa: E231
            f"{HOME}/.fzf && yes | {HOME}/.fzf/install"
        )
        os.system(cmd)

    def _install_brew_if_not_present(self):
        print("Brew checking...")
        if self._exists("brew"):
            print("Brew already installed!")
            return

        print("Installing brew for you...")
        os.system('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/' 'Homebrew/install/HEAD/install.sh)"')

    def _exists(self, cmd: str):
        result = os.system(f"which {cmd} >/dev/null")
        if result == 0:
            print(f"Great, you have {cmd} alread installed")
            return True
        return False

    def _install_kitty(self):
        if self._exists("kitty"):
            return

        print("Looks like kitty is not installed in your platform. " "Installing it for you...")

        if is_debian_based():
            os.system("sudo apt-get install kitty")
            return

        print("Installing kitty manually via curl")
        os.system("brew install --cask kitty")

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
