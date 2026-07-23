"""Prometheus 指标端点与低基数路由标签测试。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_exposes_http_and_database_observability(
    client: AsyncClient,
) -> None:
    database_response = await client.get("/api/v1/health/database")
    assert database_response.status_code == 200

    await client.get("/api/v1/issues/987654")
    metrics_response = await client.get("/metrics")

    assert metrics_response.status_code == 200
    assert metrics_response.headers["content-type"].startswith("text/plain")
    body = metrics_response.text
    assert "devflow_http_requests_total" in body
    assert "devflow_http_request_duration_seconds" in body
    assert "devflow_db_query_duration_seconds" in body
    assert 'route="/issues/{issue_id}"' in body
    assert 'route="/issues/987654"' not in body
