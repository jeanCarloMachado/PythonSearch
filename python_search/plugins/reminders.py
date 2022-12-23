import time


from python_search.apps.notification_ui import send_notification
from python_search.config import ConfigurationLoader, PythonSearchConfiguration


def get_random():
    config: PythonSearchConfiguration = ConfigurationLoader().load_config()
    print("Running reminder job")

    all_entries = config.commands

    reminders = {}
    for entry, content in all_entries.items():
        if "tags" in content and "Reminder" in content["tags"]:
            reminders[entry] = content

    import random

    random_key = random.choice(list(reminders.keys()))

    run_key(random_key)


from python_search.feature_toggle import FeatureToggle


def run_key(key):
    import os

    os.system(f"python_search run_key '{key}'")


def run_daemon():
    import schedule

    FeatureToggle().enable("reminders")
    schedule.every(15).minutes.do(get_random)

    entries = ConfigurationLoader().load_entries()
    for key, entry in entries.items():
        if "schedules" in entry:
            print("Found a schedule for key: " + key)
            for entry_schedule in entry["schedules"]:
                entry_schedule(schedule).do(run_key, key)

    print("entering loop")
    while True:
        feature_toggle = FeatureToggle()
        if feature_toggle.is_enabled("reminders"):
            print("Running pending")
            schedule.run_pending()
        else:
            print("Feature is disabled")

        print("Sleeping")
        time.sleep(1)


def main():
    import fire

    fire.Fire()


if __name__ == "__main__":
    main()
