import schedule
import time

from python_search.config import ConfigurationLoader, PythonSearchConfiguration
from python_search.apps.notification_ui import send_notification

def job():
    config: PythonSearchConfiguration = ConfigurationLoader().load_config()

    all_entries = config.commands

    reminders = {}
    for entry, content in all_entries.items():
        if 'tags' in content and 'Reminder' in content['tags']:
            reminders[entry] = content

    import random
    random_key = random.choice(list(reminders.keys()))

    send_notification(f"{reminders[random_key]}, key={random_key}")



def run_daemon():
    schedule.every(1).hours.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    import fire
    fire.Fire()
if __name__ == '__main__':
    main()


