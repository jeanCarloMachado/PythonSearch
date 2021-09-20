import datetime

from fire import Fire

from search_run.cli import SearchAndRunCli

data = {
    # a browser url
    "search browser": {"url": "https://google.com"},
    # snippets to the clipboard
    "date current today now copy": {
        # anything can be
        "snippet": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "i3_shortcut": "Control+Shift+0",
    },
    # a shell command
    "watch current cpu frequency": {
        "new-window-non-cli": True,
        "cmd": """
                sudo watch \
                 cat /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_cur_freq
            """,
    },
}

instance = SearchAndRunCli(application_name="test", data=data)

Fire(instance)
