import os
import shlex
import tempfile


class TerminatorTerminal:
    """
    Terminal abstraction for Python Search using Terminator, the default on Linux
    """

    # width x height in pixels; terminator's default window is too small
    GEOMETRY = "1400x900"

    def wrap_cmd_into_terminal(self, cmd, title=None, hold_terminal_open_on_end=True) -> str:
        """
        Wraps the command in a Terminator window but does not execute it.
        Writes the command to a temporary script to avoid complex escaping issues.
        """
        title_str = title if title else "PythonSearch"

        fd, script_path = tempfile.mkstemp(suffix=".sh", prefix="pythonsearch_")
        os.close(fd)

        with open(script_path, "w") as f:
            f.write("#!/bin/bash\n")
            # Add paths PythonSearch needs; the interactive shell below also loads ~/.bashrc
            f.write('export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"\n')
            from python_search.host_system.system_paths import SystemPaths

            python_path = SystemPaths.get_python_executable_path()
            f.write(f'export PATH="{python_path}:$PATH"\n')  # noqa: E231
            f.write("\n# Run the actual command\n")
            f.write(f"{cmd}\n")
            if hold_terminal_open_on_end:
                f.write('echo ""\n')
                f.write('echo "Press Enter to close..."\n')
                f.write("read\n")
            # Clean up the script after execution
            f.write(f"rm -f {shlex.quote(script_path)}\n")

        os.chmod(script_path, 0o755)

        # `--new-tab` reuses a running Terminator window; geometry only applies when none is open.
        # `bash -i` runs the script with the user's interactive environment (aliases, PATH).
        return (
            f"terminator --new-tab --geometry={self.GEOMETRY} --title {shlex.quote(title_str)} "
            f"-x bash -i {shlex.quote(script_path)}"
        )
