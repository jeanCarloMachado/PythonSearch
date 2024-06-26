
# PythonSearch

Python search is a minimal search engine writting in python for developers productivity.
With PythoSearch you collect and retrieve and refactor information efficiently.

- collect commands, scripts, prompts, snippets, urls, files, efficiently as python dictionaries
- retrieve or execute the registered entries (depending on the type) either by searching them or invoking them via shortcuts
- refactor, reuse, generate and further automate entries as they are code
 
Check out [these slides](https://docs.google.com/presentation/d/10J0n0wdXYKCtB-tr2z4twY3T4TFBb8h2EGZghw7q1hk/edit#slide=id.p) if you want to know more

<img src="https://i.imgur.com/pECSsjc.gif" width="620"/>


For an example of how an entries could look like see [here](https://github.com/jeanCarloMachado/PythonSearch/blob/e424868662bda4d9daa314e6e77d4cc79a511a95/python_search/init/entries_main.py).


## Minimal installation

This installation covers the minimun functionality of Python search.
Write a python script like this, and call it.

### 1. Install python search

```sh
pip install python-search && python_search install_missing_dependencies
```
Note that you might need to upgrade your pip first: `pip install --upgrade pip`

To access the CLI manual and understand the options run:

```sh
python_search
```

Everything in python search you do through the cli tool.

We support **Mac and Linux**.

If you want to develop python-search install it via [the instructions in the contributing doc](CONTRIBUTING.md)


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

Read our documentaiton here for more in [depth knwoledge](https://docs.google.com/document/d/1Y_-kdEea9IQshUU-anWKC8sDUJ_y3XRvQJWZ6CV3pWw/edit#heading=h.kwxo59w3vr4x).


## Got an issue?

Create a github issue to report it or send a patch.

## Contributing

Feature contributions are also welcomed! If you want to be part of the roadmap discussions reach out.

## Contributors
 
- Aeneas Christodoulou
- Jean Machado
- Thallys Costa


## Supported Systems

PythonSearch officially supports MacOS and Linux. 

## Legal

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full text.\
Copyright 2022 Jean Carlo Machado


See also our [website](https://jeancarlomachado.github.io/PythonSearch/)
