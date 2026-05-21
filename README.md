# 🏎️ F1 Real-Time Telemetry Streaming Platform

A cloud-deployed, distributed telemetry streaming platform that ingests, processes, stores, caches, and visualizes live Formula 1 telemetry data. Built with Kafka, FastAPI WebSockets, Redis, TimescaleDB, Docker, React, AWS EC2, and Cloudflare Tunnel.

---

## 📡 Live Architecture

```
OpenF1 API
     │
     ▼
Kafka Producer          ← Polls OpenF1 API, normalizes + publishes telemetry events
     │
     ▼
Apache Kafka            ← Distributed event streaming backbone
     │
     ▼
Kafka Consumer          ← Consumes events, writes to DB and cache
     │
     ├──────────────────────────────┐
     ▼                              ▼
TimescaleDB                       Redis
(time-series storage)             (latest telemetry cache)
     │                              │
     └──────────────┬───────────────┘
                    ▼
            FastAPI Backend
          (REST + WebSockets)
                    │
                    ▼
         React Frontend (Vercel)
                    │
                    ▼
       Cloudflare Tunnel (HTTPS/WSS)
```

---

## ✨ Features

### Real-Time Telemetry Streaming
- Streams live telemetry events from the [OpenF1 API](https://openf1.org/)
- Processes speed, RPM, throttle, brake, gear, and DRS data per driver
- Apache Kafka handles distributed, fault-tolerant event streaming

### WebSocket-Based Live Dashboard
- Instant frontend updates via FastAPI WebSockets — no polling, no page refreshes
- Live telemetry charts rendered with Recharts
- Displays the last 30 telemetry snapshots per driver in real time

### Distributed Data Pipeline
- Decoupled Kafka producer/consumer architecture for resilient ingestion
- Event normalization and schema enforcement before storage
- Low-latency end-to-end telemetry workflow

### Time-Series Storage with TimescaleDB
- Hypertable schema optimized for time-ordered telemetry events
- Supports historical telemetry replay and analytics queries
- PostgreSQL-compatible — use any standard SQL tooling

### Redis Caching Layer
- Stores the latest telemetry snapshot per driver at `driver:{driver_number}:latest`
- Reduces per-request DB load and cuts API response latency to ~19 ms
- Enables near-instant frontend rendering on WebSocket connect

### Cloud Deployment
- FastAPI backend hosted on AWS EC2
- React frontend deployed on Vercel
- HTTPS and WSS secured end-to-end via Cloudflare Tunnel
- All infrastructure services containerized with Docker Compose

### Monitoring & Metrics
- API, Redis, and TimescaleDB latency tracking
- Active driver and telemetry event counters exposed via `/metrics/system`

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
│   ├── api/              # REST API route handlers
│   ├── cache/            # Redis client and caching logic
│   ├── consumer/         # Kafka consumer — writes to DB and Redis
│   ├── core/             # App config, settings, startup
│   ├── db/               # SQLAlchemy models, TimescaleDB init
│   ├── producer/         # Kafka producer — polls OpenF1 API
│   ├── services/         # Business logic shared across layers
│   └── websocket/        # WebSocket connection manager
│
├── frontend/
│   ├── src/              # React components and hooks
│   └── public/           # Static assets
│
├── scripts/              # Utility and maintenance scripts
├── docker-compose.yml    # Kafka, Zookeeper, Redis, TimescaleDB
├── requirements.txt
└── README.md
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `GET` | `/drivers/{driver_number}/latest` | Latest telemetry snapshot for a driver (Redis-cached) |
| `GET` | `/drivers/{driver_number}/history` | Historical telemetry from TimescaleDB |
| `GET` | `/metrics/system` | System metrics (latency, event counts, active drivers) |
| `WS` | `/ws/telemetry/{driver_number}` | Live WebSocket stream for a driver |

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

Verify all four containers are running:

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

### 5. Run Backend Services

Open three separate terminals:

```bash
# Terminal 1 — FastAPI server
uvicorn app.main:app --reload

# Terminal 2 — Kafka consumer
python -m app.consumer.telemetry_consumer

# Terminal 3 — Kafka producer (OpenF1 polling)
python -m app.producer.openf1_producer
```

---

### 6. Start the Frontend

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

# Cloudflare Tunnel (HTTPS/WSS)
tmux new -s cloudflare
cloudflared tunnel --url http://localhost:8000
```

> The Cloudflare Tunnel URL printed in the `cloudflare` tmux session is the public HTTPS/WSS endpoint for the frontend to connect to.

---

## 🗺️ Roadmap

- [ ] Multi-driver side-by-side dashboard
- [ ] Historical lap replay with scrubbing
- [ ] RPM / throttle / brake overlay charts
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Nginx reverse proxy
- [ ] Permanent named Cloudflare Tunnel + custom domain
- [ ] Telemetry anomaly detection

---

## 📝 License

[MIT License](LICENSE)