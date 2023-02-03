#!/usr/bin/env python3
import os
from typing import Optional

from python_search.config import MLFlowConfig


def build():
    result = os.system("docker build . -t ps:latest ")
    if result == 0:
        print("Build successful")
    else:
        raise Exception("Build failed")


def build_and_run():
    build()
    run()


def run(
    cmd="",
    entrypoint="",
    port="",
    restart=False,
    extra_env_vars=None,
    name: Optional[str] = None,
):
    """
    Runs inside the docker container

    :param cmd:
    :param entrypoint:
    :param port:
    :param restart:
    :param extra_env_vars:
    :param name:
    :return:
    """

    if entrypoint:
        entrypoint = f" --entrypoint '{entrypoint}'"

    restart_exp = ""
    if restart:
        print("Adding restart flag")
        restart_exp = " --restart always "

    if port:
        port = f" -p {port}"

    volumes = " ".join(
        [
            " -v $HOME/projects/PythonSearch:/src ",
            " -v $HOME/.ssh:/root/.ssh ",
            " -v $HOME/projects/PySearchEntries/:/entries ",
            " -v $HOME/.PythonSearch:/root/.PythonSearch ",
            " -v $HOME/.ddataflow:/root/.ddataflow",
            " -v $HOME/.PythonSearch/container_cache/:/root/.cache ",
            " -v $HOME/.data:/root/.data" " -v $HOME/.gitconfig:/root/.gitconfig",
        ]
    )

    env_vars = [
        " -e 'PS_ENTRIES_HOME=/entries' ",
        " -e ARIZE_API_KEY=$ARIZE_API_KEY ",
        " -e ARIZE_SPACE_KEY=$ARIZE_SPACE_KEY ",
        " -e PS_WEB_PASSWORD=$PS_WEB_PASSWORD",
    ]

    env_vars = env_vars + extra_env_vars if extra_env_vars else env_vars

    environment_variables = " ".join(env_vars)

    name_expr = ""
    if name:
        name_expr = f" --name {name} "

    LIMIT_CPU = 8
    cmd = f"docker run {name_expr} {port} {restart_exp} --expose=8000 --expose 4040 --expose 6380 --cpus={LIMIT_CPU} {environment_variables} -it {volumes} {entrypoint} ps {cmd}"
    print("Cmd: " + cmd)
    os.system(cmd)


def run_webserver():
    name = "python_search_webserver"
    _stop_and_remove_by_name(name)

    run(
        cmd="python_search_webapi",
        port="8000:8000",
        name=name,
    )


def sh():
    shell()


def shell():
    run(entrypoint="/bin/bash")


def run_jupyter(with_token=False, restart=False):

    token_expression = " --NotebookApp.token=''"
    if with_token:
        token_expression = ""
    run(
        cmd=f"jupyter lab --allow-root --ip '*' --notebook-dir / {token_expression} --NotebookApp.password=''",
        port="8888:8888",
        restart=restart,
    )


def run_mlflow(restart=False):
    run(
        cmd=f"mlflow ui --backend-store-uri file:/entries/mlflow --port {MLFlowConfig.port} --host '0.0.0.0' ",
        port=f"{MLFlowConfig.port}:{MLFlowConfig.port}",
        restart=restart,
    )


def _restart_by_port(port):
    print("Stopping previously running container")
    os.system(f"docker stop $(docker ps | grep -i {port} | cut -d ' ' -f1) ; sleep 3")


def _stop_and_remove_by_name(name):
    print("Stopping previously running container")
    os.system(f"docker stop {name} ; docker rm {name}")


def run_streamlit(
    *, custom_entry_point: Optional[str] = None, restart=False, disable_password=False
):

    if restart:
        _restart_by_port(8501)

    entry_point = "python_search/data_ui/main.py"
    if custom_entry_point:
        entry_point = custom_entry_point

    run(
        cmd=f"streamlit run {entry_point} --server.address=0.0.0.0  --server.port=8501",
        port="8501:8501",
        restart=restart,
        extra_env_vars=[" -e 'PS_DISABLE_PASSWORD=1' "] if disable_password else None,
    )


def start():
    import fire

    fire.Fire()


if __name__ == "__main__":
    start
