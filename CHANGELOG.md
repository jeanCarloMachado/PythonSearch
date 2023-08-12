# Changelog

## 0.25

- Support for focusing on register new window for mac
- Remove i3 support as it is likelly not working anymore

## 0.24.9
- Fix Issues with Debian Installation
- Update Installation Instructions
- Reworked LLM Config to be customizable
- Fixed CI-Related issues with pypi

## 0.24

- Drop scikit

## 0.23
 - explore llms
 - entries loader
 - privancy component

## 0.22

- Add new models exploration
- Train extensivly on base t5
- delete old next item predictor code base

## 0.21

- Add entry type classifier
- Improve register new speed
- Expriment with more data

## 0.20
- Dependencies groups
- LLM setup

## 0.18
- Next item predictor functional

## 0.17.1
- fixing Browser Issues on Linux
- making Browser/URL-Code more resiliant 
- Implementing Browser Tests
## 0.17

- Improve install script

## 0.16

- Fix rank
- Improve image

## 0.15

- Disable entry generation by default

## 0.14

- Add semantic search


## 0.11

- Add google it script (ctrl-g)
- Many improvements related to LLMs
    - Generate new prompt via shortcut on entry editor (ctrl-g)
    - Add prompt editor to fzf search (ctrl-p)
    - Add new entry suggestions at typing time using chatgpt

## 0.10.14

- Added examples for body generation
- Streamlit improvements
  - Add performance page
  - Documentation on how to use the website

## 0.10.13

-Adding support for XFCE
-Removing more legacy i3 Code
-New is_linux function
-Changing default browser logic


## 0.10.11

- Improve docs about shortcuts
- Add docs about data collection
- Fix bug printing trash on the search
- Fix copy to clipboard with special characters

## 0.10.10

- Improve docs about search ui
- Add error panel to display exception traces
- Add project image

## 0.10.9

- Improve docs
- Add feature to share entry <Ctrl+S> in fzf to do it.


## 0.10.8

- Improve prompt editor experience 
- Improve archlinux installation process
- Support for "<CLIPBOARD>" in prompts to replace with clipboard content
 
## 0.10.7

- Removing Support for i3 in Favor of GNOME
- Fixing smaller issues with setting up python_search in GNOME

## 0.10.6

- [Backward incompatible] default_fzf_theme renamed to fzf_theme
- Imrpove fzf themes 
- Improve preview window
 
## 0.10.5

- Small UI-Fixes on Linux
 
## 0.10.4

- Installation automations for mac
- Remove deafult theme customizations

## 0.10.3

- Installation automations for mac

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
