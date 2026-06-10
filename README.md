# 🏎️ F1 Real-Time Telemetry Streaming Platform

A distributed telemetry analytics and visualization platform for Formula 1 data — combining real-time streaming with historical race exploration. The system ingests live telemetry from OpenF1, streams events through Kafka, stores time-series data in TimescaleDB, caches state in Redis, and delivers interactive race visualizations through FastAPI and React.

---

## 📡 System Architecture

```
                        OpenF1 API
                            │
              ┌─────────────┴──────────────┐
              │                            │
        Live Telemetry            Historical Race Data
              │                            │
              ▼                            ▼
        Kafka Producer             Race Prep Scripts
              │                    (sessions, drivers,
              ▼                     circuits, track maps)
        Apache Kafka                        │
              │                            │
              ▼                            ▼
        Kafka Consumer ──────────► TimescaleDB
                                   ├── Telemetry Events
                                   ├── Session Metadata
                                   ├── Driver Metadata
                                   └── Track Maps (precomputed)
                                            │
                                   Redis Cache
                                   └── Latest Driver State
                                            │
                                            ▼
                                    FastAPI Backend
                                   ├── REST APIs
                                   ├── WebSocket Endpoints
                                   ├── Replay APIs
                                   ├── Track Map APIs
                                   └── Race Explorer APIs
                                            │
                                            ▼
                                   React Dashboard (Vercel)
                                   ├── Live Telemetry View
                                   ├── Historical Race Explorer
                                   ├── Interactive Circuit Maps
                                   ├── Driver Profiles
                                   └── Replay Controls
                                            │
                                            ▼
                               Cloudflare Tunnel (HTTPS / WSS)
```

---

## ✨ Features

### 🔴 Real-Time Telemetry Streaming
- Ingests live Formula 1 telemetry from OpenF1 via a Kafka producer-consumer pipeline
- Processes speed, RPM, throttle, brake, gear, and DRS events in near real time
- WebSocket endpoints push live telemetry updates directly to the frontend dashboard

### 🗂️ Historical Race Explorer
- Browse Formula 1 races across multiple seasons (2023–2026)
- Filter by year and circuit
- Dynamically loads driver rosters, session metadata, and race information

### 🗺️ Interactive Circuit Visualization
- Auto-generates track maps from raw OpenF1 location data
- Stores precomputed, downsampled circuit outlines for rapid frontend rendering
- Places drivers on circuit layouts using official team colors
- Supports per-driver race visualization and telemetry inspection

### ▶️ Driver Replay Engine
- On-demand retrieval of historical location data from OpenF1 — no permanent storage of millions of location points
- Replay driver movement around the circuit at adjustable speeds
- Timeline scrubbing controls for exploring specific race moments

### ⚙️ Automated Race Preparation Pipeline
- Automated scripts pre-load race and driver metadata, circuit information, and track maps into TimescaleDB
- Supports bulk preparation of entire Formula 1 seasons in a single run
- Gracefully handles missing race data and API differences across seasons

### 📦 Distributed Data Architecture
- Kafka decouples telemetry ingestion from processing and storage
- Redis caches the latest telemetry snapshot per driver for sub-millisecond retrieval
- TimescaleDB stores full telemetry history and all race metadata as time-series hypertables
- FastAPI serves REST and WebSocket traffic from a single backend process

### ⚡ Performance Optimization
- Track maps are precomputed and stored — no on-the-fly geometry processing on page load
- Downsampling reduces circuit payload size while preserving visual accuracy
- Redis cache eliminates redundant DB reads for frequently polled driver state
- Location replay data is fetched on demand, keeping storage overhead low

### ☁️ Cloud Deployment
- FastAPI backend hosted on AWS EC2
- React frontend deployed on Vercel
- HTTPS and WSS secured end-to-end via Cloudflare Tunnel
- All infrastructure services containerized with Docker Compose

### 📊 Monitoring & Observability
- Dedicated metrics endpoint tracks telemetry ingestion volume, active drivers, and API latency
- Operational visibility into Kafka, Redis, and TimescaleDB health

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | FastAPI, Python, WebSockets, SQLAlchemy, kafka-python |
| **Frontend** | React, Vite, Recharts, CSS |
| **Streaming** | Apache Kafka, Zookeeper |
| **Databases** | TimescaleDB (PostgreSQL), Redis |
| **DevOps / Cloud** | Docker, Docker Compose, AWS EC2, Cloudflare Tunnel, Vercel |

---

## 📁 Project Structure

