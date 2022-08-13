# PythonSearch

<!-- ![](https://i.imgur.com/86foqnf.gif) -->


- collect commands, scripts, snippets, urls, files, efficiently into your python entries database
- search them using a ml driven search or add shortcuts to them
- Execute the registered entries possibly customizing the execution behaviour

## Minimal installation

This installation covers the minimun functionality of Python search.
Write a python script like this, and call it.

### 1. Install python search

```sh
pip install python-search
```

We support Mac and Linux.

### 2. Initialize your entries project

```sh
python_search init_project "MyEntries"
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

## Got an issue?

Create a github issue to report it or send a patch.

## Contributing

Feature contributions are also welcomed! If you want to be part of the roadmap discussions reach out.

## Legal

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE.txt) for the full text.\
Copyright 2022 Jean Carlo Machado
