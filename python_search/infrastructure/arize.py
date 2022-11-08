import os

from arize.api import Client

class Arize:
    def get_client(self):
        API_KEY = os.environ["ARIZE_API_KEY"]
        SPACE_KEY = os.environ["ARIZE_SPACE_KEY"]
        return Client(space_key=SPACE_KEY, api_key=API_KEY)

