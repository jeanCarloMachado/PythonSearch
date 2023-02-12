# Single click configuration manual

This manual shows how to use karabiner elements to remap capslock to start python search in a single click.

1. Install the software: https://karabiner-elements.pqrs.org/

2. Remap ctrl-space to capslock

Ctrl-space is the default keybinding for python search. We will remap it to capslock.

Install a modification like this one:


```
{
  "title": "Python Search",
  "rules": [
    {
      "description": "",
      "manipulators": [
        {
          "type": "basic",
          "from": {
            "key_code": "caps_lock"
          },
          "to": [
            {
              "key_code": "spacebar",
              "modifiers": [
                "left_control"
              ]
            }
          ]
        }
      ]
    }
  ]
}
```