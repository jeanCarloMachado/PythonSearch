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

### call_after and call_before

Type: Str
An entry key to execute before or after running the current key.

Example:

```py
    "call_after": "python_search run_key 'localhost 5000'",
```

## Ask confirmation

"ask_confirmation": True,

To get a popup asking to continue before doing so.

# Before and After hooks

"call_before": "Staff engineering book notes",
"call_after": "restart i3",

## Other

"file": ""HOME + "/Desktop/books/StaffEng-Digital.pdf""",
"disable_sequential_execution": True,
