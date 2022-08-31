import os

from python_search.environment import is_mac


class Project:
    def new(self, project_name):
        """
        Initialize a new project to use Python search and make sure all remaining dependencies exist
        """

        current_directory = os.getcwd()
        project_directory = f"{current_directory}/{project_name}"
        print(f"Initializing project in: {project_directory}")

        os.system(f"mkdir {project_name} 2>/dev/null")
        script_dir = os.path.dirname(os.path.realpath(__file__))

        copy_cmd = f"cp -r {script_dir}/entries_main.py {project_name}"
        os.system(copy_cmd)
        os.system(f"cd {project_name} && git init . 1>/dev/null ")

        self._install_kitty()
        self._install_fzf()
        self._set_current_project(project_directory)

        print(
            f"""Project created successfully! 

Your main config script can be found at {project_directory}/entries_main.py

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
