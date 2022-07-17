#!/usr/bin/env python3
import os

from python_search.apps.notification_ui import send_notification


class StartSevices:
    def zookeeper(self):
        os.system(
            "zookeeper-server-start /opt/homebrew/etc/kafka/zookeeper.properties &"
        )

    def kafka(self):
        os.system("kafka-server-start /opt/homebrew/etc/kafka/server.properties &")

    def spark_consumer(self):
        os.system(
            """ spark-submit \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
        $HOME/projects/PythonSearch/python_search/events/consumer.py consume_search_run_performed &
                  """
        )

    def redis(self):
        os.system("redis-server &")

    def consume_latest_entries_redis(self):
        os.system(
            "$HOME/projects/PythonSearch/python_search/events/latest_used_entries.py consume &"
        )

    def api(self, background=False, print_only=False, kill=False):

        if kill:
            print("Killing web api first")
            os.system("pkill -f web_api.py")

        HOME = os.getenv("HOME")
        cmd = f"conda run --no-capture-output  -n base python {HOME}/projects/PythonSearch/python_search/web_api.py"

        if print_only:
            print(cmd)
            return

        return self._run(cmd, background)

    def _run(self, cmd: str, background=False):
        if background:
            print("Background enabled")
            cmd = "nohup " + cmd + " & "

        os.system(cmd)

    def all(self):
        import time

        self.zookeeper()
        time.sleep(15)
        self.kafka()
        time.sleep(3)
        self.spark_consumer()
        time.sleep(3)
        self.redis()
        time.sleep(3)
        self.consume_latest_entries_redis()
        time.sleep(3)
        self.api(background=True)

        time.sleep(5)
        send_notification("Infra setup finished")


if __name__ == "__main__":
    import fire

    fire.Fire(StartSevices)
