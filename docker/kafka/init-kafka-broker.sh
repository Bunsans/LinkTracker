#!/bin/sh

mkdir -p /etc/kafka/secrets \
&& cp /kafka_server_jaas.conf /etc/kafka/secrets/ \
&& sed -i "s/\${TEST_KAFKA_PASS}/$TEST_KAFKA_PASS/g" /etc/kafka/secrets/kafka_server_jaas.conf \
&& sed -i "s/\${TEST_KAFKA_USER}/$TEST_KAFKA_USER/g" /etc/kafka/secrets/kafka_server_jaas.conf \

/etc/confluent/docker/run &

echo "Waiting for Kafka to be ready..."
cub kafka-ready -b broker1:29092 1 30

kafka-topics --create \
  --bootstrap-server broker1:29092 \
  --topic schedule_send_updates \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists

kafka-topics --create \
  --bootstrap-server broker1:29092 \
  --topic schedule_send_updates.DLQ \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists

wait
