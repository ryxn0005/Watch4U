from pathlib import Path

from surrealdb.connections.async_embedded import AsyncEmbeddedSurrealConnection
from surrealdb.connections.async_http import AsyncHttpSurrealConnection
from surrealdb.connections.async_ws import AsyncWsSurrealConnection

Connection = AsyncEmbeddedSurrealConnection | AsyncWsSurrealConnection | AsyncHttpSurrealConnection

_SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "db" / "schema.surql"


async def apply_schema(db: Connection) -> None:
    text = _SCHEMA_PATH.read_text(encoding="utf-8")
    await db.query(text)
