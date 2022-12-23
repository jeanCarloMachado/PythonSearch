from __future__ import annotations

from python_search.events.run_performed import RunPerformed


class LogRunPerformedClient:
    def send(self, data: RunPerformed):
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

    def write(self, event: RunPerformed):
        import datetime

        event.timestamp = str(datetime.datetime.now(datetime.timezone.utc).timestamp())

        from python_search.data_collector import GenericDataCollector
        return GenericDataCollector().write(
            data=event.__dict__, table_name="searches_performed"
        )
