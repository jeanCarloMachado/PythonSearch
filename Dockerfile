FROM python:3.10-buster

RUN pip install python-search

RUN python_search new_project MyFunctions && python_search search
#COPY .:/src
#WORKDIR /src