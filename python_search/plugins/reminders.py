import time

import schedule

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

    feature_toggle = FeatureToggle()
    if feature_toggle.is_enabled("reminders"):
        content = (
            reminders[random_key]["snippet"]
            if "snippet" in reminders[random_key]
            else str(reminders[random_key])
        )
        send_notification(f"R: {content}, key={random_key}")
    else:
        print("reminders disabled in feature togle")


from python_search.feature_toggle import FeatureToggle


def run_daemon():

    feature_toggle = FeatureToggle()
    if feature_toggle.is_enabled("reminders_1m"):
        print("Enabling every minute")
        schedule.every(1).minutes.do(get_random)

    if feature_toggle.is_enabled("reminders_15m"):
        print("Enabling every 15 minutes")
        schedule.every(15).minutes.do(get_random)

    if feature_toggle.is_enabled("reminders_1h"):
        print("Enabling every hour")
        schedule.every(60).minutes.do(get_random)

    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    import fire

    fire.Fire()


if __name__ == "__main__":
    main()
