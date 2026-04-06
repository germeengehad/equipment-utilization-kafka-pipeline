# from kafka import KafkaProducer
# import json
# import time
# import os

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# INPUT_FILE = os.path.join(BASE_DIR, "outputs", "logs", "tracking_payloads.jsonl")

# KAFKA_TOPIC = "equipment_tracking_clean_v2"
# KAFKA_SERVER = "127.0.0.1:9092"

# # =========================
# # Producer Setup
# # =========================
# producer = KafkaProducer(
#     bootstrap_servers=KAFKA_SERVER,
#     value_serializer=lambda v: json.dumps(v).encode("utf-8")
# )

# # =========================
# # Read JSONL file
# # =========================
# INPUT_FILE = "outputs/logs/tracking_payloads.jsonl"

# def send_to_kafka():
#     with open(INPUT_FILE, "r", encoding="utf-8") as f:
#         for line in f:
#             payload = json.loads(line.strip())

#             producer.send(KAFKA_TOPIC, payload)

#             print(f"Sent: {payload['track_id']} - {payload['state']}")

#             # simulate real-time streaming
#             time.sleep(0.05)

#     producer.flush()
#     print("All messages sent!")


# if __name__ == "__main__":
#     send_to_kafka()

import os
import json
import time
from kafka import KafkaProducer

# =========================
# Paths
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.getenv(
    "INPUT_FILE",
    os.path.join(BASE_DIR, "outputs", "logs", "tracking_payloads.jsonl")
)

# =========================
# Kafka Config
# =========================
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "equipment_tracking_clean_v2")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def wait_for_input_file():
    while not os.path.exists(INPUT_FILE):
        print(f"Waiting for input file: {INPUT_FILE}")
        time.sleep(2)


def create_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            print(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
            return producer
        except Exception as e:
            print(f"Kafka not ready yet: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)


def send_to_kafka():
    wait_for_input_file()
    producer = create_producer()

    print(f"Reading from: {INPUT_FILE}")
    print(f"Sending to Kafka topic '{KAFKA_TOPIC}' at {KAFKA_BOOTSTRAP_SERVERS}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            payload = json.loads(line.strip())
            producer.send(KAFKA_TOPIC, payload)

            print(
                f"Sent machine_id={payload.get('machine_id')} "
                f"track_id={payload.get('track_id')} "
                f"state={payload.get('state')}"
            )

            time.sleep(0.05)

    producer.flush()
    print("All messages sent!")


if __name__ == "__main__":
    send_to_kafka()