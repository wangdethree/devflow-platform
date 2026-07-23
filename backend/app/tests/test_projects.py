"""项目创建事务、成员管理和项目级权限集成测试。"""

import pytest
from httpx import AsyncClient


async def create_user(
    client: AsyncClient,
    *,
    username: str,
    email: str,
) -> tuple[dict, dict[str, str]]:
    password = "StrongPass123!"
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert register_response.status_code == 201
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    token = login_response.json()["access_token"]
    return (
        register_response.json(),
        {"Authorization": f"Bearer {token}"},
    )


async def create_project(client: AsyncClient, headers: dict[str, str]) -> dict:
    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "DevFlow API",
            "description": "研发协作平台",
            "status": "ACTIVE",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_create_project_atomically_creates_owner_membership(
    client: AsyncClient,
) -> None:
    owner, headers = await create_user(
        client,
        username="owner",
        email="owner@example.com",
    )
    project = await create_project(client, headers)

    members_response = await client.get(
        f"/api/v1/projects/{project['id']}/members",
        headers=headers,
    )
    assert members_response.status_code == 200
    assert members_response.json()["items"] == [
        {
            "id": members_response.json()["items"][0]["id"],
            "project_id": project["id"],
            "user_id": owner["id"],
            "username": "owner",
            "email": "owner@example.com",
            "role": "Owner",
            "joined_at": members_response.json()["items"][0]["joined_at"],
        }
    ]


@pytest.mark.asyncio
async def test_duplicate_member_is_rejected(client: AsyncClient) -> None:
    _, owner_headers = await create_user(
        client,
        username="owner",
        email="owner@example.com",
    )
    developer, _ = await create_user(
        client,
        username="developer",
        email="developer@example.com",
    )
    project = await create_project(client, owner_headers)
    payload = {"user_id": developer["id"], "role": "Developer"}

    first = await client.post(
        f"/api/v1/projects/{project['id']}/members",
        json=payload,
        headers=owner_headers,
    )
    duplicate = await client.post(
        f"/api/v1/projects/{project['id']}/members",
        json=payload,
        headers=owner_headers,
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_non_member_cannot_access_project(client: AsyncClient) -> None:
    _, owner_headers = await create_user(
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

    response = await client.get(
        f"/api/v1/projects/{project['id']}",
        headers=outsider_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_can_change_and_remove_member(client: AsyncClient) -> None:
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
    await client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"user_id": member["id"], "role": "Viewer"},
        headers=owner_headers,
    )

    updated = await client.patch(
        f"/api/v1/projects/{project['id']}/members/{member['id']}",
        json={"role": "Developer"},
        headers=owner_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "Developer"

    removed = await client.delete(
        f"/api/v1/projects/{project['id']}/members/{member['id']}",
        headers=owner_headers,
    )
    assert removed.status_code == 204
    denied = await client.get(
        f"/api/v1/projects/{project['id']}",
        headers=member_headers,
    )
    assert denied.status_code == 403
