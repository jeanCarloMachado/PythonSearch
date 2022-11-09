import os
import concurrent.futures as cf

from arize.api import Client

class Arize:

    MODEL_ID = "entry_type_classifier_v2"
    MODEL_VERSION = "v4"
    def get_client(self) -> Client:
        API_KEY = os.environ["ARIZE_API_KEY"]
        SPACE_KEY = os.environ["ARIZE_SPACE_KEY"]
        print('Arize API_KEY', API_KEY)
        print('Arize SPACE_KEY', SPACE_KEY)
        return Client(space_key=SPACE_KEY, api_key=API_KEY)


    def arize_responses_helper(responses):
        """
        responses: a list of responses from Arize
        returns: None
        """
        responses = [responses]
        for response in cf.as_completed(responses):
            res = response.result()
            if res.status_code != 200:
                raise ValueError(f'failed with code {res.status_code}, {res.text}')
            print("Arize succeeded with 200 status code")

