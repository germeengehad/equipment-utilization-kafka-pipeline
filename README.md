# 🏭 Equipment Utilization Kafka Pipeline

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Apache_Kafka-7.5.0-231F20?style=for-the-badge&logo=apache-kafka" />
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
- [Technical Write-Up](#-technical-write-up)
- [Trade-offs & Design Decisions](#-trade-offs--design-decisions)
- [Configuration Reference](#-configuration-reference)
- [Troubleshooting](#-troubleshooting)
- [Python Dependencies](#-python-dependencies)

---

## 🔍 Overview

This project implements an **end-to-end real-time data engineering pipeline** for tracking and analyzing heavy-equipment utilization in construction or industrial video feeds. The system answers a single operational question: *Is this machine actively working — and if so, what is it doing?*

The pipeline is designed around four guiding principles:

- **Articulated-motion awareness** — excavators move only their arm during many productive activities; the system must not classify these moments as idle
- **Stable identity across frames** — YOLO track IDs reset on occlusion; a Re-ID layer maintains consistent equipment IDs for analytics
- **Streaming-first architecture** — every detection event flows through Kafka so downstream consumers can be added without modifying the vision layer
- **Containerised simplicity** — a single `docker-compose up --build` starts every service in the correct dependency order

The full lifecycle is covered: **Ingestion → Streaming → Storage → Visualization**

---

## 🏗️ Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Docker Network                              │
│                                                                     │
│  ┌──────────────┐    JSONL     ┌──────────────────┐                 │
│  │              │─────────────▶│                  │                 │
│  │ vision_      │  (file vol)  │  kafka_producer  │                 │
│  │ service      │              │                  │                 │
│  │ (YOLOv8)     │              └────────┬─────────┘                 │
│  │              │                       │  Kafka Topic              │
│  │  MP4 Video   │               ┌───────▼──────────┐               │
│  │     ↓        │               │   Apache Kafka   │               │
│  │  Detection   │               │   + Zookeeper    │               │
│  │  & Tracking  │               └───────┬──────────┘               │
│  └──────────────┘                       │                           │
│                               ┌─────────▼──────────┐               │
│                               │  kafka_consumer_db  │               │
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

### Service Responsibilities

| Service | Language / Image | Responsibility |
|---|---|---|
| `vision_service` | Python 3.10 + YOLOv8 | Frame-by-frame detection, tracking, motion analysis, JSONL output |
| `kafka_producer` | Python 3.10 + kafka-python | Tails JSONL file, serialises payloads, publishes to Kafka topic |
| `zookeeper` | Confluent 7.5.0 | Kafka cluster coordination |
| `kafka` | Confluent 7.5.0 | Distributed message broker |
| `kafka_consumer_db` | Python 3.10 + psycopg2 | Subscribes to topic, upserts rows into PostgreSQL |
| `dashboard` | Python 3.10 + Streamlit | Live metrics, charts, and annotated video on port 8501 |

### End-to-End Data Flow

```
[Input Video]
     │
     ▼
[vision_service/main.py]
  - Loads yolov8n.pt model
  - Processes each frame with YOLOv8 + ByteTrack
  - Computes region-split optical flow per bounding box
  - Classifies state (ACTIVE / INACTIVE) and activity
  - Writes annotated video → outputs/videos/
  - Writes detection events → outputs/logs/tracking_payloads.jsonl
     │
     ▼  (shared Docker volume)
[kafka/kafka_producer.py]
  - Tails tracking_payloads.jsonl line by line
  - Serialises each record as JSON
  - Publishes to Kafka topic: $KAFKA_TOPIC
     │
     ▼  (Kafka broker)
[kafka/kafka_to_postgres.py]
  - Subscribes to $KAFKA_TOPIC
  - Deserialises JSON messages
  - Inserts / upserts records into PostgreSQL
     │
     ▼  (PostgreSQL)
[dashboard/dashboard_app.py]
  - Queries PostgreSQL for utilization data
  - Renders metrics, charts, and annotated video
  - Served via Streamlit on port 8501
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
├── dashboard/                   # Streamlit dashboard
│   ├── Dockerfile
│   └── dashboard_app.py         # Reads from PostgreSQL, renders metrics + video
│
├── data/
│   └── raw/                    # 📥 Place your input video here: your_video.mp4
│
├── outputs/
│   ├── logs/                   # tracking_payloads.jsonl  (auto-generated)
│   └── videos/                 # Annotated output video   (auto-generated)
│
├── yolov8n.pt                  # YOLOv8 nano model weights
├── docker-compose.yml          # Full stack orchestration
├── requirements.txt            # Python dependencies
├── .env                        # ⚠️ Not committed — see Environment Setup
└── README.md
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Object Detection | YOLOv8 nano (Ultralytics) |
| Multi-Object Tracking | ByteTrack (built into Ultralytics) |
| Motion Analysis | OpenCV Farneback Dense Optical Flow |
| Message Broker | Apache Kafka 7.5.0 (Confluent) + Zookeeper |
| Database | PostgreSQL 15 |
| Dashboard | Streamlit |
| Data Processing | Pandas, NumPy |
| Containerization | Docker & Docker Compose v2 |
| Language | Python 3.10+ |

---

## ✅ Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker Desktop | v24+ | Docker Compose v2 required |
| RAM allocated to Docker | 8 GB minimum | YOLOv8 + Kafka + PostgreSQL are memory-intensive |
| Input video | MP4 | Place at `data/raw/your_video.mp4` |
| YOLOv8 weights | yolov8n.pt | Pre-place in project root, or Ultralytics downloads on first run |

---

## ⚙️ Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/germeengehad/equipment-utilization-kafka-pipeline.git
cd equipment-utilization-kafka-pipeline
```

### 2. Add Your Input Video

```bash
cp /path/to/your/video.mp4 data/raw/your_video.mp4
```

### 3. Create the `.env` File

```env
# Kafka
KAFKA_TOPIC=equipment_tracking_clean_v2

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

Docker Compose starts services in dependency order:

1. `zookeeper` — Kafka coordination
2. `kafka` — Message broker
3. `postgres` — Database
4. `vision_service` — Runs YOLOv8 on your video; produces `tracking_payloads.jsonl`
5. `kafka_producer` — Reads JSONL and publishes to the Kafka topic
6. `kafka_consumer_db` — Consumes from Kafka and persists to PostgreSQL
7. `dashboard` — Serves the Streamlit app on port `8501`

> The `vision_service` processes the video and writes results to JSONL, which are then streamed to Kafka to simulate real-time processing.

### View the Dashboard

```
http://localhost:8501
```

### Stop the Pipeline

```bash
docker-compose down          # stop containers, keep volumes
docker-compose down -v       # stop containers AND delete PostgreSQL data
```

---

## 📊 Dashboard

The Streamlit dashboard connects to PostgreSQL and displays:

- **Equipment utilization metrics** — active vs. idle time per machine, with live utilization percentages
- **Detection timeline** — frame-by-frame state and activity tracking
- **Annotated output video** — processed video with bounding boxes, state labels, and utilization overlaid

The dashboard auto-refreshes as new data flows in from the Kafka consumer.

---

## 🎥 Demo Video

👉 [Watch Demo Video](https://drive.google.com/file/d/1vtVit6ekPlSLE0pXmNBXy94l2MIVi6Eb/view?usp=sharing)

This demo demonstrates:

- Real-time video processing with bounding boxes
- Machine state updates (ACTIVE / INACTIVE)
- Activity classification (Digging, Dumping, Loading)
- Kafka streaming pipeline
- Live dashboard updating utilization metrics

---

The system processes video frame-by-frame and updates analytics in near real-time.

## 🧠 Technical Write-Up

This section details the key design decisions and trade-offs in the computer vision and data pipeline layers.

### The Core Challenge: Articulated Equipment Motion

Standard motion detection treats a bounding box as a single unit — if the box as a whole doesn't move, the machine is idle. **This breaks for excavators.**

An excavator in productive operation routinely keeps its undercarriage and cab stationary while the arm swings, digs, or dumps. A naive whole-box optical-flow score averages the energetic arm movement with the static body, producing a low mean that falsely classifies the machine as `INACTIVE`. This can cause utilization underestimates of 30–50% on typical excavation footage.

#### Solution: Region-Split Optical Flow

For each detected bounding box, three Farneback optical-flow scores are computed on grayscale ROI crops:

| Region | Sub-Crop of Bounding Box | Purpose |
|---|---|---|
| Full machine | Entire bounding box | Overall translational motion (travel, tramming) |
| Arm / boom region | Top-right 55% × 65% of box | Isolated arm and bucket movement for excavators |
| Truck base region | Central-lower 60% × 45% of box | Wheel and chassis motion for dump trucks |

The **effective motion score** used for state classification is then computed per equipment type:

```python
# Excavator: arm motion amplified 3.5× before comparison with full-body motion
effective_motion = max(full_motion, arm_motion * 3.5)

# Dump truck: only the base region is used
effective_motion = truck_base_motion
```

The 3.5× arm amplifier ensures that small but real arm movement (`arm_motion ≈ 0.05`) exceeds the excavator activity threshold (`0.15`), while ambient camera shake (`arm_motion ≈ 0.01`) does not. State flips are further stabilised by requiring **4 consecutive below-threshold frames** (`INACTIVE_MIN_FRAMES = 4`) before transitioning to `INACTIVE`.

**Trade-offs:**
- Optical flow is CPU-intensive. The current implementation processes video offline, so real-time throughput is not required.
- The arm sub-crop is a heuristic tuned to a specific camera angle. A different viewpoint would require re-tuning the region coordinates.
- Farneback dense flow is more robust than frame differencing on texture-poor metal surfaces, but slower than sparse Lucas-Kanade flow.

---

### Activity Classification

Once state is established, a deterministic rule-based classifier maps motion scores to a human-readable activity label. Rules are interpretable, which makes them easy for domain experts to audit and adjust without retraining a model.

#### Excavator Activities

| Activity | Condition | Rationale |
|---|---|---|
| `WAITING` | `state == INACTIVE` | Machine is stationary; no productive work |
| `DUMPING` | `arm_motion >= 0.25` AND `full_motion <= 0.35` | High arm motion + low body motion = dump cycle |
| `DIGGING` | `arm_motion >= 0.10` | Moderate arm motion = bucket cutting into material |
| `LOADING` | `full_motion >= 0.25` | High whole-body motion = swinging material to truck |
| `SWINGING` | Active fallback | Machine is on but no distinctive motion pattern |

The `DUMPING` condition uses a **compound gate** (high arm + low full body) rather than arm alone, because during `SWINGING` the full body also moves as the cab rotates. This reduces false `DUMPING` labels without requiring a second model.

#### Dump Truck Activities

| Activity | Condition | Rationale |
|---|---|---|
| `WAITING` | `state == INACTIVE` OR `base_motion < 0.90` | Not actively receiving material |
| `LOADING` | `truck_base_motion >= 0.90` | High base motion signals material impact / chassis bounce |

**Trade-off:** Rule thresholds are calibrated to the demo clip. A production deployment would require per-site calibration runs, or replacement of the rules with a small supervised classifier trained on labelled segments.

---

### Stable Machine Identity (Re-ID)

YOLO ByteTrack assigns new track IDs after occlusions or detection gaps. For utilization analytics, a machine that disappears behind a truck for five frames must resume accumulating time under the **same machine ID**.

The Re-ID layer matches incoming detections to a `machine_memory` dictionary using a scored combination of:

- **IoU** between current and last known bounding box (minimum 0.25)
- **Euclidean centre distance** (maximum 85 px)
- **Per-axis shift limits** (x < 70 px, y < 60 px) to reject implausible jumps
- **Area ratio** (0.70 – 1.40) to reject scale changes caused by partial detections
- **Spatial zone** (left / right half of frame) to prevent cross-side ID swaps

`MAX_MACHINE_IDS_PER_TYPE` caps the number of IDs per class (1 excavator + 1 truck for the demo clip). When the cap is reached, new detections fall back to the nearest existing ID in the same zone rather than spawning a new ID. This prevents ID proliferation from partial or flickering detections.

**Trade-off:** The zone-based cap works well for fixed-camera scenes with few machines. Multi-machine sites require raising `MAX_MACHINE_IDS_PER_TYPE` and tightening Re-ID distance thresholds.

---

### Kafka as the Integration Bus

The vision service writes detections to a **JSONL file** rather than pushing directly to Kafka. The Kafka producer tails this file and publishes each line as a message.

This decoupling provides two benefits:
- **Resilience:** if Kafka is temporarily unavailable, the JSONL file accumulates events. The producer replays them on reconnect.
- **Debuggability:** the JSONL file is a complete audit log that can be replayed into any downstream system without re-running inference.

**Trade-off:** File-based handoff introduces a small lag (one write-read cycle per event). For a live-camera deployment requiring sub-second latency, the vision service should publish directly to Kafka, with the JSONL file written as a secondary side-effect.

---

### Utilization Calculation

Utilization is computed incrementally per frame using wall-clock frame time (`1 / fps` seconds):

```python
active_time += frame_time    # if state == ACTIVE
idle_time   += frame_time    # if state == INACTIVE

utilization_pct = (active_time / (active_time + idle_time)) * 100
```

Each payload also carries `current_idle_session_seconds`, which resets to zero whenever the machine transitions to `ACTIVE`. This enables dashboard alerts when a machine has been continuously idle beyond a configurable threshold.

---

### Technology Choices

| Decision | Chosen Approach | Alternative Considered | Reason |
|---|---|---|---|
| Object detection | YOLOv8n (nano) | Faster R-CNN, custom CNN | Real-time speed; pretrained weights; simple Ultralytics API |
| Motion analysis | Dense Farneback optical flow | Frame differencing, sparse LK flow | More robust on slow motion and texture-poor metal surfaces |
| Message broker | Apache Kafka | RabbitMQ, Redis Streams | Log-based retention allows replay; scales to many consumers |
| Database | PostgreSQL 15 | InfluxDB, SQLite | Relational schema suits mixed metadata + time-series workloads |
| Dashboard | Streamlit | Grafana, Dash | Minimal boilerplate; Python-native; easy to co-locate with DB queries |
| Orchestration | Docker Compose | Kubernetes, bare metal | Single-node demo; Compose is sufficient and far simpler to operate |

---

## ⚖️ Trade-offs & Design Decisions

This system was designed to balance real-time performance, simplicity, and scalability within the constraints of a prototype environment.

- **YOLOv8 for real-time detection**
  YOLOv8 (nano) was selected for its fast inference speed and ease of integration.
  *Trade-off:* While faster and suitable for real-time processing, it may be slightly less accurate than heavier models such as Faster R-CNN.

- **Optical Flow for motion analysis**
  Dense Optical Flow (Farneback) was used to detect motion instead of deep learning-based motion models.
  *Trade-off:* This approach is lightweight and does not require training, but may be less robust in highly dynamic or noisy environments.

- **Region-based motion for articulated equipment**
  The system splits each machine into regions (e.g., arm vs. base) to correctly detect partial motion such as excavator arm movement.
  *Trade-off:* Region selection is heuristic and tuned to the demo camera angle, which may require adjustment for different viewpoints.

- **High motion sensitivity tuning**
  The system was intentionally tuned to be sensitive to small movements in order to capture subtle articulated motion.
  *Trade-off:* Improves detection of real activity but may increase sensitivity to noise in more complex scenes.

- **Controlled video selection (short, fixed camera)**
  A short video with a fixed camera was used to reduce noise and clearly demonstrate both active and idle states.
  *Trade-off:* Improves clarity and stability but may not fully generalize to real-world multi-camera environments.

- **Frame-based incremental time calculation**
  Active and idle times are accumulated per frame using FPS-based timing.
  *Trade-off:* Ensures smooth real-time updates but introduces minor approximation compared to exact timestamp tracking.

- **Decoupled JSON → Kafka → Database pipeline**
  The vision service writes results to a JSONL file, which is then streamed through Kafka and stored in PostgreSQL. This design:
  - Prevents blocking the vision pipeline due to network or database latency
  - Enables replayability and debugging via persisted logs
  - Decouples processing from data transmission

  *Trade-off:* Introduces a small delay due to file I/O, but significantly improves reliability, scalability, and fault tolerance.

- **Kafka for streaming architecture**
  Kafka was used as the central message broker to enable a scalable and decoupled system.
  *Trade-off:* Adds system complexity compared to direct API communication but allows easy extension with additional consumers.

- **Streamlit for rapid dashboard development**
  Streamlit was chosen to quickly build a functional visualization layer.
  *Trade-off:* Suitable for prototyping, but not as flexible or scalable as full frontend frameworks for production use.

- **Simplified tracking approach with Re-ID heuristics**
  A lightweight Re-ID mechanism was implemented to maintain consistent machine identities across frames.
  *Trade-off:* Works well in controlled scenarios, but may require more advanced tracking (e.g., DeepSORT) in complex environments.

---

## 🔧 Configuration Reference

| Variable | Service(s) | Default | Description |
|---|---|---|---|
| `INPUT_VIDEO` | vision_service | `/app/data/raw/test_clip.mp4` | Path to input video inside container |
| `YOLO_MODEL_PATH` | vision_service | `/app/yolov8n.pt` | YOLOv8 weights file |
| `SHOW_WINDOW` | vision_service | `false` | Show OpenCV window (requires display) |
| `KAFKA_TOPIC` | all | `equipment_tracking` | Kafka topic name |
| `KAFKA_BOOTSTRAP_SERVERS` | producer / consumer | `kafka:9092` | Kafka broker address |
| `POSTGRES_DB` | consumer / dashboard | — | Database name |
| `POSTGRES_USER` | consumer / dashboard | — | DB username |
| `POSTGRES_PASSWORD` | consumer / dashboard | — | DB password |
| `POSTGRES_HOST` | consumer / dashboard | `postgres` | DB hostname (Compose service name) |
| `POSTGRES_PORT` | consumer / dashboard | `5432` | DB port |

---

## 🧩 Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `vision_service` exits immediately | Video file missing or corrupt | Ensure `data/raw/your_video.mp4` exists and is a valid MP4 |
| Kafka producer cannot connect | Broker not yet ready | Increase sleep delay in `docker-compose.yml` for the producer |
| Dashboard shows no data | Producer or consumer did not run | Check: `docker-compose logs kafka_producer` and `docker-compose logs kafka_consumer_db` |
| Port 8501 already in use | Another Streamlit instance running | Change host port to `8502:8501` in `docker-compose.yml` |
| PostgreSQL connection refused | Credential mismatch | Verify `.env` credentials match the running container |
| High false-idle rate on excavator | Arm amplifier too low for your footage | Increase the `3.5` multiplier in `main.py`: `effective_motion = max(full_motion, arm_motion * X)` |

---

## 📦 Python Dependencies

| Package | Purpose |
|---|---|
| `ultralytics` | YOLOv8 model loading, inference, and ByteTrack integration |
| `opencv-python-headless` | Video capture, frame processing, optical flow (no GUI) |
| `numpy` | Array operations for motion score computation |
| `pandas` | Tabular data manipulation in the dashboard |
| `streamlit` | Dashboard UI rendering and auto-refresh |
| `psycopg2-binary` | PostgreSQL adapter for the consumer and dashboard |
| `kafka-python` | Kafka producer and consumer clients |
| `python-dotenv` | `.env` file loading into environment variables |

---

<p align="center">Built with ❤️ using YOLOv8 · Apache Kafka · PostgreSQL · Streamlit · Docker</p>
