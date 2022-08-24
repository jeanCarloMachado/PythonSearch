# PythonSearch

With python search you collect and retrieve and refactor information efficiently.

- collect commands, scripts, snippets, urls, files, efficiently as python dictionaries
- search them using a smart (ML based) ranking or add shortcuts to them
- refactor, reuse, generate and further automate entries as they are code
- execute the registered entries possibly customizing the execution behaviour

<img src="https://i.imgur.com/pECSsjc.gif" width="720"/>

For an example of how an entries could look like see [here](https://github.com/jeanCarloMachado/PythonSearch/blob/main/python_search/init_project/entries_main.py).

## Minimal installation

This installation covers the minimun functionality of Python search.
Write a python script like this, and call it.

### 1. Install python search

```sh
pip install python-search
```

We support **Mac and Linux**.

### 2. Initialize your entries project

```sh
python_search new_project "MyEntries"
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
