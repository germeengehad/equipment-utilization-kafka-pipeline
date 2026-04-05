from kafka import KafkaProducer
import json
import time
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "outputs", "logs", "tracking_payloads.jsonl")

KAFKA_TOPIC = "equipment_tracking_clean_v2"
KAFKA_SERVER = "127.0.0.1:9092"

# =========================
# Producer Setup
# =========================
producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# =========================
# Read JSONL file
# =========================
INPUT_FILE = "outputs/logs/tracking_payloads.jsonl"

def send_to_kafka():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            payload = json.loads(line.strip())

            producer.send(KAFKA_TOPIC, payload)

            print(f"Sent: {payload['track_id']} - {payload['state']}")

            # simulate real-time streaming
            time.sleep(0.05)

    producer.flush()
    print("All messages sent!")


if __name__ == "__main__":
    send_to_kafka()