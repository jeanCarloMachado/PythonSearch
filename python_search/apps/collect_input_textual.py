import json
import os
import subprocess
import tempfile

from python_search.host_system.system_paths import SystemPaths

OUTPUT_FILE = os.environ.get("OUTPUT_FILE")


class CollectInputTextual:
    """Textual-based input collection UI that can run standalone or wrapped in kitty."""

    def run(self):
        """Run the textual app directly (use when already inside a terminal)."""
        from textual.app import App
        from textual.widgets import Input

        output_file = OUTPUT_FILE

        class _CollectInputApp(App):
            def compose(self):
                yield Input(placeholder="Enter value", id="field1")

            def on_input_submitted(self, event):
                result = {"value": event.value}
                if output_file:
                    with open(output_file, "w") as f:
                        json.dump(result, f)
                else:
                    print(json.dumps(result))
                self.exit()

        _CollectInputApp().run()

    def run_in_kitty(self) -> dict | None:
        """Launch in a kitty window and return the result after it closes."""
        output_file = tempfile.mktemp(suffix=".json")
        binary = SystemPaths.get_binary_full_path("collect_input_textual")

        cmd = [
            SystemPaths.KITTY_BINNARY,
            "-1",  # Force new instance (don't connect to existing)
            "--title",
            "Input",
            "-o",
            "initial_window_width=60c",
            "-o",
            "initial_window_height=5c",
            "-o",
            "close_on_child_death=yes",
            "-e",
            "sh",
            "-c",
            f'OUTPUT_FILE="{output_file}" {binary} run',
        ]

        subprocess.run(cmd)

        if os.path.exists(output_file):
            with open(output_file) as f:
                result = json.load(f)
            os.remove(output_file)
            return result
        return None


def main():
    import fire

    fire.Fire(CollectInputTextual)


if __name__ == "__main__":
    main()
