# Setup machine for development of PythonSearch


1. Clone python search source code
2. Install it in a local python, (conda or virtualenviroment recommended)
3. Create a feature branch, develop it!

# Requirements

On every change that modifies the code make sure to change the CHANGELOG.md and to increase the version in pyproject.toml

## Generating code docs

Run the following command and commit the results.

```sh
 pdoc --skip-errors --html python_search
```
