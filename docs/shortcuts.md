
## Python Search Shortcuts


All entries in python search can be assigned to shortcuts so you can get instantaneous access to the entries.

The following systems are supported for generating shortcuts:

- Mac using iCanHazShortcut
- Linux
  - Gnome
  - XFCE

In your entries define the shortcut:

```py
"explain descripbe code clipboard content": {
  "cmd": "prompt_editor ... ",
  "mac_shortcuts": ["⌘⇧E"],
  "gnome_shortcuts": ["Control+e"],
},
```

Then to generate the shortcuts run the following commands:

```sh
python_search config_shortcuts
```
