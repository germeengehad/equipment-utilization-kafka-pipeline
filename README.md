# 🏭 Equipment Utilization Kafka Pipeline

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Apache_Kafka-2.8+-231F20?style=for-the-badge&logo=apache-kafka" />
  <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-FF6F00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql" />
  <img src="https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker" />
</p>

> A real-time computer vision pipeline that uses **YOLOv8** object detection to monitor equipment activity from video footage, streams events through **Apache Kafka**, persists tracking data to **PostgreSQL**, and visualizes utilization metrics on a live **Streamlit** dashboard — all orchestrated with **Docker Compose**.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Environment Setup](#-environment-setup)
- [Running the Pipeline](#-running-the-pipeline)
- [Dashboard](#-dashboard)
- [Pipeline Flow](#-pipeline-flow)
- [Configuration Reference](#-configuration-reference)
- [Troubleshooting](#-troubleshooting)

---

## 🔍 Overview

This project implements an **end-to-end real-time data engineering pipeline** for tracking and analyzing equipment utilization in industrial or warehouse video feeds. The core idea is:

1. A **Vision Service** processes video frames using YOLOv8 to detect and track equipment objects, logging detection payloads.
2. A **Kafka Producer** streams those detection events to a Kafka topic.
3. A **Kafka Consumer** reads from the topic and writes records to PostgreSQL.
4. A **Streamlit Dashboard** connects to PostgreSQL and displays live utilization metrics and annotated video output.

This covers the full lifecycle: **ingestion → streaming → storage → visualization**.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Docker Network                              │
│                                                                     │
│  ┌──────────────┐    JSONL     ┌──────────────────┐                 │
│  │              │─────────────▶│                  │                 │
│  │ Vision       │  (file vol)  │  Kafka Producer  │                 │
│  │ Service      │              │                  │                 │
│  │ (YOLOv8)     │              └────────┬─────────┘                 │
│  │              │                       │  Kafka Topic              │
│  │  MP4 Video   │               ┌───────▼──────────┐                │
│  │     ↓        │               │   Apache Kafka   │                │
│  │  Detection   │               │   + Zookeeper    │                │
│  │  & Tracking  │               └───────┬──────────┘                │
│  └──────────────┘                       │                           │
│                               ┌─────────▼──────────┐               │
│                               │  Kafka Consumer DB  │               │
│                               │  (kafka_to_postgres)│               │
│                               └─────────┬──────────┘               │
│                                         │                           │
│                               ┌─────────▼──────────┐               │
│                               │    PostgreSQL 15    │               │
│                               └─────────┬──────────┘               │
│                                         │                           │
│                               ┌─────────▼──────────┐               │
│                               │  Streamlit Dashboard│  :8501        │
│                               └────────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
equipment-utilization-kafka-pipeline/
│
├── vision_service/             # YOLOv8 object detection & tracking
│   ├── Dockerfile
│   └── main.py                 # Processes video, writes tracking_payloads.jsonl
│
├── kafka/                      # Kafka producer & consumer
│   ├── Dockerfile
│   ├── kafka_producer.py       # Reads JSONL, publishes to Kafka topic
│   └── kafka_to_postgres.py    # Consumes Kafka topic, writes to PostgreSQL
│
├── dashbord/                   # Streamlit dashboard
│   ├── Dockerfile
│   └── dashbord_app.py         # Reads from PostgreSQL, renders metrics + video
│
├── streamlit/                  # (Streamlit config / assets)
│
├── data/
│   └── raw/                    # 📥 Place your input video here (your_video.mp4)
│
├── outputs/
│   ├── logs/                   # tracking_payloads.jsonl (generated)
│   └── videos/                 # Annotated output video (generated)
│
├── static/                     # Static assets
│
├── yolov8n.pt                  # YOLOv8 nano model weights
├── docker-compose.yml          # Full stack orchestration
├── requirements.txt            # Python dependencies
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Object Detection | [YOLOv8 (Ultralytics)](https://github.com/ultralytics/ultralytics) |
| Video Processing | OpenCV (`opencv-python-headless`) |
| Message Broker | Apache Kafka 7.5.0 (Confluent) + Zookeeper |
| Database | PostgreSQL 15 |
| Dashboard | Streamlit |
| Data Processing | Pandas, NumPy |
| Containerization | Docker & Docker Compose |
| Language | Python 3.10+ |

---

## ✅ Prerequisites

Before running the project, make sure you have:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24+ recommended) with Docker Compose v2
- At least **8 GB RAM** allocated to Docker (YOLOv8 + Kafka + PostgreSQL are memory-intensive)
- A valid **MP4 video file** of the equipment/scene you want to analyze
- Git

---

## ⚙️ Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/germeengehad/equipment-utilization-kafka-pipeline.git
cd equipment-utilization-kafka-pipeline
```

### 2. Add Your Input Video

Place your video file in the `data/raw/` directory and name it `your_video.mp4`:

```bash
cp /path/to/your/video.mp4 data/raw/your_video.mp4
```

### 3. Create the `.env` File

Create a `.env` file in the project root with the following variables:

```env
# Kafka
KAFKA_TOPIC=equipment_tracking

# PostgreSQL
POSTGRES_DB=equipment_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

---

## 🚀 Running the Pipeline

### Start All Services

```bash
docker-compose up --build
```

This will spin up all 6 services in the correct order:

1. `zookeeper` → Kafka coordination
2. `kafka` → Message broker
3. `postgres` → Database
4. `vision_service` → Runs YOLOv8 on your video, produces `tracking_payloads.jsonl`
5. `kafka_producer` → Reads JSONL and publishes to the Kafka topic
6. `kafka_consumer_db` → Consumes from Kafka and persists to PostgreSQL
7. `dashboard` → Serves the Streamlit app on port `8501`

### View the Dashboard

Once all services are running, open your browser at:

```
http://localhost:8501
```

### Stop the Pipeline

```bash
docker-compose down
```

To also remove the PostgreSQL data volume:

```bash
docker-compose down -v
```

---

## 🎥 Demo

<p align="center">
  <img src="https://raw.githubusercontent.com/germeengehad/equipment-utilization-kafka-pipeline/main/dashboard.png" width="900"/>
</p>

## 📊 Dashboard

The Streamlit dashboard (`dashbord/dashbord_app.py`) connects to PostgreSQL and displays:

- **Equipment utilization metrics** — active vs. idle time per object/equipment class
- **Detection timeline** — frame-by-frame tracking activity
- **Annotated output video** — the processed video with bounding boxes overlaid (`outputs/videos/state_activity_output_h264.mp4`)

The dashboard is accessible at **`http://localhost:8501`** and auto-refreshes as new data flows in.

---

## 🔄 Pipeline Flow

```
[Input Video]
     │
     ▼
[vision_service/main.py]
  - Loads yolov8n.pt model
  - Processes each frame with YOLOv8
  - Tracks object IDs across frames
  - Classifies equipment state (active/idle)
  - Writes annotated video to outputs/videos/
  - Writes detection events to outputs/logs/tracking_payloads.jsonl
     │
     ▼  (shared volume)
[kafka/kafka_producer.py]
  - Reads tracking_payloads.jsonl line by line
  - Serializes each record as JSON
  - Publishes to Kafka topic: $KAFKA_TOPIC
     │
     ▼  (Kafka broker)
[kafka/kafka_to_postgres.py]
  - Subscribes to $KAFKA_TOPIC
  - Deserializes JSON messages
  - Inserts records into PostgreSQL table
     │
     ▼  (PostgreSQL)
[dashbord/dashbord_app.py]
  - Queries PostgreSQL for utilization data
  - Renders metrics, charts, and annotated video
  - Served via Streamlit on port 8501
```

---

## 🔧 Configuration Reference

All service configurations are managed through environment variables in `.env` and `docker-compose.yml`.

| Variable | Service | Description | Default |
|----------|---------|-------------|---------|
| `KAFKA_TOPIC` | All | Kafka topic name | `equipment_tracking` |
| `KAFKA_BOOTSTRAP_SERVERS` | Producer/Consumer | Kafka broker address | `kafka:9092` |
| `POSTGRES_DB` | PostgreSQL / Consumer / Dashboard | Database name | — |
| `POSTGRES_USER` | PostgreSQL / Consumer / Dashboard | DB username | — |
| `POSTGRES_PASSWORD` | PostgreSQL / Consumer / Dashboard | DB password | — |
| `POSTGRES_HOST` | Consumer / Dashboard | DB host | `postgres` |
| `POSTGRES_PORT` | Consumer / Dashboard | DB port | `5432` |
| `INPUT_VIDEO` | vision_service | Path to input video | `/app/data/raw/your_video.mp4` |
| `YOLO_MODEL_PATH` | vision_service | Path to YOLO weights | `/app/yolov8n.pt` |
| `SHOW_WINDOW` | vision_service | Show OpenCV window | `false` |

---

## 🧩 Troubleshooting

**`vision_service` exits immediately**
- Ensure `data/raw/your_video.mp4` exists and is a valid video file.
- Check that `yolov8n.pt` is present in the project root.

**Kafka producer/consumer can't connect**
- The producer and consumer have a `sleep 10` delay to wait for Kafka to be ready. If Kafka is slow to start, try increasing the sleep value in `docker-compose.yml`.

**Dashboard shows no data**
- Confirm the vision service has finished and `outputs/logs/tracking_payloads.jsonl` has been generated.
- Check that the producer and consumer both ran successfully: `docker-compose logs kafka_producer` and `docker-compose logs kafka_consumer_db`.

**Port 8501 already in use**
- Change the host port mapping in `docker-compose.yml`: `"8502:8501"` and access via `http://localhost:8502`.

**PostgreSQL connection refused**
- Verify your `.env` credentials match the running PostgreSQL container.

---

## 📦 Python Dependencies

```
ultralytics          # YOLOv8 model
opencv-python-headless  # Video frame processing (no GUI)
numpy                # Numerical operations
pandas               # Data manipulation
streamlit            # Dashboard UI
psycopg2-binary      # PostgreSQL adapter
kafka-python         # Kafka producer & consumer
python-dotenv        # .env file loading
```

---

## 📄 License

This project was created as an academic assignment. Feel free to use and adapt it for learning purposes.

---

<p align="center">Built with ❤️ using YOLOv8 · Apache Kafka · PostgreSQL · Streamlit · Docker</p>
