# Reference of Entries options

The entries of search run are simple python dictionaries.

## cli_cmd

A shell command to run that should run in a new terminal window.

## Window title

The title that will be displayed in the new opened window

Example:

```py
"window_title": "RandomTerminal",
```

## focus_match

alue: String
Tries to match the window and focusing on it before opening a new one.

## app_mode

Type: Boolean, default False

## Before and after hooks

### run_before_cmd

Type: Str (shell command)

Runs synchronously in the shell **after** `call_before` (if any) and **before** the entry’s main action (open URL, run `cmd`, open file, etc.). Uses the same `directory` prefix as `cmd` when set. Fails fast if the command exits non-zero.

Example:

```py
"run_before_cmd": "osascript -e 'display notification \"Starting\"'",
"url": "https://example.com",
```

### call_after and call_before

Type: Str
An entry key to execute before or after running the current key.

Example:

```py
    "call_after": "python_search run_key 'localhost 5000'",
```

## shortcut / shortcuts

Type: Str / List[Str]

Global hotkeys that run the entry, e.g. `"shortcuts": ["⌘⇧E"]`. See [shortcuts.md](shortcuts.md)
for the full reference.

## notify_output

Type: Boolean, default False. Applies to `cmd` entries.

Shows the command's combined stdout/stderr as a system notification when it finishes (notify-send
on Linux, osascript on macOS). When the command exits non-zero the notification is titled as a
failure and shows the last 5 lines. Empty output sends nothing.

```py
"git pull monorepo": {"cmd": "git -C ~/prj/monorepo pull", "notify_output": True},
```

## Ask confirmation

"ask_confirmation": True,

To get a popup asking to continue before doing so.

# Before and After hooks

"call_before": "Staff engineering book notes",
"call_after": "restart i3",

## Other

"file": HOME + "/Desktop/books/StaffEng-Digital.pdf",  # opens with the default app (open / xdg-open)
"disable_sequential_execution": True,
