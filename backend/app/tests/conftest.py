"""真实 MySQL 测试库隔离、基础数据和 HTTP 客户端夹具。"""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete


# 在导入应用配置前切换到独立测试库，禁止污染开发数据。
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["MYSQL_DATABASE"] = "devflow_migration_test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-only-for-automated-tests"

from app.database.session import AsyncSessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.permission import Permission  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.role_permission import RolePermission  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.user_role import UserRole  # noqa: E402
from app.services.seed_service import seed_reference_data  # noqa: E402


async def clean_auth_tables() -> None:
    """按外键依赖顺序清理当前阶段测试数据。"""

    async with AsyncSessionLocal() as session:
        for model in (UserRole, RolePermission, User, Permission, Role):
            await session.execute(delete(model))
        await session.commit()


@pytest.fixture(autouse=True)
async def isolated_database() -> AsyncGenerator[None, None]:
    await clean_auth_tables()
    async with AsyncSessionLocal() as session:
        await seed_reference_data(session)
    yield
    await clean_auth_tables()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as http_client:
        yield http_client
