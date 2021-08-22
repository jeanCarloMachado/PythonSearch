from search_run.cli import SearchAndRunCli
from fire import Fire


data = {"search browser": "https://google.com"}

instance = SearchAndRunCli(application_name="test", data=data)


Fire(instance)
