import tempfile
import os

from python_search.apps.theme.theme import get_current_theme


class ITermTerminal:
    """
    Terminal abstraction for Python Search using iTerm2
    """

    def wrap_cmd_into_terminal(self, cmd, title=None, hold_terminal_open_on_end=True) -> str:
        """
        Wraps the command in an iTerm2 terminal but does not execute it.
        Creates a temporary shell script to avoid complex escaping issues.
        """
        title_str = title if title else "PythonSearch"
        theme = get_current_theme()
        font_spec = f"{theme.font} {theme.font_size}"

        # Create a temporary script file to execute
        fd, script_path = tempfile.mkstemp(suffix=".sh", prefix="pythonsearch_")
        os.close(fd)

        # Write the command to the script
        with open(script_path, "w") as f:
            f.write("#!/bin/zsh\n")
            # Source user's zsh profile to get their PATH and environment
            f.write("# Load user shell environment\n")
            f.write("[[ -f ~/.zshrc ]] && source ~/.zshrc\n")
            f.write("[[ -f ~/.zprofile ]] && source ~/.zprofile\n")
            # Add common paths that PythonSearch needs
            f.write("# Add standard paths\n")
            f.write('export PATH="/opt/homebrew/bin:$PATH"\n')
            f.write('export PATH="$HOME/.local/bin:$PATH"\n')
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
            f.write(f'rm -f "{script_path}"\n')

        # Make script executable
        os.chmod(script_path, 0o755)

        # Build AppleScript - using heredoc to avoid escaping issues
        # The script will delete itself after running
        applescript = f"""osascript <<'EOF'  # noqa: E271, E272
tell application "iTerm"
    activate
    try
        tell current window
            create tab with default profile command "{script_path}"
            tell current session
                set name to "{title_str}"
                set normal font to "{font_spec}"
            end tell
        end tell
    on error
        create window with default profile command "{script_path}"
        tell current window
            tell current session
                set name to "{title_str}"
                set normal font to "{font_spec}"
            end tell
        end tell
    end try
end tell
EOF"""

        return applescript
