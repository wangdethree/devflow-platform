"""基础服务和数据库健康检查测试。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_database_health_check(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/database")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "mysql"}


@pytest.mark.asyncio
async def test_local_frontend_cors_preflight(client: AsyncClient) -> None:
    response = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:5173"
    )
