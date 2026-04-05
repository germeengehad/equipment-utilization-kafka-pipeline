from kafka import KafkaConsumer
import psycopg2
import json

# =========================
# Kafka Config
# =========================
KAFKA_TOPIC = "equipment_tracking_clean_v2"
KAFKA_SERVER = "127.0.0.1:9092"

# =========================
# PostgreSQL Config
# =========================
DB_HOST = "127.0.0.1"
DB_PORT = 5544
DB_NAME = "equipment_db"
DB_USER = "postgres"
DB_PASSWORD = "1234"


def create_table(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment_tracking (
        id SERIAL PRIMARY KEY,
        frame_index INT,
        timestamp_sec FLOAT,
        machine_id TEXT,
        track_id INT,
        equipment_class TEXT,
        bbox_x1 INT,
        bbox_y1 INT,
        bbox_x2 INT,
        bbox_y2 INT,
        state TEXT,
        activity TEXT,
        current_idle_session_sec FLOAT,
        total_idle_sec FLOAT,
        total_active_sec FLOAT,
        utilization_percent FLOAT,
        full_motion FLOAT,
        arm_motion FLOAT,
        truck_base_motion FLOAT
    );
    """)


def insert_record(cursor, payload):
    bbox = payload.get("bbox", {})

    cursor.execute("""
    INSERT INTO equipment_tracking (
        frame_index,
        timestamp_sec,
        machine_id,
        track_id,
        equipment_class,
        bbox_x1,
        bbox_y1,
        bbox_x2,
        bbox_y2,
        state,
        activity,
        current_idle_session_sec,
        total_idle_sec,
        total_active_sec,
        utilization_percent,
        full_motion,
        arm_motion,
        truck_base_motion
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        payload.get("frame_index"),
        payload.get("timestamp_sec"),
        payload.get("machine_id"),
        payload.get("track_id"),
        payload.get("equipment_class"),
        bbox.get("x1"),
        bbox.get("y1"),
        bbox.get("x2"),
        bbox.get("y2"),
        payload.get("state"),
        payload.get("activity"),
        payload.get("current_idle_session_sec"),
        payload.get("total_idle_sec"),
        payload.get("total_active_sec"),
        payload.get("utilization_percent"),
        payload.get("full_motion"),
        payload.get("arm_motion"),
        payload.get("truck_base_motion"),
    ))


def main():
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()

    create_table(cursor)
    print("PostgreSQL table is ready.")

    # Connect to Kafka
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )

    print("Listening to Kafka and writing to PostgreSQL...")

    for message in consumer:
        payload = message.value
        insert_record(cursor, payload)
        print(
            f"Inserted machine_id={payload.get('machine_id')} "
            f"track_id={payload.get('track_id')} "
            f"state={payload.get('state')} "
            f"activity={payload.get('activity')}"
        )


if __name__ == "__main__":
    main()