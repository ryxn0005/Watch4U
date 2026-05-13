import logging
from typing import Any

from surrealdb import AsyncSurreal

from app.core.config import Settings
from app.db.schema import apply_schema

log = logging.getLogger("watch4u.db")


def _url_embedded(url: str) -> bool:
    u = url.strip().lower()
    return (
        u.startswith("mem://")
        or u.startswith("memory:")
        or u.startswith("file://")
        or u.startswith("surrealkv://")
    )


async def init_surreal(app: Any, settings: Settings) -> None:
    url = settings.surreal_url.strip()
    if not url:
        log.info("SurrealDB disabled (SURREAL_URL empty)")
        app.state.surreal = None
        return
    db = AsyncSurreal(url)
    try:
        await db.__aenter__()
    except BaseException:
        log.exception("SurrealDB connection failed")
        app.state.surreal = None
        return
    try:
        if not _url_embedded(url):
            await db.signin(
                {"username": settings.surreal_username, "password": settings.surreal_password}
            )
        await db.use(settings.surreal_namespace, settings.surreal_database)
        if settings.surreal_apply_schema_on_startup:
            await apply_schema(db)
            log.info("SurrealDB schema applied")
        ver = await db.version()
        log.info("SurrealDB ready (%s)", ver)
        app.state.surreal = db
    except BaseException:
        await db.__aexit__(None, None, None)
        app.state.surreal = None
        log.exception("SurrealDB failed to start")


async def shutdown_surreal(app: Any) -> None:
    db = getattr(app.state, "surreal", None)
    if db is not None:
        await db.__aexit__(None, None, None)
        app.state.surreal = None
        log.info("SurrealDB connection closed")
