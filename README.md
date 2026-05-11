# F1 Real-Time Telemetry Streaming Platform

A distributed real-time telemetry analytics platform that ingests Formula 1 telemetry data from OpenF1, streams events through Kafka, and prepares telemetry for real-time processing, storage, and visualization.

## Tech Stack

- Python
- FastAPI
- Apache Kafka
- Redis
- PostgreSQL + TimescaleDB
- Docker & Docker Compose

---

## Current Progress

### Day 1
- Project structure initialized
- Docker Compose infrastructure configured
- Kafka, Zookeeper, Redis, and TimescaleDB containers added
- OpenF1 telemetry producer implemented
- Telemetry events successfully published to Kafka
- Kafka topic consumption verified

---

## Project Architecture

```text
OpenF1 API
    ↓
Telemetry Producer
    ↓
Kafka Topic
    ↓
Telemetry Consumer
    ↓
TimescaleDB + Redis
    ↓
FastAPI APIs + WebSockets
    ↓
Frontend Dashboard