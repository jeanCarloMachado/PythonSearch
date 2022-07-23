#!/usr/bin/env python3
import os

from python_search.apps.notification_ui import send_notification


class StartSevices:
    def zookeeper(self):
        os.system(
            "LOG_FILE=/tmp/log_zoookeeper log_command.sh zookeeper-server-start /opt/homebrew/etc/kafka/zookeeper.properties &"
        )

    def kafka(self):
        os.system(
            "LOG_FILE=/tmp/log_kafka log_command.sh kafka-server-start /opt/homebrew/etc/kafka/server.properties &"
        )

    def spark_consumer(self):
        os.system(
            """ LOG_FILE=/tmp/log_spark log_command.sh spark-submit \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
        $HOME/projects/PythonSearch/python_search/events/consumer.py consume_search_run_performed &
                  """
        )

    def redis(self):
        os.system("LOG_FILE=/tmp/log_redis log_command.sh redis-server &")

    def consume_latest_entries_redis(self):
        os.system(
            "LOG_FILE=/tmp/log_consumer_redis log_command.sh $HOME/projects/PythonSearch/python_search/events/latest_used_entries.py consume &"
        )

    def api(self, background=False, print_only=False, kill=False):

        if kill:
            print("Killing web api first")
            os.system("pkill -f web_api.py")

        cmd = f"LOG_FILE=/tmp/log_webserver log_command.sh  python_search_webapi"

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
        time.sleep(6)
        self.consume_latest_entries_redis()
        self.api(background=True)

        time.sleep(5)
        send_notification("Infra setup finished")


def main():
    import fire

    fire.Fire(StartSevices)


if __name__ == "__main__":
    main()
