from typing import Union

import requests
import json

from python_search.entry_description_generator.description_geneartor import (
    EntryKeyGeneratorCmd,
)


class PythonSearchWebAPISDK:
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

    def generate_description(
        self, generator_cmd: Union[dict, EntryKeyGeneratorCmd], return_json=False
    ):
        if type(generator_cmd) == dict:
            generator_cmd = EntryKeyGeneratorCmd(**generator_cmd)
        result = requests.post(
            url="http://localhost:8000/entry/generate_description",
            json=generator_cmd.dict(),
        )
        if return_json:
            return result.text

        data = json.loads(result.text)
        return data


def main():
    import fire

    fire.Fire(PythonSearchWebAPISDK)


if __name__ == "__main__":
    main()
