import os
from python_search.apps.collect_input import CollectInput
from python_search.apps.notification_ui import send_notification


class GoogleIt:
    def search(self, content):
        send_notification(f"Searching for {content} in Google")

        url = f"http://www.google.com/search?q={content}"

        if content.startswith("http://") or content.startswith("https://"):
            url = content

        os.system(f'browser open "{url}"')
    
    def ask_then_search(self):
        content = CollectInput().launch(name="Search Google", prefill_with_clipboard=True)
        self.search(content)


def main():
    import fire

    fire.Fire(GoogleIt())


if __name__ == "__main__":
    main()
