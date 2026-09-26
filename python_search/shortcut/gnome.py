#!/usr/bin/env python3
import ast
import glob
import os
import shlex
import subprocess

from python_search.entries_group import EntriesGroup
from python_search.host_system.system_paths import SystemPaths
from python_search.shortcut.keyd import Keyd
from python_search.shortcut.shortcuts import (
    entry_shortcuts,
    keyd_remap,
    to_linux_accelerator,
)


class Gnome:
    """
    Register entry shortcuts as GNOME custom keybindings.

    Only keybindings under the `python-search-` prefix are managed, so shortcuts created by hand in
    GNOME Settings are left alone. A GNOME or shell-extension binding that uses the same accelerator is
    removed so the entry shortcut wins.
    """

    LIST_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
    LIST_KEY = "custom-keybindings"
    ITEM_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
    BASE_PATH = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"
    PREFIX = "python-search-"

    # Schemas holding GNOME's own bindings, checked for clashes. Installed shell-extension schemas
    # (e.g. dash-to-dock's app hotkeys) are checked too.
    BUILTIN_SCHEMAS = (
        "org.gnome.desktop.wm.keybindings",
        "org.gnome.shell.keybindings",
        "org.gnome.mutter.keybindings",
        "org.gnome.mutter.wayland.keybindings",
        "org.gnome.settings-daemon.plugins.media-keys",
    )

    def __init__(self, configuration: EntriesGroup):
        self.configuration = configuration

    def generate(self):
        print("Generating gnome shortcuts")
        run_key = SystemPaths.get_binary_full_path("run_key")
        builtins = self._builtin_bindings()

        bindings = {}
        for key, content in list(self.configuration.commands.items()):
            for shortcut in entry_shortcuts(content):
                accelerator = to_linux_accelerator(shortcut)
                if accelerator is None:
                    print(f"Skipping {shortcut} for '{key}': not bindable on Linux")
                    continue
                if accelerator.lower() in bindings:
                    print(
                        f"Skipping {shortcut} for '{key}': already bound to '{bindings[accelerator.lower()][0]}'"
                    )
                    continue
                canonical = self._canonical(accelerator)
                for schemadir, schema, name in builtins.get(canonical, []):
                    print(
                        f"Overriding GNOME's '{schema} {name}' so {shortcut} ({accelerator}) runs '{key}'"
                    )
                    self._release(schemadir, schema, name, canonical)
                bindings[accelerator.lower()] = (key, accelerator)
                remap = keyd_remap(shortcut)
                if remap:
                    Keyd().ensure(*remap)

        managed = self._remove_managed()

        for number, (key, accelerator) in enumerate(bindings.values(), start=1):
            path = f"{self.BASE_PATH}{self.PREFIX}{number}/"
            command = f"{shlex.quote(run_key)} {shlex.quote(key)} --from_shortcut=True"
            self._set_item(path, "name", f"python search: {key}")
            self._set_item(path, "command", command)
            self._set_item(path, "binding", accelerator)
            managed.append(path)

        self._gsettings("set", self.LIST_SCHEMA, self.LIST_KEY, str(managed))
        print(f"Registered {len(bindings)} gnome shortcuts")

    def _remove_managed(self) -> list:
        """Drop the keybindings a previous run created and return the ones to keep."""
        current = self._read_list()
        kept = []
        for path in current:
            if path.startswith(self.BASE_PATH + self.PREFIX):
                self._gsettings("reset-recursively", f"{self.ITEM_SCHEMA}:{path}")
            else:
                kept.append(path)
        return kept

    def _read_list(self) -> list:
        raw = self._gsettings("get", self.LIST_SCHEMA, self.LIST_KEY).strip()
        # An empty list is printed with a type annotation: "@as []".
        return ast.literal_eval(raw.removeprefix("@as").strip())

    def _set_item(self, path: str, field: str, value: str):
        self._gsettings("set", f"{self.ITEM_SCHEMA}:{path}", field, value)

    def _builtin_bindings(self) -> dict:
        """Accelerator (canonical) → [(schemadir, schema, key)] of the GNOME actions already using it."""
        result = {}
        for schemadir, schema in self._builtin_schemas():
            try:
                listing = self._gsettings(*self._schema_args(schemadir), "list-recursively", schema)
            except subprocess.CalledProcessError:
                continue
            for line in listing.splitlines():
                parts = line.split(" ", 2)
                if len(parts) < 3:
                    continue
                value = self._parse(parts[2])
                for accelerator in value if isinstance(value, list) else [value]:
                    if isinstance(accelerator, str) and accelerator.startswith("<"):
                        result.setdefault(self._canonical(accelerator), []).append(
                            (schemadir, schema, parts[1])
                        )
        return result

    def _builtin_schemas(self) -> list:
        """[(schemadir, schema)]; schemadir is None for schemas installed system-wide."""
        schemas = [(None, schema) for schema in self.BUILTIN_SCHEMAS]
        seen = set(self.BUILTIN_SCHEMAS)
        for schema in sorted(self._gsettings("list-schemas").split()):
            if schema.startswith("org.gnome.shell.extensions.") and schema not in seen:
                schemas.append((None, schema))
                seen.add(schema)
        # Extensions installed per user ship their schemas inside the extension folder, invisible to
        # a plain `gsettings list-schemas`.
        for schemadir in self._extension_schemadirs():
            for schema in sorted(self._gsettings("--schemadir", schemadir, "list-schemas").split()):
                if schema.startswith("org.gnome.shell.extensions.") and schema not in seen:
                    schemas.append((schemadir, schema))
                    seen.add(schema)
        return schemas

    @staticmethod
    def _extension_schemadirs() -> list:
        roots = [
            os.path.expanduser("~/.local/share/gnome-shell/extensions"),
            "/usr/share/gnome-shell/extensions",
        ]
        return sorted(
            os.path.dirname(compiled)
            for root in roots
            for compiled in glob.glob(f"{root}/*/schemas/gschemas.compiled")
        )

    @staticmethod
    def _schema_args(schemadir) -> list:
        return ["--schemadir", schemadir] if schemadir else []

    def _release(self, schemadir, schema: str, name: str, canonical: str):
        """Remove one accelerator from a GNOME binding, keeping any others it has."""
        args = self._schema_args(schemadir)
        value = self._parse(self._gsettings(*args, "get", schema, name))
        if isinstance(value, list):
            remaining = [a for a in value if self._canonical(a) != canonical]
            self._gsettings(*args, "set", schema, name, str(remaining))
        else:
            self._gsettings(*args, "set", schema, name, "")

    @staticmethod
    def _parse(raw: str):
        try:
            return ast.literal_eval(raw.strip().removeprefix("@as").strip())
        except (ValueError, SyntaxError):
            return None

    @staticmethod
    def _canonical(accelerator: str) -> str:
        """GNOME writes modifiers in any order and as <Primary>/<Ctrl>; normalise for comparison."""
        accelerator = accelerator.replace("<Primary>", "<Control>").replace("<Ctrl>", "<Control>")
        modifiers = []
        while accelerator.startswith("<"):
            end = accelerator.index(">") + 1
            modifiers.append(accelerator[:end])
            accelerator = accelerator[end:]
        order = ["<Control>", "<Alt>", "<Shift>", "<Super>"]
        modifiers.sort(key=lambda m: order.index(m) if m in order else len(order))
        return ("".join(modifiers) + accelerator).lower()

    @staticmethod
    def _gsettings(*args) -> str:
        return subprocess.run(
            ["gsettings", *args], check=True, capture_output=True, text=True
        ).stdout
