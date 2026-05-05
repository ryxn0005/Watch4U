import pytest
from surrealdb import AsyncSurreal

from app.db.schema import apply_schema


@pytest.mark.asyncio
async def test_schema_applies_on_embedded() -> None:
    async with AsyncSurreal("mem://") as db:
        await db.use("watch4u", "main")
        await apply_schema(db)
        await apply_schema(db)
        ver = await db.version()
        assert "surrealdb" in str(ver).lower()
