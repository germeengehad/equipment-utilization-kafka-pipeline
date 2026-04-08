import os
import json
import time
from kafka import KafkaConsumer
import psycopg2

# =========================
# Kafka Config
# =========================
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "equipment_tracking_clean_v2")

# =========================
# PostgreSQL Config
# =========================
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "equipment_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "1234")


def create_table(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment_tracking (
        id SERIAL PRIMARY KEY,
        frame_id INT,
        timestamp FLOAT,
        equipment_id TEXT,
        track_id INT,
        equipment_class TEXT,
        equipment_class_raw TEXT,
        bbox_x1 INT,
        bbox_y1 INT,
        bbox_x2 INT,
        bbox_y2 INT,
        current_state TEXT,
        current_activity TEXT,
        motion_source TEXT,
        current_idle_session_seconds FLOAT,
        total_tracked_seconds FLOAT,
        total_active_seconds FLOAT,
        total_idle_seconds FLOAT,
        utilization_percent FLOAT,
        full_motion FLOAT,
        arm_motion FLOAT,
        truck_base_motion FLOAT
    );
    """)


def insert_record(cursor, payload):
    bbox = payload.get("bbox", {})
    utilization = payload.get("utilization", {})
    time_analytics = payload.get("time_analytics", {})
    motion_metrics = payload.get("motion_metrics", {})

    cursor.execute("""
    INSERT INTO equipment_tracking (
        frame_id,
        timestamp,
        equipment_id,
        track_id,
        equipment_class,
        equipment_class_raw,
        bbox_x1,
        bbox_y1,
        bbox_x2,
        bbox_y2,
        current_state,
        current_activity,
        motion_source,
        current_idle_session_seconds,
        total_tracked_seconds,
        total_active_seconds,
        total_idle_seconds,
        utilization_percent,
        full_motion,
        arm_motion,
        truck_base_motion
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        payload.get("frame_id"),
        payload.get("timestamp"),
        payload.get("equipment_id"),
        payload.get("track_id"),
        payload.get("equipment_class"),
        payload.get("equipment_class_raw"),
        bbox.get("x1"),
        bbox.get("y1"),
        bbox.get("x2"),
        bbox.get("y2"),
        utilization.get("current_state"),
        utilization.get("current_activity"),
        utilization.get("motion_source"),
        time_analytics.get("current_idle_session_seconds"),
        time_analytics.get("total_tracked_seconds"),
        time_analytics.get("total_active_seconds"),
        time_analytics.get("total_idle_seconds"),
        time_analytics.get("utilization_percent"),
        motion_metrics.get("full_motion"),
        motion_metrics.get("arm_motion"),
        motion_metrics.get("truck_base_motion"),
    ))


def create_consumer():
    while True:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode("utf-8"))
            )
            print(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
            return consumer
        except Exception as e:
            print(f"Kafka not ready yet: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)


def main():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()

    create_table(cursor)
    print("PostgreSQL table is ready.")

    consumer = create_consumer()

    print(f"Listening to Kafka topic '{KAFKA_TOPIC}' and writing to PostgreSQL...")

    for message in consumer:
        payload = message.value
        insert_record(cursor, payload)

        utilization = payload.get("utilization", {})

        print(
            f"Inserted equipment_id={payload.get('equipment_id')} "
            f"track_id={payload.get('track_id')} "
            f"state={utilization.get('current_state')} "
            f"activity={utilization.get('current_activity')}"
        )


if __name__ == "__main__":
    main()