import os

MANUAL_ADDED_PACKAGES = ['tqdm', 'regex', 'requests',  'packaging', 'filelock', 'numpy', 'tokenizers', 'bitsandbytes']


def build_and_run():
    project_root = '/Users/jean.machado/projects/PythonSearch'
    libs = '/Users/jean.machado/miniconda3/envs/python310/lib/python3.10/site-packages'
    register_new_path = f'{project_root}/python_search/entry_capture/entry_inserter_gui/register_new_gui.py'
    collect_modules = ' '.join([f' --collect-all {package} ' for package in MANUAL_ADDED_PACKAGES])
    cmd = f'pyinstaller --paths {libs} -w --onedir --noconfirm --specpath {project_root} --clean -F  {register_new_path} {collect_modules} --name register_new_app '
    print("Command to run is: ", cmd)

    os.system(cmd)

    print("Now print the dist folder")
    os.system("ls -l dist")


    print("Now trying to run the program")
    os.system("./dist/register_new_app ")


def main():

    import fire
    fire.Fire()

if __name__ == "__main__":
    main()

