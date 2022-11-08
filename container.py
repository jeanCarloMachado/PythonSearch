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

    volumes = " ".join([
        " -v $HOME/projects/PythonSearch:/src ",
        " -v $HOME/projects/PySearchEntries/:/entries ",
        " -v $HOME/.PythonSearch:/root/.PythonSearch ",
        " -v $HOME/.PythonSearch/container_cache/:/root/.cache ",
        " -v $HOME/.data:/root/.data"
    ])

    environment_variables = " ". join([
        " -e 'PS_ENTRIES_HOME=/entries' ",
        " -e ARIZE_API_KEY=$ARIZE_API_KEY ",
        " -e ARIZE_SPACE_KEY=$ARIZE_API_SPACE_KEY ",
    ])

    cmd = f"docker run {port} --expose 6379 --cpuset-cpus='0-6' {environment_variables} -it {volumes} {entrypoint} ps {cmd}"
    print("Cmd: " + cmd)
    os.system(cmd)

def sh():
    run(entrypoint="/bin/bash")

def run_jupyter():
    run(cmd="jupyter lab --allow-root --ip '*' --notebook-dir /", port="8888:8888")
def run_mlflow():
    run(cmd="mlflow ui --backend-store-uri file:/entries/mlflow --port 5001 --host '0.0.0.0' --port='5001:5001'", port="5001:5001")

def run_webserver():
    run(cmd="python_search_webapi", port="8000:8000")


def main():
    import fire

    fire.Fire()

if __name__ == "__main__":
    main
