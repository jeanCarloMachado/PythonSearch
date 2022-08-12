

class InitializeProject():
    def initialize(self, project_name):
        """
        Initialize a new project to use Python search
        """
        import os

        current_directory = os.getcwd()
        print(f"Initializing project {project_name} at {current_directory}")

        os.system(f"mkdir {project_name}")
        script_dir = os.path.dirname(os.path.realpath(__file__))

        copy_cmd = f"cp -r {script_dir}/entries_main.py {project_name}"
        os.system(copy_cmd)
        os.system(f"cd {project_name} && git init . ")

        result = os.system("which kitty")
        if result != 0:
            print(
                "Looks like kitty is not installed in your platform. Installing it for you..."
            )
            os.system(
                "curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin"
            )

        print(
            f"""Project created! Now export the PS_ENTRIES_HOME variable in a init script of your shell, examples: 

echo 'export PS_ENTRIES_HOME={current_directory}/{project_name}'  >> ~/.bashrc
echo 'export PS_ENTRIES_HOME={current_directory}/{project_name}'  >> ~/.zshrc

Logout and login again so your system can pick up the changes.
"""
        )
