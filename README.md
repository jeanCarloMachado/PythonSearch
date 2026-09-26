
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

## Shortcuts

Give any entry a global hotkey with one `shortcut` / `shortcuts` field, written in Mac glyph
notation. The same definition is used on macOS (Karabiner), GNOME and XFCE:

```py
"open mail": {"url": "https://mail.google.com", "shortcuts": ["⌥M"]},
"launcher": {"cmd": "ps_ui show", "shortcut": "capslock"},
```

Then run `python_search shortcuts`. See [docs/shortcuts.md](docs/shortcuts.md) for the notation and
per-platform details.

## Native launcher (macOS and Linux)

There is a second front end: a Spotlight-style launcher written in Rust, in
**[`rust/`](rust/README.md)**. It is a single self-contained binary with no runtime dependencies.

A resident daemon holds the entries in memory and ranks them in-process, so searching never starts
a Python interpreter — the terminal UI boots two of them per launch. Running an entry still shells
out to `run_key`, so every interpreter behaviour is shared between the two front ends.

```sh
rust/install.sh     # macOS: build, install to ~/.local/bin/ps_ui, register the LaunchAgent
ps_ui show          # open the launcher
```

On Linux (X11 or Wayland) build it with `cargo build --release -p ps-ui` in `rust/`, start
`ps_ui daemon` at login, and bind `ps_ui show` to a key through an entry shortcut. See
[`rust/README.md`](rust/README.md#linux).

| | terminal UI (`term_ui`) | native launcher (`ps_ui`) |
|---|---|---|
| Startup | two Python interpreters per launch | resident, ~10 ms to show |
| Search | BM25 in Python over the full corpus | in-memory fuzzy match, 0.1–2 ms |
| Rendering | full ANSI repaint per keystroke | GPU (a macOS panel, or a window on Linux) |
| Host | a Kitty window | its own borderless window |

Both read the same entries and run the same executor; `term_ui` is untouched and remains available
via `python_search search`. See [`rust/README.md`](rust/README.md) for the source layout, key
bindings, ranking, and platform notes.

## Documentation

- [Entry options](docs/entries_options.md): every field an entry can have
- [Shortcuts](docs/shortcuts.md): global hotkeys for entries
- [Terminal configuration](TERMINAL_CONFIG.md): iTerm, Kitty or Terminator for `cli_cmd` entries
- [Changelog](CHANGELOG.md)

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

## Binaries

Installing the Python package (`pip install python-search`, or `poetry install` for development)
puts these console scripts on your `PATH`. They are defined in `pyproject.toml` under
`[tool.poetry.scripts]`:

| Binary | What it does |
|---|---|
| `python_search` | Main CLI: `search`, `shortcuts`, `register_new`, `new_project`, and more. Run it with no arguments for the full list |
| `pys` | Shortcut for `python_search search` |
| `term_ui` | The terminal search UI on its own |
| `run_key` | Run one entry by key, e.g. `run_key 'open mail'` |
| `run_shortcut` | Run the entry that owns a shortcut, e.g. `run_shortcut '⌘⇧E'` |
| `entries_editor` | Open an entry's definition in the editor (`edit_key`) or delete it (`delete_key`) |
| `share_entry` | Share an entry (`share_key <key>`) |
| `collect_input` | GUI window that asks for text (optionally prefilled from the clipboard) and prints it |
| `collect_input_textual` | Terminal (Textual) version of `collect_input` |
| `clipboard` | Read and write the clipboard |
| `browser` | Open a URL in the configured browser, cross-platform |
| `google_it` | Google a query, or open it directly if it is a URL |
| `notify_send` | Show a system notification |
| `register_new_launch_ui` | Broken: points at `entry_capture/entry_inserter_gui/register_new_gui.py`, which no longer exists. Use `python_search register_new_ui` |

The Rust workspace in [`rust/`](rust/README.md) adds one more:

| Binary | What it does |
|---|---|
| `ps_ui` | Native launcher: `daemon`, `show`, `hide`, `toggle`, `reload`, `quit`, `ui`, `search <query>`, `screenshot` |

`rust/install.sh` is a macOS helper script, not a binary: it builds `ps_ui`, installs it, and
registers the LaunchAgent.

### Building the Rust binaries

To build every binary in the Rust workspace and put it on your `PATH`:

```sh
cd rust
cargo build --release --workspace

# copy every built executable to ~/.local/bin
mkdir -p ~/.local/bin
find target/release -maxdepth 1 -type f -perm -u+x -exec install -m 0755 {} ~/.local/bin/ \;
```

If `~/.local/bin` (the installed binaries) or `~/.cargo/bin` (`cargo` itself, from rustup) is not on
your `PATH` yet, add them to your shell profile (`~/.bashrc` or `~/.zshrc`) and open a new shell:

```sh
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
```

Check it with `which ps_ui`. You need a Rust toolchain of 1.82 or newer (`rustup update`). On macOS,
`rust/install.sh` does the same for `ps_ui` and also registers the daemon as a LaunchAgent; on Linux
start `ps_ui daemon` at login yourself (see [`rust/README.md`](rust/README.md#linux)).
