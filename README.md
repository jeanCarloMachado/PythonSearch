# PythonSearch

- collect pieces of actionable text in the internet and add them to python dictionaries
- search them using text similarity based on bert and many other ranking methods
- Run the searched entries, with customizeable actions
- add custom types and actions
- add shortcuts to actions

## Minimal installation

This installation covers the minimun functionality of Python search.
Write a python script like this, and call it.

### 1. Install python search

```sh
pip install python-search
```

### 2. Initialize your entries project

```sh
python-search init_project "MyEntries"
```
It will create a new git project for you for your entries.

### 3. Using

Done! You can run the search UI by running.

```shell
python_search search
```

Basically everything in python search you do through the cli tool.
To understand the options run:

```sh
python_search --help
```

You can also find the [code documentation here](https://jeancarlomachado.net/PythonSearch/).

## Legal

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE.txt) for the full text.\
Copyright 2022 Jean Carlo Machado
