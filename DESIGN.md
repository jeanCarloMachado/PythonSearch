# PythonSearch Design

PythonSearch core is designed to run fully on the local machine.

There are two front ends over the same entries database and the same executor.

## Native launcher (default)

A resident Rust daemon holds the entries in memory and draws a Spotlight-style macOS panel.
Searching never leaves the process; running an entry shells out to the Python `run_key` binary so
all interpreter behaviour is shared. See `rust/README.md`.

```mermaid
graph LR
    A[User] -- hotkey --> B[ps_ui show]
    B -- unix socket --> C[ps_ui daemon]
    C -- fuzzy rank in memory --> D[egui panel]
    D -- Enter --> E[run_key]
    E --> F[InterpreterMatcher]
```

## Terminal UI (fallback)

`python_search search` opens a Kitty window running `term_ui`, a hand rolled ANSI UI that loads
entries by shelling out to the Python entries loader and ranks them with BM25.

```mermaid
graph LR
    A[User] -- python_search search --> B[Kitty window]
    B --> C[term_ui: BM25 over entries]
    C -- Enter --> D[run_key]
```

## Entries

Both front ends read the same database: `entries_main.py` in the entries project, which is
executable Python. The native launcher consumes a JSON dump of it
(`python_search _entries_loader dump_entries`) rather than importing Python on every launch.
