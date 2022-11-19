FROM buildpack-deps:buster

RUN apt-get update -y && apt install default-jre -y
RUN apt-get install curl wget htop zsh -y

WORKDIR /src
COPY ./container /src/container
COPY pyproject.toml /src/pyproject.toml
COPY poetry.lock /src/poetry.lock
RUN /src/container/setup.sh


#RUN /root/.local/bin/poetry run pip install -e d

RUN apt-get install -y vim

ENV SHELL /bin/zsh
ENV PATH /root/miniconda3/envs/310/bin:/root/.local/bin:/root/miniconda3/bin:$PATH
RUN poetry export --dev --with-credentials --without-hashes -f requirements.txt -E server > requirements.txt && pip install -r requirements.txt
RUN pip install torch sentence-transformers lsof fastapi
RUN pip install streamlit --force-reinstall

COPY . /src


RUN pip install -e .
CMD zsh
