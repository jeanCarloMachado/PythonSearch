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


def run(cmd="", entrypoint="", port="", restart=False, extra_env_vars=None):

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

    LIMIT_CPU = 8
    cmd = f"docker run {port} {restart_exp} --expose=8000 --expose 4040 --expose 6380 --cpus={LIMIT_CPU} {environment_variables} -it {volumes} {entrypoint} ps {cmd}"
    print("Cmd: " + cmd)
    os.system(cmd)


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
        cmd="mlflow ui --backend-store-uri file:/entries/mlflow --port 5001 --host '0.0.0.0' ",
        port="5001:5001",
        restart=restart,
    )


def run_webserver(restart=False, force_restart=False):
    if force_restart:
        print("Stopping previously running container")
        os.system("docker stop $(docker ps | grep -i 8000 | cut -d ' ' -f1) ")
    run(
        cmd="python_search_webapi",
        port="8000:8000",
        restart=restart,
    )


def run_streamlit(restart=False, disable_password=False):
    run(
        cmd="streamlit run python_search/data_ui/main.py --server.address=0.0.0.0  --server.port=8501",
        port="8501:8501",
        restart=restart,
        extra_env_vars=[" -e 'PS_DISABLE_PASSWORD=1' "] if disable_password else None,
    )

def run_calendar(restart=True, disable_password=False):
    run(
        cmd="streamlit run /entries/calendar_app.py --server.address=0.0.0.0  --server.port=8502",
        port="8502:8502",
        restart=restart,
        extra_env_vars=[" -e 'PS_DISABLE_PASSWORD=1' "] if disable_password else None,
    )

def start():
    import fire

    fire.Fire()


if __name__ == "__main__":
    start
