FROM python:3.10-buster

RUN pip install --upgrade pip ; pip install fire
#RUN pip install poetry && poetry config virtualenvs.create false

COPY . /src
WORKDIR /src

RUN pip install python-search
RUN poetry install --all-extras ; pip install -e .


