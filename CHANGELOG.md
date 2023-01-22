# Changelog

## 0.10.1 (2023-01)

- Add support for chatgpt UI
- Separate FZF and kitty
- Always use the same kitty window
- New model for next item predictor


## 0.9.8


 - use constant variables to call ranking
 - improvements debugging
 - hability to query tags via query parameter
 - use mlflow config
 - fixes for pipeline next item predictor
 - tensorflow and running docker
 - override pyspark with local spark driver variable with same value
 - fix retrain pipeline using wrong python version
 - improve shortcut generation logic
 - fail if restart of shortcut fails



## 0.9.6

- add profiling

## 0.9.5

- Dev container
- Data exporter
- Arize integration

## 0.9.2
- improve development container
- updates dependencies
- add arize to type classifier

## 0.9.0
- Moving to dockerfile model

## 0.7.0

- Moving to an architecture without kafka

## 0.6.0

- Support customized tags while registering
- Preview window now also shows time slices of the created entry

## 0.5.8

- Use HOME from env variables to setup new project

## 0.5.7

- New project now takes the full path

## 0.5.6

- Remove systemd dependency for linux

## 0.5.1

Streamlined init_project script with better docs

## 0.5

Created a init_project "project_name" command to finalize the setup.

## 0.4.0

Minimal intallation supported.

## 0.3.1

-added customisation for the GUI Theme/Font_Size

## 0.3

- rename search_run module to python_search

## 2022-07-12

- Mac now closes the window when python search runs

## 2022-06-13

Make preview window work both on mac and linux by using python rather than shell.

## 2022-05-27

Add support to gnome shortcuts
