import shlex
import subprocess

from python_search.host_system.system_paths import SystemPaths
from python_search.shortcut.keyd import Keyd
from python_search.shortcut.shortcuts import entry_shortcuts, keyd_remap, to_linux_accelerator


class XFCE:
    def __init__(self, configuration):
        self.configuration = configuration

    def generate(self):
        print("Generating XFCE-Shortcuts")
        run_key = SystemPaths.get_binary_full_path("run_key")

        for key, content in list(self.configuration.commands.items()):
            for shortcut in entry_shortcuts(content):
                accelerator = to_linux_accelerator(shortcut)
                if accelerator is None:
                    print(f"Skipping {shortcut} for '{key}': not bindable on Linux")
                    continue
                remap = keyd_remap(shortcut)
                if remap:
                    Keyd().ensure(*remap)
                command = f"{shlex.quote(run_key)} {shlex.quote(key)} --from_shortcut=True"
                print(f"{accelerator} -> {command}")
                subprocess.run(
                    [
                        "xfconf-query",
                        "-c",
                        "xfce4-keyboard-shortcuts",
                        "-p",
                        f"/commands/custom/{accelerator}",
                        "-n",
                        "-t",
                        "string",
                        "-s",
                        command,
                    ],
                    check=False,
                )
