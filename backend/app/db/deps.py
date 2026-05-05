from fastapi import HTTPException, Request
from surrealdb.connections.async_embedded import AsyncEmbeddedSurrealConnection
from surrealdb.connections.async_http import AsyncHttpSurrealConnection
from surrealdb.connections.async_ws import AsyncWsSurrealConnection

SurrealConnection = (
    AsyncEmbeddedSurrealConnection | AsyncWsSurrealConnection | AsyncHttpSurrealConnection
)


async def get_surreal(request: Request) -> SurrealConnection:
    db = getattr(request.app.state, "surreal", None)
    if db is None:
        raise HTTPException(status_code=503, detail="SurrealDB is not configured or failed to start")
    return db
