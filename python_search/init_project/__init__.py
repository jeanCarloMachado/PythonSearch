import os

from python_search.environment import is_mac


class Project:
    def new(self, new_project_location):
        """
        Initialize a new project to use Python search and make sure all remaining dependencies exist
        """

        if os.path.exists(new_project_location):
            raise Exception(f"{new_project_location} already exists")

        os.system(f"mkdir -p {new_project_location} 2>/dev/null")

        script_dir = os.path.dirname(os.path.realpath(__file__))
        copy_cmd = f"cp -r {script_dir}/entries_main.py {new_project_location}"
        os.system(copy_cmd)
        os.system(f"cd {new_project_location} && git init . 1>/dev/null ")

        self._install_kitty()
        self._install_fzf()
        self._set_current_project(new_project_location)

        print(
            f"""Project created successfully! 

Your main config script can be found at {new_project_location}/entries_main.py

You can now start using python search by issuing:
python_search search"""
        )

    def _set_current_project(self, project_directory):
        os.system("mkdir -p ~/.config/python_search/")
        os.system(
            f'echo "{project_directory}" >  ~/.config/python_search/current_project'
        )

    def _install_fzf(self):
        result = os.system("which fzf >/dev/null")
        if result == 0:
            print("Great, you have fzf alread installed")
            return

        print("Looks like kitty is not installed in your platform. ")
        if is_mac():
            print("Installing it for you...")
            os.system("brew install fzf")
        else:
            print(
                "Dont know how to install fzf for your platform, please do so manually"
            )

    def _install_kitty(self):
        result = os.system("which kitty >/dev/null")
        if result != 0:
            print(
                "Looks like kitty is not installed in your platform. Installing it for you..."
            )
            os.system(
                "curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin"
            )
