#!/usr/bin/env python3
import os


def build():
    result = os.system("docker build . -t ps:latest ")
    if result == 0:
        print("Build successful")
    else:
        raise Exception("Build failed")


def build_and_run():
    build()
    run()


def run(*, cmd="", entrypoint="", port=""):

    if entrypoint:
        entrypoint = f" --entrypoint '{entrypoint}'"

    if port:
        port = f" -p {port}"

    cmd = f"docker run {port} --expose 6379 --cpuset-cpus='0-6' -e 'PS_ENTRIES_HOME=/entries' -it -v $HOME/projects/PythonSearch:/src -v $HOME/projects/PySearchEntries/:/entries -v $HOME/.PythonSearch:/root/.PythonSearch -v $HOME/.data:/root/.data {entrypoint} ps {cmd}"
    os.system(cmd)


def run_webserver():
    run(cmd="python_search_webapi", port="8000:8000")


if __name__ == "__main__":
    import fire

    fire.Fire()
