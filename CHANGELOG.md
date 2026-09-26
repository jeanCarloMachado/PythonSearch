# Changelog

## 2026-09-26

### Added
- One `shortcut` / `shortcuts` field on entries, written in Mac glyph notation (`⌘⌥⌃⇧` + key), replaces the per-platform `mac_shortcut(s)` and `xfce_shortcut(s)` fields. `python_search/shortcut/shortcuts.py` translates it for Karabiner, GNOME and XFCE; `capslock` and `right_command` can be bound on every platform.
- keyd integration (`python_search/shortcut/keyd.py`): on Linux, `python_search shortcuts` maps Caps Lock / right Super to a key combination in `/etc/keyd/default.conf` (via `sudo`) so desktops can bind them.
- Terminator terminal (`terminal_app="terminator"`), used by default on Linux since iTerm only exists on macOS.
- `python_search _entries_loader print_entries`: writes the rich entry records as JSON to stdout (entries modules' own prints go to stderr), so the Rust launcher reads entries without a dump file.
- Native launcher (`ps_ui`) runs on Linux (X11 and Wayland): the daemon keeps entries in memory and opens each window as a `ps_ui ui --entries-stdin` process fed over stdin; `PS_UI_THEME=system` follows GNOME's `color-scheme`.
- `notify_output` on `cmd` entries: show the command's output as a system notification when it finishes (notify-send / osascript), flagged as a failure with the last 5 lines when it exits non-zero (8a7f733).
- Rust native launcher `ps_ui` in `rust/` (ps-core, ps-mac, ps-ui crates): resident daemon, in-memory fuzzy ranking with usage boost, AppKit panel, LaunchAgent install script; `EntriesLoader.dump_entries()` export and `__PS_UI__` expansion in the Karabiner config (f772af4).
- `python_search register_new <key> <value> [--type]` to register an entry without the UI (96e2531).
- Configurable terminal app for `cli_cmd` entries via `terminal_app` (`iterm` default, `kitty`), see `TERMINAL_CONFIG.md` (7f10731).
- `app_mode` and `focus_match` on URL entries (6a26351).
- Ctrl+R in the terminal UI reloads entries from disk (81bb3e9).
- Tests for shortcut translation, keyd, `print_entries`, terminal selection, browser binary lookup, and Rust entry parsing / daemon protocol.

### Changed
- GNOME shortcuts only manage keybindings under the `python-search-` prefix instead of resetting all custom keybindings, so hand-made shortcuts survive; GNOME and shell-extension bindings on the same accelerator are released so the entry shortcut wins.
- XFCE shortcuts use the shared translation and call `run_key` by absolute path with `--from_shortcut=True`.
- `file` entries open with the platform's default app (`open` on macOS, `xdg-open` on Linux) as a background `cmd` instead of in Vim inside a terminal (1d82a5b).
- `ps_ui` no longer watches entry files: entries are reloaded only on `ps_ui reload` or the in-app reload (⌘R / Ctrl+R). The file watcher and the `notify` dependencies are removed.
- The Caps Lock → `ps_ui show` binding moved from `karabiner_base.json` into an entry (`"shortcut": "capslock"`).
- Linux: Chrome is the default browser (`google-chrome` or `google-chrome-stable`, with `--app` for `app_mode` / `focus_match`); Firefox is only used when Chrome is missing.
- `rg` and `kitty` are resolved from `PATH` before falling back to Homebrew paths; `ps_ui` also looks in `~/.local/bin` and uses `$SHELL` instead of `/bin/zsh` to find the PythonSearch binaries.
- Entry editor locates an entry by matching it as a dict key (`"key": `) rather than any occurrence of the text.
- `cmd` entries get `/usr/local/bin` on `PATH` (d46027b).
- Kitty terminals use the theme font (SF Mono) (f31f2bf, 3845b27); iTerm sessions keep their own font (b4b5408).
- Adaptive window width is capped at 100 columns on wide displays (72b0d11).
- PySimpleGUI added as a dependency (72037b5).

### Fixed
- `ps_ui` on Wayland: opens at full list height (a resize before the first configure was dropped, cutting results off), asks the compositor for focus, and exits when closed by the window manager.
- Entry editor no longer fails when ripgrep finds no match (exit code 1).
- `ps_ui` ⌘ key bindings work with Super on Linux: `rust/vendor/egui-winit` is a patched copy (via `[patch.crates-io]`) that maps Super to egui's `command` modifier, which upstream ignores.

### Removed
- Per-platform shortcut fields `mac_shortcut(s)`, `xfce_shortcut(s)`: migrate them to `shortcut` / `shortcuts`.

## [Unreleased]

### Added
- Native Rust "register new entry" form: `register_new_rust` binary alongside `ps_ui`, invoked via Alt+R outside the Python environment with full clipboard prefill and native window positioning.
- `Actions.register_new()` in Rust core: calls `python_search register_new` and waits for completion with stderr capture for error reporting (unlike fire-and-forget daemon actions).
- Window positioning for satellite forms (register-new): centered on primary screen, movable, distinct from the mouse-following launcher panel.
- Notification wrapping for silent cmd entries: on failure, toast the last stderr line; with `notify_output: true`, toast stdout/stderr even on success; wrapping runs inside the detached subprocess so notifications survive the CLI exit.
- PATH configuration in cmd interpreter: appends conda env bin paths so monorepo CLI tools (e.g. `monorepo` command) resolve from Karabiner's minimal environment.
- Tests in `rust/ps-core/src/actions.rs` for `register_new` success/failure, stderr capture, argument order, and missing-binary detection.
- Test for `share_only_value` with colons in keys (URLs, "Task: ..." entries) to prevent silent copy failures.
- `run_before_cmd` on entries: run a shell command synchronously before the main action (after `call_before` if set); respects `directory`; fails fast on non-zero exit.
- `run_shortcut` console script: resolve an entry key from a configured shortcut pattern (mac/gnome/xfce, single or list) and run it via `EntryRunner` with `from_shortcut=True` (Python Fire CLI).
- LLM-assisted delete for a single entry: `python_search.entry_capture.llm_delete_entry` (ripgrep → OpenAI sed/perl plan → apply with logged stdout/stderr → optional OpenAI retries on tool failure, BSD `sed -f` hints). Validates only via `EntriesLoader` before/after delta (same as Search UI).
- `entries_editor delete_key`: opens Kitty with the delete pipeline; Search UI **Ctrl+D** on a focused result row calls it via `Actions.delete_key` (Tab remains edit; Shift+D / `;` clear the query only).
- `EntriesLoader.count_entries_from_disk()`: reload config from disk and return `len(load_entries())` for tooling such as LLM delete validation.
- Tests in `tests/test_llm_delete_entry.py` for loader counts, snippet bounds, mocked delete flow, sed failure retry, and `delete_key --help`.

### Changed
- Launcher copy-to-clipboard UX: show "Copied" toast for 450ms before auto-hiding, rather than hiding instantly; improves visual feedback on successful copy.
- `run_before_cmd` execution in the base interpreter: capture subprocess output, forward stdout/stderr after completion, and append captured output to the error when the command fails; sequential execution is enabled only when `run_before_cmd` is non-empty.
- URL entries: `run_before_cmd` uses the shared base implementation (no duplicate pre-command path).
- `ConfigurationLoader.load_config` / `reload`: normalize entries folder to an absolute path, prepend it on `sys.path` (removing duplicates), drop a cached `entries_main` on reload, and refresh the loader singleton so disk edits and `PS_ENTRIES_HOME` match the Search UI and entry counts.
- Search UI shortcut docs: Tab (edit), Ctrl+D (LLM delete), Shift+D / `;` (clear query).
- Karabiner config template: registers new entries via native Rust form (Alt+R), preserving Python `register_new` console script for Rust form's subprocess call.

### Fixed
- `share_only_value` now uses the exact key passed, no longer truncates at colons: prevents silent failures on URLs and colon-containing entry keys.
- Exception notifications: call `error_panel` only when that executable is on `PATH`.
- Serialized entry decoding: treat plain entry text without `:` or with an empty payload after `:` as non-JSON and return `{}` instead of raising.

## 0.5 - 2024-06-17 Major simplifications

- Tailoring the project towards minimal setup

## 0.31 - 2024-01-27

- Replce fzf with a python native logic.
- Cleanup github sites.
- Cleanup tons of files

## 0.28 - 2023-11-02

- Performance improvements
- Change default theme to light one

## 0.27.1 - 2023-10-21

- Fixing things that were broken for glorious Linux-People.



## 0.27 -  2023-10-13

- Add better support to solarized theme
- Changed defualt window size
- disable llm by configuration again
- gracefully degrate on features without model

## 0.26 - 2023-08-19

- Add support to app_focus_title  in mac.
- Cleanup options in ps_search
- Add design doc


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
