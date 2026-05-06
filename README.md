# Watch4U

**Context-Aware AI Fall Detection with Multilingual Staged Escalation for CALD Seniors**

41004 - Group 43A

## Project Structure

```
Watch4U/
├── backend/          FastAPI service - domain logic (Ryan, Muhamad)
├── streamlit_app/    Prototype UI - multi-page demo for each component
├── data/             Synthetic patient profiles + preprocessing (Affan)
└── frontend/         Future Next.js web app (placeholder)
```

## Prerequisites

The following tools are required to run Watch4U:

- **Docker** 20.10+ and **Docker Compose** v2.0+ (everything runs in containers)
- **GNU Make** 4.0+ (for task automation)
- **Git** 2.0+ (for version control)

Python and Node.js are NOT required for the standard workflow - all services run in containers. Install them locally only if developing individual components outside of Docker.

## Quickstart

```bash
# Spin up backend + Streamlit prototype
make up

# Or start them individually
make backend       # FastAPI on http://localhost:8000
make streamlit     # Streamlit on http://localhost:8501

# Start with SurrealDB (required for RAG vector search)
make surreal-up    # SurrealDB on http://localhost:8080
make backend       # FastAPI with SurrealDB connection

# Restart everything (stop + rebuild + start)
make restart

# Stop everything
make down
make surreal-down  # Stop SurrealDB separately
```

## Team & Component Ownership

| Component             | Owner(s)        | Path                                   | Database                |
|-----------------------|-----------------|----------------------------------------|-------------------------|
| RAG workflow          | Ryan            | `backend/app/services/rag/`            | SurrealDB (vector)      |
| Triage logic          | Jayce           | `backend/app/services/triage/`         | SurrealDB               |
| Fall detection (CV)   | Darrel          | `backend/app/services/fall_detection/` | -                       |
| Wi-Fi detection       | Ryan            | `backend/app/services/wifi_detection/` | SurrealDB               |
| Backend setup         | Ryan, Muhamad   | `backend/`                             | SurrealDB               |
| Synthetic data + prep | Affan           | `data/`                                | -                       |

## Database Architecture

All persistent data is stored in **SurrealDB**, a multi-model database with native vector search support:

- **Residents** — Patient profiles, emergency contacts, care plans
- **Fall Events** — Detected falls with severity, location, timestamps
- **RAG Documents** — Medical knowledge with 768-dim vector embeddings (HNSW index)
- **Sensor Data** — Wi-Fi CSI readings and CV detection events

SurrealDB runs via Docker Compose (`backend/docker-compose.surreal.yml`) and is accessible at `ws://localhost:8080`.

## Documents

- A1 - Plan and Proposal: `41004 A1.docx`
- A2 - Mid-Project Update: `41004 A2.docx`