```
f1_telemetry_platform/
│
├── app/
│   ├── api/              # REST API route handlers (telemetry, races, drivers, maps)
│   ├── cache/            # Redis client and caching logic
│   ├── consumer/         # Kafka consumer — persists events to TimescaleDB and Redis
│   ├── core/             # App config, settings, and startup lifecycle
│   ├── db/               # SQLAlchemy models, TimescaleDB schema, migrations
│   ├── producer/         # Kafka producer — polls OpenF1 live telemetry
│   ├── services/         # Business logic shared across API and consumer layers
│   └── websocket/        # WebSocket connection manager and live broadcast
│
├── frontend/
│   ├── src/              # React components, pages, hooks, and chart logic
│   └── public/           # Static assets
│
├── scripts/              # Race preparation, season bulk-load, and utility scripts
├── docker-compose.yml    # Kafka, Zookeeper, Redis, TimescaleDB
├── requirements.txt
└── README.md
```

---

## 🔌 API Reference

### Telemetry

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `GET` | `/drivers/{driver_number}/latest` | Latest telemetry snapshot (Redis-cached) |
| `GET` | `/drivers/{driver_number}/history` | Historical telemetry from TimescaleDB |
| `GET` | `/metrics/system` | System metrics — latency, event counts, active drivers |
| `WS` | `/ws/telemetry/{driver_number}` | Live WebSocket stream for a driver |

### Race Explorer

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/races` | List available races, optionally filtered by year |
| `GET` | `/races/{session_key}` | Race metadata and driver roster |
| `GET` | `/races/{session_key}/track` | Precomputed circuit track map |
| `GET` | `/drivers/{driver_number}/replay` | On-demand historical location data for replay |

---

## ⚡ Benchmark Results

| Endpoint | Avg Latency |
|---|---|
| `GET /drivers/{n}/latest` | ~19 ms |
| `GET /metrics/system` | ~24 ms |
| `GET /drivers/{n}/history` | ~27 ms |

---

## 🚀 Local Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

---

### 1. Clone the Repository

```bash
git clone https://github.com/Bteja272/f1_telemetry_platform.git
cd f1_telemetry_platform
```

---

### 2. Set Up Python Environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

---

### 3. Start Infrastructure Services

```bash
docker compose up -d
```

Verify all containers are running:

```bash
docker ps
```

Expected containers:

| Container | Service |
|---|---|
| `f1_kafka` | Apache Kafka broker |
| `f1_zookeeper` | Kafka coordination |
| `f1_redis` | Redis cache |
| `f1_timescaledb` | TimescaleDB (PostgreSQL) |

---

### 4. Initialize the Database

```bash
python -m app.db.init_db
```

---

### 5. (Optional) Prepare Historical Race Data

Load race metadata, driver rosters, and precomputed track maps for one or more seasons:

```bash
# Prepare a single session
python -m scripts.prepare_session --session_key <SESSION_KEY>

# Bulk-prepare an entire season
python -m scripts.prepare_season --year 2024
```

---

### 6. Run Backend Services

Open three separate terminals:

```bash
# Terminal 1 — FastAPI server
uvicorn app.main:app --reload

# Terminal 2 — Kafka consumer
python -m app.consumer.telemetry_consumer

# Terminal 3 — Kafka producer (live OpenF1 polling)
python -m app.producer.openf1_producer
```

---

### 7. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: `http://localhost:5173`

---

## ☁️ Cloud Deployment (AWS EC2)

### SSH into EC2

```bash
ssh -i "f1-telemetry-key.pem" ubuntu@YOUR_EC2_PUBLIC_IP
```

### Start Infrastructure

```bash
docker compose up -d
```

### Run Services with tmux

```bash
# FastAPI
tmux new -s api
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Kafka Consumer
tmux new -s consumer
python -m app.consumer.telemetry_consumer

# Kafka Producer
tmux new -s producer
python -m app.producer.openf1_producer

# Cloudflare Tunnel — exposes HTTPS/WSS publicly
tmux new -s cloudflare
cloudflared tunnel --url http://localhost:8000
```

> The public HTTPS/WSS URL printed by the Cloudflare session is what the Vercel frontend connects to. Set it as your `VITE_API_URL` environment variable in Vercel.

---

## 🏆 Engineering Highlights

- Built a fault-tolerant distributed telemetry pipeline using Kafka, FastAPI, Redis, and TimescaleDB
- Designed a hybrid architecture combining persisted telemetry history with on-demand OpenF1 replay retrieval — avoiding storing millions of transient location points
- Automated race preparation workflows generate and store reusable circuit maps from raw OpenF1 location streams
- Created an interactive Formula 1 race explorer supporting multiple seasons, circuits, drivers, and live replay visualization
- Delivered sub-second race loading using precomputed track maps and Redis-cached telemetry state

---

## 🗺️ Roadmap

- [ ] Multi-driver side-by-side telemetry comparison
- [ ] RPM / throttle / brake overlay charts
- [ ] Lap time leaderboards and sector analysis
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Nginx reverse proxy
- [ ] Permanent named Cloudflare Tunnel + custom domain
- [ ] Telemetry anomaly detection and alerting

---

## 📝 License

[MIT License](LICENSE)