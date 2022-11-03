FROM --platform=linux/amd64 python:3.10-buster


WORKDIR /src
COPY ./container /src/container
COPY pyproject.toml /src/pyproject.toml
COPY poetry.lock /src/poetry.lock
RUN /src/container/setup.sh


COPY . /src

RUN /root/.local/bin/poetry run pip install -e .

ENV SHELL /bin/bash
ENV PATH /root/.local/bin:$PATH

CMD poetry shell

