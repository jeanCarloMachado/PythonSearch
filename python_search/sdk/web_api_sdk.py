import requests
import json


class WebApiSDK:
    """
    A lightweight SDK for the web api
    """

    def __init__(self):
        pass

    def recent_history(self, return_json=False):
        """
        Returns the recent history of the user

        """

        result = requests.get(url="http://localhost:8000/recent_history")
        if return_json:
            return result.text

        data = json.loads(result.text)
        return data["history"]

    def generate_description(self, content, return_json=False):
        result = requests.post(url="http://localhost:8000/entry/generate_description", json={'content': content})
        if return_json:
            return result.text

        data = json.loads(result.text)
        return data

def main():
    import fire

    fire.Fire(WebApiSDK)


if __name__ == "__main__":
    main()
