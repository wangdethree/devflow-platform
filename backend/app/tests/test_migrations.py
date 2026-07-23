"""Alembic 迁移版本一致性测试。"""

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
import pytest

from app.core.config import BACKEND_DIR
from app.database.session import engine


@pytest.mark.asyncio
async def test_database_is_at_alembic_head() -> None:
    """测试库必须已经升级到代码声明的唯一 head。"""

    config = Config(BACKEND_DIR / "alembic.ini")
    script = ScriptDirectory.from_config(config)
    expected_head = script.get_current_head()

    async with engine.connect() as connection:
        current_head = await connection.run_sync(
            lambda sync_connection: MigrationContext.configure(
                sync_connection
            ).get_current_revision()
        )

    assert current_head == expected_head
