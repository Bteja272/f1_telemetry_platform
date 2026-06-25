# 🏎️ F1 Real-Time Telemetry Streaming Platform

[![CI](https://github.com/Bteja272/f1_telemetry_platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Bteja272/f1_telemetry_platform/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat&logo=fastapi&logoColor=white)
![Kafka](https://img.shields.io/badge/Apache_Kafka-Event_Streaming-231F20?style=flat&logo=apachekafka&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-EC2-FF9900?style=flat&logo=amazonaws&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

> A production-style distributed telemetry platform ingesting live Formula 1 data through Kafka, storing time-series events in TimescaleDB, caching state in Redis, and delivering real-time visualizations via WebSockets and React — deployed on AWS EC2 with GitHub Actions CI.

**🔴 [Live Demo](https://your-vercel-url.vercel.app)** &nbsp;|&nbsp; **[API Docs](https://your-cloudflare-url.trycloudflare.com/docs)**

---

## 📌 Overview

This project supports two main workflows:

**Live telemetry streaming** — OpenF1 telemetry is ingested through a Kafka producer-consumer pipeline, cached in Redis, persisted in TimescaleDB, and streamed to the frontend via WebSockets.

**Historical race exploration** — Race sessions, driver rosters, circuit maps, and replay data are prepared from OpenF1 and exposed through FastAPI APIs for multi-season race analysis.

---

## 🏗️ Key Technical Decisions

**Why Kafka over a simple queue or direct DB writes?**
Kafka decouples the telemetry producer from the consumer, enabling independent scaling, fault tolerance, and replay of events without data loss. A direct write approach would tightly couple ingestion speed to DB write speed — unacceptable for high-frequency telemetry bursts.

**Why TimescaleDB over plain PostgreSQL?**
TimescaleDB's hypertables provide automatic time-based partitioning and compression for time-series data, significantly improving query performance on telemetry history without changing the PostgreSQL interface. Everything remains SQL-compatible.

**Why Redis for latest-state caching?**
The most common frontend request is "what is this driver doing right now?" — a single key lookup. Redis serves this in sub-millisecond time, eliminating repeated DB reads for high-frequency WebSocket polling.

**Why on-demand replay instead of storing all location points?**
Storing full location data for every driver across every session would consume hundreds of gigabytes. Fetching from OpenF1 on demand keeps storage bounded while maintaining replay functionality.

**Why Cloudflare Tunnel over a load balancer?**
For a portfolio deployment, Cloudflare Tunnel provides HTTPS/WSS without requiring a managed load balancer, static IP, or SSL certificate management — reducing infrastructure cost to zero while maintaining production-grade security.

---

## 🛠️ Tech Stack

| Layer            | Technologies                          |
| ---------------- | ------------------------------------- |
| Backend API      | FastAPI, Python, WebSockets           |
| Streaming        | Apache Kafka, Zookeeper, kafka-python |
| Database         | TimescaleDB, PostgreSQL, SQLAlchemy   |
| Cache            | Redis                                 |
| Frontend         | React, Vite, Recharts, CSS            |
| External Data    | OpenF1 API                            |
| Infrastructure   | Docker, Docker Compose                |
| Cloud Deployment | AWS EC2, Vercel, Cloudflare Tunnel    |
| CI/CD            | GitHub Actions                        |

---

## 📡 System Architecture

```text
                        OpenF1 API
                            │
              ┌─────────────┴──────────────┐
              │                            │
        Live Telemetry            Historical Race Data
              │                            │
              ▼                            ▼
        Kafka Producer             Race Prep Scripts
              │                    ├── Sessions
              ▼                    ├── Drivers
        Apache Kafka               ├── Track Maps
              │                    └── Replay Data
              ▼                            │
        Kafka Consumer ────────────┘
              │
              ▼
        TimescaleDB / PostgreSQL
        ├── Telemetry Events
        ├── Session Metadata
        ├── Driver Metadata
        └── Track Map Points
              │
              ▼
        Redis Cache
        └── Latest Driver State
              │
              ▼
        FastAPI Backend
        ├── REST APIs
        ├── WebSocket Streams
        ├── Replay APIs
        ├── Track Map APIs
        └── Race Explorer APIs
              │
              ▼
        React Dashboard
        ├── Season Selector
        ├── Race Selector
        ├── Driver Profiles
        ├── Interactive Track Map
        ├── Live Telemetry View
        └── Replay Controls
              │
              ▼
        Vercel Frontend + Cloudflare Tunnel (HTTPS / WSS)
```

---

## ✨ Features

### 🔴 Real-Time Telemetry Streaming
- Ingests Formula 1 telemetry from OpenF1 using a Kafka producer
- Streams telemetry events through Kafka for decoupled ingestion and processing
- Persists telemetry history in TimescaleDB
- Caches latest driver state in Redis for low-latency reads
- Pushes live telemetry updates through FastAPI WebSocket endpoints

### 🗂️ Historical Race Explorer
- Browse Formula 1 sessions across multiple seasons (2023–2026)
- Supports available years, sessions, drivers, and race metadata
- Loads race-specific driver rosters from OpenF1
- Enables race-by-race exploration from the frontend dashboard

### 🗺️ Interactive Circuit Visualization
- Generates circuit maps from raw OpenF1 location data
- Stores precomputed track map points in TimescaleDB
- Avoids expensive map generation during frontend page load
- Renders circuit outlines and driver positions in the React dashboard
- Uses official team colors for driver visualization

### ▶️ Driver Replay Engine
- Retrieves historical driver location data from OpenF1 on demand
- Avoids permanently storing millions of raw location points
- Supports driver replay around the circuit
- Includes play, pause, reset, speed control, and timeline scrubbing

### ⚙️ Automated Race Preparation
- Initializes database schema for telemetry, sessions, drivers, and track maps
- Loads session metadata across seasons
- Prepares race-specific driver metadata and track maps
- Supports bulk race preparation workflows
- Handles missing or unavailable OpenF1 data gracefully

### ☁️ Cloud Deployment
- FastAPI backend hosted on AWS EC2
- React frontend deployed on Vercel
- Cloudflare Tunnel exposes the backend over HTTPS/WSS
- Docker Compose manages Kafka, Zookeeper, Redis, and TimescaleDB
- GitHub Actions validates backend and infrastructure changes before deployment

---

## ⚡ Benchmark Results

| Endpoint                               | Avg Latency | Notes                        |
| -------------------------------------- | ----------- | ---------------------------- |
| `GET /drivers/{driver_number}/latest`  | ~21 ms      | Redis-cached, no DB read     |
| `GET /metrics/system`                  | ~24 ms      | Aggregated system metrics    |
| `GET /drivers/{driver_number}/history` | ~27 ms      | TimescaleDB hypertable query |

---

## 📁 Project Structure

```text
f1_telemetry_platform/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── telemetry.py
│   │       └── websocket_routes.py
│   ├── cache/
│   │   └── redis_client.py
│   ├── consumer/
│   │   └── telemetry_consumer.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── database.py
│   │   ├── init_db.py
│   │   └── models.py
│   ├── producer/
│   │   └── openf1_producer.py
│   ├── repositories/
│   │   └── telemetry_repository.py
│   ├── scripts/
│   │   ├── load_sessions.py
│   │   ├── prepare_race.py
│   │   └── prepare_races_per_year.py
│   ├── services/
│   │   └── telemetry_service.py
│   ├── websocket/
│   │   └── connection_manager.py
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🔌 API Reference

### Core

| Method | Endpoint          | Description                    |
| ------ | ----------------- | ------------------------------ |
| `GET`  | `/`               | Root API check                 |
| `GET`  | `/health`         | Backend health check           |
| `GET`  | `/metrics`        | Application metrics            |
| `GET`  | `/metrics/system` | System-level telemetry metrics |

### Seasons and Sessions

| Method | Endpoint                          | Description                              |
| ------ | --------------------------------- | ---------------------------------------- |
| `GET`  | `/years`                          | List available F1 seasons                |
| `GET`  | `/years/{year}/sessions`          | List available sessions for a given year |
| `GET`  | `/sessions`                       | List stored sessions                     |
| `GET`  | `/sessions/{session_key}/drivers` | Get driver roster for a session          |

### Telemetry

| Method | Endpoint                                                  | Description                                         |
| ------ | --------------------------------------------------------- | --------------------------------------------------- |
| `GET`  | `/drivers/{driver_number}/latest`                         | Latest telemetry snapshot for a driver              |
| `GET`  | `/drivers/{driver_number}/history`                        | Historical telemetry for a driver                   |
| `GET`  | `/sessions/{session_key}/drivers/{driver_number}/history` | Session-specific driver telemetry history           |
| `WS`   | `/ws/telemetry`                                           | Live telemetry stream for all latest driver updates |
| `WS`   | `/ws/telemetry/{driver_number}`                           | Live telemetry stream for a specific driver         |

### Track Maps and Replay

| Method | Endpoint                                                           | Description                                        |
| ------ | ------------------------------------------------------------------ | -------------------------------------------------- |
| `GET`  | `/sessions/{session_key}/track-map`                                | Precomputed track map for a session                |
| `GET`  | `/sessions/{session_key}/latest-locations`                         | Latest stored driver locations for a session       |
| `GET`  | `/sessions/{session_key}/openf1-latest-locations`                  | Latest driver locations fetched from OpenF1        |
| `GET`  | `/sessions/{session_key}/drivers/{driver_number}/openf1-locations` | On-demand historical replay locations for a driver |

---

## 🚀 Quick Start (Local)

```bash
# 1. Clone and set up environment
git clone https://github.com/Bteja272/f1_telemetry_platform.git
cd f1_telemetry_platform
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Start infrastructure
docker compose up -d

# 3. Initialize database and load sessions
python -m app.db.init_db
python -m app.scripts.load_sessions

# 4. Prepare a race
python -m app.scripts.prepare_race <SESSION_KEY>

# 5. Start backend + streaming (3 terminals)
python -m uvicorn app.main:app --reload
python -m app.consumer.telemetry_consumer
python -m app.producer.openf1_producer

# 6. Start frontend
cd frontend && npm install && npm run dev
```

API docs at `http://localhost:8000/docs` · Frontend at `http://localhost:5173`

---

## ✅ CI/CD

This project uses GitHub Actions to validate backend and infrastructure changes before deployment.

The CI workflow checks:
- Python dependency installation
- Python syntax compilation
- FastAPI app import
- Docker Compose configuration validation

Planned improvements:
- Frontend build validation
- Backend API smoke tests
- Automated EC2 deployment on merge

---

## ☁️ Deployment (AWS EC2)

```bash
# SSH in and start infrastructure
ssh -i path/to/key.pem ubuntu@YOUR_EC2_IP
cd ~/f1_telemetry_platform
docker compose up -d

# Start backend
source .venv/bin/activate
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# Expose via Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8000
```

Update Vercel environment variables with the Cloudflare URL:
```env
VITE_API_BASE_URL=https://your-cloudflare-url.trycloudflare.com
VITE_WS_URL=wss://your-cloudflare-url.trycloudflare.com/ws/telemetry
```

---

## 🔐 Security Notes

Never commit sensitive values. Use `.env` locally and platform secrets for deployment.

```env
DATABASE_URL=postgresql://<username>:<password>@localhost:<port>/<database_name>
```

---

## 🏆 Engineering Highlights

- Architected fault-tolerant Kafka producer-consumer pipeline decoupling telemetry ingestion from persistence, enabling independent scaling of each layer
- Designed hybrid storage strategy — persisted telemetry in TimescaleDB hypertables for historical queries, on-demand OpenF1 location fetch for replay, avoiding storage of millions of transient location points
- Achieved ~21ms Redis-cached API latency for latest driver state, eliminating redundant DB reads for high-frequency WebSocket polling
- Precomputed and stored circuit maps from raw OpenF1 location streams, reducing frontend rendering latency to sub-second page loads
- Deployed FastAPI on AWS EC2 and React on Vercel with end-to-end HTTPS/WSS secured via Cloudflare Tunnel
- Implemented GitHub Actions CI workflow validating Python syntax, FastAPI imports, and Docker Compose config before every deployment

---

## 🗺️ Roadmap

- [ ] Frontend build validation in GitHub Actions
- [ ] Backend API smoke tests in CI
- [ ] Systemd service for FastAPI backend on EC2
- [ ] Permanent named Cloudflare Tunnel with custom domain
- [ ] Multi-driver side-by-side telemetry comparison
- [ ] RPM, throttle, brake, and speed overlay charts
- [ ] Lap time leaderboards and sector analysis
- [ ] Telemetry anomaly detection and alerting
- [ ] Redis caching for OpenF1 latest-location calls
- [ ] Full Dockerized backend deployment

---

## 📝 License

This project is licensed under the MIT License.

---

> Built as a production-style distributed telemetry platform demonstrating Kafka streaming, FastAPI REST/WebSocket APIs, Redis caching, TimescaleDB time-series storage, React visualization, AWS EC2 deployment, and GitHub Actions CI.