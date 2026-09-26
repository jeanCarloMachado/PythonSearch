# Terminal Configuration

PythonSearch now supports multiple terminal applications for running `cli_cmd` commands.

## Default Terminal

**iTerm2** is the default on macOS. iTerm only exists on macOS, so on Linux **Terminator** is used
instead, unless `terminal_app="kitty"` is set.

## Supported Terminals

- **iTerm2** (default) - Uses AppleScript to create new windows/tabs. Commands are executed via temporary shell scripts to ensure proper handling of special characters.
- **Kitty** - The original terminal used by PythonSearch with extensive customization options
- **Terminator** (default on Linux) - Opens a new tab (or a 1400x900 window when none is open) running the command through a temporary script with `bash -i`, so aliases and `PATH` from `~/.bashrc` apply.

## Switching Terminal Applications

To use a different terminal, add the `terminal_app` parameter to your `PythonSearchConfiguration` in `entries_main.py`:

### Use iTerm2 (default)
```python
config = PythonSearchConfiguration(
    entries=entries,
    terminal_app="iterm"  # This is the default, can be omitted
)
```

### Use Kitty
```python
config = PythonSearchConfiguration(
    entries=entries,
    terminal_app="kitty"
)
```

### Use Terminator
```python
config = PythonSearchConfiguration(
    entries=entries,
    terminal_app="terminator"
)
```

## Notes

- The Search UI (fzf interface) continues to use Kitty regardless of this setting, as it relies on Kitty-specific features
- This configuration only affects commands run via `cli_cmd` entries
- Both terminals must be installed on your system to use them
- iTerm2 implementation creates temporary shell scripts that self-delete after execution, avoiding complex shell escaping issues

## Implementation Details

### iTerm2
- Uses AppleScript via `osascript` to communicate with iTerm2
- Creates temporary executable shell scripts in `/tmp` for each command
- Scripts automatically clean themselves up after execution
- Tries to create a new tab first, falls back to new window if no window exists
- Supports window titles and "hold terminal open" mode

### Terminator
- Writes the command to a temporary script that adds `~/.local/bin`, `~/.cargo/bin` and the Python bin dir to `PATH`, then deletes itself
- Runs `terminator --new-tab --geometry=1400x900 --title <title> -x bash -i <script>`
- Supports window titles and "hold terminal open" mode

### Kitty
- Uses Kitty's command-line interface with extensive options
- Supports custom window sizing, fonts, and themes
- Provides fine-grained control over terminal behavior
