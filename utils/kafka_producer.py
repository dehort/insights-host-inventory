import json
import os
import time
from threading import Thread

import payloads
from kafka import KafkaConsumer
from kafka import KafkaProducer

# import logging

# logging.basicConfig(level=logging.INFO)

INGRESS_TOPIC = os.environ.get("INGRESS_KAFKA_TOPIC", "platform.inventory.host-ingress")
BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")

start = None
expected_number_of_messages = 10000


def consumer_thread():
    global start
    EGRESS_TOPIC = os.environ.get("EGRESS_KAFKA_TOPIC", "platform.inventory.host-egress")
    EGRESS_KAFKA_GROUP = "inventory-mq"

    print("EGRESS_TOPIC:", EGRESS_TOPIC)
    print("EGRESS_KAFKA_GROUP:", EGRESS_KAFKA_GROUP)
    print("BOOTSTRAP_SERVERS:", BOOTSTRAP_SERVERS)

    consumer = KafkaConsumer(EGRESS_TOPIC, group_id=EGRESS_KAFKA_GROUP, bootstrap_servers=BOOTSTRAP_SERVERS)

    msg_count = 0

    print("consumer waiting on messages")
    for msg in consumer:
        msg_count += 1
        # print("inside msg_handler()")
        # print("type(parsed):", type(parsed))
        # print("parsed:", parsed)

        if msg_count == expected_number_of_messages:
            print("Got 'em all ... done")
            break

    end = time.time()
    print("Time to receive all hosts: ", end - start)


# Start consumer thread
t = Thread(target=consumer_thread, daemon=True)
t.start()


def generate_payloads(number_of_hosts):
    payload_type = "default"
    metadata_dict = {}
    for _ in range(number_of_hosts):
        yield str.encode(
            json.dumps(
                {
                    "operation": "add_host",
                    "platform_metadata": metadata_dict,
                    "data": payloads.build_data(payload_type),
                }
            )
        )


producer = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS, api_version=(0, 10))
print("INGRESS_TOPIC:", INGRESS_TOPIC)

start = time.time()
for payload in generate_payloads(expected_number_of_messages):
    producer.send(INGRESS_TOPIC, value=payload)
end = time.time()
print("Time to send all hosts to queue: ", end - start)

print("Sleeping")
time.sleep(2)
print("Waiting on consumer thread")
t.join()
print("consumer thread is done")
