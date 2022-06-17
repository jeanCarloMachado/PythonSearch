#!/usr/bin/env python3
import os


class StartSevices:
    def zookeeper(self):
        os.system('zookeeper-server-start /opt/homebrew/etc/kafka/zookeeper.properties &')

    def kafka(self):
        os.system('kafka-server-start /opt/homebrew/etc/kafka/server.properties &')

    def spark_consumer(self):
        os.system(''' spark-submit \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
        $HOME/projects/PythonSearch/search_run/events/consumer.py consume_search_run_performed &
                  ''')

    def redis(self):
        os.system('redis-server &')

    def consume_entries_redis(self):
        os.system('$HOME/projects/PythonSearch/search_run/events/latest_used_entries.py consume &')

    def all(self):
        import time;

        self.zookeeper()
        time.sleep(3)
        self.kafka()
        time.sleep(3)
        self.spark_consumer()
        time.sleep(3)
        self.redis()
        time.sleep(3)
        self.consume_entries_redis()
        time.sleep(3)

if __name__ == '__main__':
    import fire
    fire.Fire(StartSevices)


