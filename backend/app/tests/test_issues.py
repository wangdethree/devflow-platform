"""Issue 筛选分页、权限、软删除和状态机集成测试。"""

import asyncio

import pytest
from httpx import AsyncClient

from app.tests.test_projects import create_project, create_user


async def add_member(
    client: AsyncClient,
    *,
    project_id: int,
    owner_headers: dict[str, str],
    user_id: int,
    role: str,
) -> None:
    response = await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": user_id, "role": role},
        headers=owner_headers,
    )
    assert response.status_code == 201


async def create_issue(
    client: AsyncClient,
    *,
    project_id: int,
    headers: dict[str, str],
    title: str = "实现认证模块",
    assignee_id: int | None = None,
    issue_type: str = "TASK",
    priority: str = "MEDIUM",
) -> dict:
    response = await client.post(
        f"/api/v1/projects/{project_id}/issues",
        json={
            "title": title,
            "description": f"{title}的详细描述",
            "type": issue_type,
            "priority": priority,
            "assignee_id": assignee_id,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_viewer_cannot_create_issue(client: AsyncClient) -> None:
    _, owner_headers = await create_user(
        client,
        username="owner",
        email="owner@example.com",
    )
    viewer, viewer_headers = await create_user(
        client,
        username="viewer",
        email="viewer@example.com",
    )
    project = await create_project(client, owner_headers)
    await add_member(
        client,
        project_id=project["id"],
        owner_headers=owner_headers,
        user_id=viewer["id"],
        role="Viewer",
    )

    response = await client.post(
        f"/api/v1/projects/{project['id']}/issues",
        json={"title": "只读成员不应创建"},
        headers=viewer_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_issue_filter_and_pagination(client: AsyncClient) -> None:
    owner, headers = await create_user(
        client,
        username="owner",
        email="owner@example.com",
    )
    project = await create_project(client, headers)
    await create_issue(
        client,
        project_id=project["id"],
        headers=headers,
        title="登录接口缺陷",
        assignee_id=owner["id"],
        issue_type="BUG",
        priority="HIGH",
    )
    await create_issue(
        client,
        project_id=project["id"],
        headers=headers,
        title="项目列表",
        issue_type="FEATURE",
        priority="LOW",
    )

    response = await client.get(
        "/api/v1/issues",
        params={
            "project_id": project["id"],
            "type": "BUG",
            "priority": "HIGH",
            "keyword": "登录",
            "page": 1,
            "page_size": 1,
        },
        headers=headers,
    )
    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "登录接口缺陷"


@pytest.mark.asyncio
async def test_illegal_status_transition_is_rejected(
    client: AsyncClient,
) -> None:
    owner, headers = await create_user(
        client,
        username="owner",
        email="owner@example.com",
    )
    project = await create_project(client, headers)
    issue = await create_issue(
        client,
        project_id=project["id"],
        headers=headers,
        assignee_id=owner["id"],
    )

    response = await client.patch(
        f"/api/v1/issues/{issue['id']}/status",
        json={"status": "DONE", "version": issue["version"]},
        headers=headers,
    )
    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATE_TRANSITION"


@pytest.mark.asyncio
async def test_non_member_cannot_change_status(client: AsyncClient) -> None:
    owner, owner_headers = await create_user(
        client,
        username="owner",
        email="owner@example.com",
    )
    _, outsider_headers = await create_user(
        client,
        username="outsider",
        email="outsider@example.com",
    )
    project = await create_project(client, owner_headers)
    issue = await create_issue(
        client,
        project_id=project["id"],
        headers=owner_headers,
        assignee_id=owner["id"],
    )

    response = await client.patch(
        f"/api/v1/issues/{issue['id']}/status",
        json={"status": "IN_PROGRESS", "version": issue["version"]},
        headers=outsider_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_deleted_issue_cannot_be_modified(client: AsyncClient) -> None:
    owner, headers = await create_user(
        client,
        username="owner",
        email="owner@example.com",
    )
    project = await create_project(client, headers)
    issue = await create_issue(
        client,
        project_id=project["id"],
        headers=headers,
        assignee_id=owner["id"],
    )
    deleted = await client.delete(
        f"/api/v1/issues/{issue['id']}",
        params={"version": issue["version"]},
        headers=headers,
    )
    assert deleted.status_code == 204

    response = await client.patch(
        f"/api/v1/issues/{issue['id']}",
        json={"title": "不能修改", "version": issue["version"]},
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_concurrent_issue_updates_reject_lost_update(
    client: AsyncClient,
) -> None:
    owner, headers = await create_user(
        client,
        username="owner",
        email="owner@example.com",
    )
    project = await create_project(client, headers)
    issue = await create_issue(
        client,
        project_id=project["id"],
        headers=headers,
        assignee_id=owner["id"],
    )

    async def update_title(title: str):
        return await client.patch(
            f"/api/v1/issues/{issue['id']}",
            json={"title": title, "version": issue["version"]},
            headers=headers,
        )

    first, second = await asyncio.gather(
        update_title("并发更新 A"),
        update_title("并发更新 B"),
    )
    assert sorted([first.status_code, second.status_code]) == [200, 409]
    conflict = first if first.status_code == 409 else second
    assert conflict.json()["code"] == "CONCURRENT_UPDATE"

    current = await client.get(
        f"/api/v1/issues/{issue['id']}",
        headers=headers,
    )
    assert current.json()["version"] == issue["version"] + 1
