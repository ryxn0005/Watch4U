# Backend — FastAPI

Owners: **Ryan, Muhamad**

The backend hosts all domain logic for Watch4U. The Streamlit prototype (and future Next.js app) call this service over HTTP — UI shells can be swapped without touching anything in `app/services/`.

## Prerequisites

- **SurrealDB** — Required for data persistence and RAG vector search
  ```bash
  make surreal-up  # Start SurrealDB (runs on port 8080)
  ```

## Run

```bash
# From repo root (starts both SurrealDB + FastAPI)
make up

# Or start individually
make surreal-up    # SurrealDB first
make backend       # FastAPI on http://localhost:8000

# Or directly
cd backend
cp .env.example .env
# Edit .env with your SurrealDB credentials
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/docs for the auto-generated Swagger UI.

## Layout

```
backend/
├── main.py                FastAPI app entrypoint
├── requirements.txt
├── Dockerfile
├── docker-compose.surreal.yml   SurrealDB service
├── db/
│   └── schema.surql       SurrealDB schema (tables, indexes, events)
└── app/
    ├── core/              Settings, config, shared constants
    ├── models/            Pydantic schemas (request/response DTOs)
    ├── routers/           HTTP endpoints, one router per feature
    └── services/          Domain logic — one folder per teammate's component
        ├── fall_detection/    (Darrel) CV pipeline
        ├── wifi_detection/    (Ryan)   Wi-Fi CSI sensing
        ├── triage/            (Jayce)  Clinical severity / Cat 1–5 logic
        └── rag/               (Ryan)   Multilingual RAG (SurrealDB vector store)
```

## Database Schema

SurrealDB schema is defined in `db/schema.surql` and applied automatically on startup:

| Table       | Purpose                              | Key Features                    |
|-------------|--------------------------------------|----------------------------------|
| `resident`  | Patient profiles                     | Full-text search, timestamps    |
| `fall_event`| Detected falls                       | Relations to residents          |
| `document`  | RAG knowledge base                   | 768-dim embeddings, HNSW index  |
| `sensor_reading` | Wi-Fi CSI data                  | Time-series capable             |

**Key Indexes:**
- `search_resident` — Full-text search on resident names
- `idx_fall_event_timestamp` — Time-based queries
- `hnsw_document_embedding` — Vector similarity (HNSW, 768 dims, cosine)

## Adding a new endpoint

1. Define the request/response schema in `app/models/`
2. Add the business logic in `app/services/<your_component>/`
3. Wire it up to a router in `app/routers/`
4. Include the router in `main.py`
5. Add a test in `tests/`
