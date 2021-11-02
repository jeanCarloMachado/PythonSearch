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

Value: String
Tries to match the window and focusing on it before opening a new one.


## app_mode

Type: Boolean, default False


## call_before

Type: Str
An entry key to execute before.

## Other

"file": """/home/jean/Desktop/books/StaffEng-Digital.pdf""",
"call_before": "Staff engineering book notes",
"disable_sequential_execution": True,
