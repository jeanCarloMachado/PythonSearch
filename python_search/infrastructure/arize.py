import os
import concurrent.futures as cf


class Arize:

    MODEL_ID = "entry_type_classifier_v2"
    MODEL_VERSION = "v5"

    @staticmethod
    def is_installed() -> bool:
        try:
            import arize

            return True
        except:
            return False

    def get_client(self):
        if not Arize.is_installed():
            return None

        API_KEY = os.environ["ARIZE_API_KEY"]
        SPACE_KEY = os.environ["ARIZE_SPACE_KEY"]

        if not API_KEY or not SPACE_KEY:
            print(
                "Arize cannot be created without both API_KEY and SPACE_KEY, values: "
                + API_KEY
                + " "
                + SPACE_KEY
            )
            return

        from arize.api import Client

        return Client(space_key=SPACE_KEY, api_key=API_KEY)

    def arize_responses_helper(responses):
        """
        responses: a list of responses from Arize
        returns: None
        """
        responses = [responses]
        for response in cf.as_completed(responses):
            res = response.result()
            print(res.status_code)
            if res.status_code != 200:
                raise ValueError(f"failed with code {res.status_code}, {res.text}")
            print("Arize succeeded with 200 status code")
