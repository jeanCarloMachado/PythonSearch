from __future__ import annotations

from python_search.events.run_performed import EntryExecuted


class LogRunPerformedClient:
    def __init__(self, configuration):
        self._configuration = configuration

    def send(self, data: EntryExecuted):
        if not self._configuration.collect_data:
            # print("Skip collecting run performed data as collect_data is disabled")
            return

        if not self._configuration.use_webservice:
            # print("Logging entry executed")
            RunPerformedWriter().write(data)
            return

        import requests

        try:
            result = requests.post(
                url="http://localhost:8000/log_run", json=data.__dict__
            )
            return result
        except BaseException as e:
            print(f"Logging results failed, reason: {e}")


class RunPerformedWriter:
    """
    Writes event
    """

    def write(self, event: EntryExecuted):
        import datetime

        event.timestamp = str(datetime.datetime.now(datetime.timezone.utc).timestamp())

        from python_search.data_collector import GenericDataCollector

        return GenericDataCollector().write(
            data=event.__dict__, table_name="searches_performed"
        )
