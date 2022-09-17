#!/usr/bin/env python3
import os
from subprocess import Popen

from python_search.apps.notification_ui import send_notification


class Infrastructure:
    def __init__(self):
        self._RUNNING_INFO = {
            "web_api": {"cmd": "python_search_webapi", "log": "/tmp/log_webserver"},
            "reminders": {
                "cmd": "reminders run_daemon",
                "log": "/tmp/log_reminders",
            },
            "zookeeper": {
                "cmd": "zookeeper-server-start /opt/homebrew/etc/kafka/zookeeper.properties",
                "log": "/tmp/log_zoookeeper",
            },
            "kafka": {
                "cmd": "kafka-server-start /opt/homebrew/etc/kafka/server.properties",
                "log": "/tmp/log_kafka",
            },
            "redis": {
                "cmd": "cd /tmp ; redis-server /opt/homebrew/Cellar/redis/7.0.3/.bottle/etc/redis.conf",
                "log": "/tmp/log_redis",
            },
            "latest_redis_consumer": {
                "cmd": "/Users/jean.machado/projects/PythonSearch/python_search/events/latest_used_entries.py consume",
                "log": "/tmp/log_consumer_redis",
            },
            "spark_consumer": {
                "cmd": "sleep 12;  log_command.sh spark-submit \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
        $HOME/projects/PythonSearch/python_search/events/consumer.py consume_search_run_performed",
                "log": "/tmp/log_spark",
            },
        }

    def all(self):
        self.run_service("web_api", follow_logs=False)
        self.run_service("zookeeper", follow_logs=False)
        self.run_service("kafka", follow_logs=False)
        self.run_service("redis", follow_logs=False)
        self.run_service("spark_consumer", follow_logs=False)
        self.run_service("latest_redis_consumer", follow_logs=False)

        send_notification("Infra setup finished")

    def run_service(self, service_name, follow_logs=True):
        if not service_name in self._RUNNING_INFO:
            raise Exception("Could not find service: " + service_name)

        print("Starting service: " + service_name)
        cmd = f"LOG_FILE={self._RUNNING_INFO[service_name]['log']} log_command.sh {self._RUNNING_INFO[service_name]['cmd']}"

        self._RUNNING_INFO[service_name]["pid"] = self._run_pid(cmd)

        if follow_logs:
            self.follow_logs(service_name)
        return self.status()

    def _run_pid(self, cmd):
        p = Popen(cmd, shell=True)
        return p.pid

    def status(self, json=False):
        for name, data in self._RUNNING_INFO.items():
            self._RUNNING_INFO[name]["already_run"] = os.path.exists(data["log"])

        if json:
            import json

            return json.dumps(self._RUNNING_INFO)

        return self._RUNNING_INFO

    def status_window(self):
        from python_search.interpreter.cmd import CmdInterpreter

        os.system(f" echo '{self.status(json=True)}' > /tmp/infra_status")
        CmdInterpreter(
            {"cli_cmd": f"  cat /tmp/infra_status | jq . "}
        ).interpret_default()

    def follow_logs(self, service):
        from python_search.interpreter.cmd import CmdInterpreter

        CmdInterpreter(
            {"cli_cmd": f"tail +1f {self._RUNNING_INFO[service]['log']}"}
        ).interpret_default()


def main():
    import fire

    fire.Fire(Infrastructure)


if __name__ == "__main__":
    main()
