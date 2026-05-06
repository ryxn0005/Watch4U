# rag/

Owner: **Ryan**

Retrieval-Augmented Generation workflow for multilingual (English ↔ Vietnamese) medical Q&A and carer guidance.

## Architecture

The RAG service now uses **SurrealDB** as its document and vector store:

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG Service                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Query → Embedding → SurrealDB HNSW Search → Results  │
│                     ↓                                       │
│              ┌──────────────┐                               │
│              │  SurrealDB   │                               │
│              │  - document  │                               │
│              │  - embedding │                               │
│              │  - HNSW idx  │                               │
│              └──────────────┘                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Storage

- **Database**: SurrealDB with native vector support
- **Index**: HNSW (Hierarchical Navigable Small World) for fast ANN search
- **Dimensions**: 768 (compatible with PhoBERT)
- **Distance**: Cosine similarity

## API Endpoints

- `POST /api/rag/query` - Query for medical Q&A with citations
- `POST /api/rag/ingest` - Ingest documents into vector store
- `GET /api/rag/stats` - Get vector store statistics

## Configuration

SurrealDB must be configured in `.env`:
```
SURREAL_URL=ws://127.0.0.1:8080
SURREAL_USERNAME=root
SURREAL_PASSWORD=root
SURREAL_NAMESPACE=watch4u
SURREAL_DATABASE=main
SURREAL_APPLY_SCHEMA_ON_STARTUP=true
```

## Implementation Details

### Vector Search Query
```sql
SELECT id, content, source, language, vector::distance::knn() as distance
FROM document
WHERE language = $language 
  AND embedding <|$k,40|> $query_embedding
ORDER BY distance
LIMIT $limit
```

### Embedding Generation
Currently uses deterministic mock embeddings (SHA256-based) for demonstration.
Ready to upgrade to PhoBERT for Vietnamese and multilingual models:

```python
# TODO: Replace with PhoBERT
embedding = phobert_model.encode(text)  # 768 dims
```

## Scope

- Input: user query (EN or VI) + optional patient context
- Output: answer with citations, in the user's language
- Corpora: **ViMQ**, **VietMed-NER**, **ViMedical Disease**, plus English clinical references
- Embeddings: **PhoBERT** for VI, multilingual model for cross-lingual retrieval

## Notes

- API security for third-party LLM calls — keep keys in `.env`, never in code
- Always return citations; never let the model answer without grounded context
- Graceful fallback to sample knowledge when SurrealDB is empty
