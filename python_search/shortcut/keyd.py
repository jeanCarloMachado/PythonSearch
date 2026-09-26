import subprocess


class Keyd:
    """
    Linux desktops cannot bind a lone key like Caps Lock, so keyd remaps it to a combination they can bind.

    Editing /etc/keyd needs root; `sudo` prompts in the terminal running `python_search shortcuts`.
    """

    CONFIG = "/etc/keyd/default.conf"

    def ensure(self, key: str, combination: str) -> bool:
        """Map `key` to `combination` unless something already maps it. Returns whether it is mapped."""
        try:
            with open(self.CONFIG) as f:
                lines = f.read().splitlines()
        except OSError:
            print(f"Caps Lock shortcut needs keyd, but {self.CONFIG} was not found")
            return False

        current = [line for line in lines if line.split("=")[0].strip() == key]
        if current:
            if current[0].split("=", 1)[1].strip() != combination:
                print(
                    f"Warning: keyd already maps {key} ({current[0].strip()}); "
                    f"the {key} shortcut expects `{key} = {combination}`"
                )
            return True

        if "[main]" in lines:
            at = lines.index("[main]") + 1
            lines[at:at] = [f"{key} = {combination}"]
        else:
            lines += ["", "[main]", f"{key} = {combination}"]

        print(f"Mapping {key} to {combination} in {self.CONFIG} (needs sudo)")
        written = subprocess.run(
            ["sudo", "tee", self.CONFIG],
            input="\n".join(lines) + "\n",
            text=True,
            stdout=subprocess.DEVNULL,
        )
        if written.returncode != 0:
            print("Could not update the keyd config")
            return False
        subprocess.run(["sudo", "keyd", "reload"], check=False)
        return True
