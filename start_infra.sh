#!/bin/bash

zookeeper-server-start /opt/homebrew/etc/kafka/zookeeper.properties &

kafka-server-start /opt/homebrew/etc/kafka/server.properties &

spark-submit \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
        $HOME/projects/PythonSearch/search_run/events/consumer.py consume_search_run_performed &

redis-server &

$HOME/projects/PythonSearch/search_run/events/latest_used_entries.py consume
