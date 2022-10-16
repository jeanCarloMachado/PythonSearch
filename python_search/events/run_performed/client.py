from __future__ import annotations

from python_search.events.run_performed import RunPerformed


class LogRunPerformedClient:
    def send(self, data: RunPerformed):
        import requests

        try:
            return requests.post(
                url="http://localhost:8000/log_run", json=data.__dict__
            )
        except BaseException as e:
            print(f"Logging results failed, reason: {e}")
