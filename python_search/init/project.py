import os

from python_search.environment import is_mac


class Project:
    def new_project(self, new_project_location):
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

        self.set_current_project(new_project_location)

        print(
            f"""Project created successfully! 

Your main config script can be found at {new_project_location}/entries_main.py

You can now start using python search by issuing:
python_search search"""
        )

    def set_current_project(self, project_location: str):
        """
        Sets an existing project as the one python search is using.
        """
        import os

        home = os.environ["HOME"]
        current_project_config = f"{home}/.config/python_search/current_project"

        os.system(f"mkdir -p {home}/.config/python_search/")
        os.system(f'echo "{project_location}" >  {current_project_config}')

        print(f"Successfuly set current project as: {project_location}")
