# Setup machine for development of PythonSearch



## Developing PythonSearch

1. Clone the repo

```sh
git clone git@github.com:jeanCarloMachado/PythonSearch.git
```

2. Install the repo code in your enviroment

```sh
cd PythonSearch ; 
# install the program in devevelopment mode
pip install -e .
```

3. Create a feature branch, develop it!

```
git checkout -b my_dev_branch
```

# Sending a modification

On every change that modifies the code make sure to change the CHANGELOG.md and to increase the version in pyproject.toml


## Generating code docs

Run the following command and commit the results.

```sh
 pdoc --skip-errors --html python_search
```
