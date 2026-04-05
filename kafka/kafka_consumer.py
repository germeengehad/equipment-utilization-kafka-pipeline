from kafka import KafkaConsumer
import json

KAFKA_TOPIC = "equipment_tracking"
KAFKA_SERVER = "localhost:9092"

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_SERVER,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

print("Listening for messages...")

for message in consumer:
    payload = message.value
    print(payload)