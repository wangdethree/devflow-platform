"""通知触发、数据归属和已读操作集成测试。"""

import pytest
from httpx import AsyncClient

from app.tests.test_issues import add_member, create_issue
from app.tests.test_projects import create_project, create_user


@pytest.mark.asyncio
async def test_member_notification_is_visible_only_to_recipient(
    client: AsyncClient,
) -> None:
    _, owner_headers = await create_user(
        client,
        username="owner",
        email="owner@example.com",
    )
    member, member_headers = await create_user(
        client,
        username="member",
        email="member@example.com",
    )
    project = await create_project(client, owner_headers)
    await add_member(
        client,
        project_id=project["id"],
        owner_headers=owner_headers,
        user_id=member["id"],
        role="Developer",
    )

    member_response = await client.get(
        "/api/v1/notifications",
        headers=member_headers,
    )
    item = member_response.json()["items"][0]
    assert member_response.json()["total"] == 1
    assert item["type"] == "PROJECT_MEMBER_ADDED"

    owner_response = await client.get(
        "/api/v1/notifications",
        headers=owner_headers,
    )
    assert owner_response.json()["total"] == 0

    forbidden = await client.patch(
        f"/api/v1/notifications/{item['id']}/read",
        headers=owner_headers,
    )
    assert forbidden.status_code == 403

    marked = await client.patch(
        f"/api/v1/notifications/{item['id']}/read",
        headers=member_headers,
    )
    assert marked.status_code == 200
    assert marked.json()["is_read"] is True


@pytest.mark.asyncio
async def test_issue_assignment_and_mark_all_read(client: AsyncClient) -> None:
    _, owner_headers = await create_user(
        client,
        username="owner",
        email="owner@example.com",
    )
    developer, developer_headers = await create_user(
        client,
        username="developer",
        email="developer@example.com",
    )
    project = await create_project(client, owner_headers)
    await add_member(
        client,
        project_id=project["id"],
        owner_headers=owner_headers,
        user_id=developer["id"],
        role="Developer",
    )
    await create_issue(
        client,
        project_id=project["id"],
        headers=owner_headers,
        assignee_id=developer["id"],
    )

    response = await client.get(
        "/api/v1/notifications",
        headers=developer_headers,
    )
    assert {item["type"] for item in response.json()["items"]} == {
        "PROJECT_MEMBER_ADDED",
        "ISSUE_ASSIGNED",
    }

    unread = await client.get(
        "/api/v1/notifications/unread-count",
        headers=developer_headers,
    )
    assert unread.json()["unread_count"] == 2

    marked = await client.patch(
        "/api/v1/notifications/read-all",
        headers=developer_headers,
    )
    assert marked.json()["updated_count"] == 2
    after = await client.get(
        "/api/v1/notifications/unread-count",
        headers=developer_headers,
    )
    assert after.json()["unread_count"] == 0
