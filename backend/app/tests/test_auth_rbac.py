"""用户认证、个人资料和系统 RBAC 集成测试。"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.services.seed_service import seed_admin


REGISTER_PAYLOAD = {
    "username": "developer",
    "email": "developer@example.com",
    "password": "StrongPass123!",
}


async def register(client: AsyncClient) -> dict:
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    return response.json()


async def login(
    client: AsyncClient,
    *,
    email: str = REGISTER_PAYLOAD["email"],
    password: str = REGISTER_PAYLOAD["password"],
) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_register_assigns_user_role_without_password_hash(
    client: AsyncClient,
) -> None:
    body = await register(client)

    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert "password_hash" not in body

    token = await login(client)
    response = await client.get(
        "/api/v1/users/me/permissions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["permissions"] == ["project:create"]


@pytest.mark.asyncio
async def test_duplicate_email_registration(client: AsyncClient) -> None:
    await register(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={**REGISTER_PAYLOAD, "username": "another"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "RESOURCE_CONFLICT"


@pytest.mark.asyncio
async def test_login_with_wrong_password(client: AsyncClient) -> None:
    await register(client)
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": REGISTER_PAYLOAD["email"],
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_disabled_user_cannot_login(client: AsyncClient) -> None:
    await register(client)
    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(
                select(User).where(User.email == REGISTER_PAYLOAD["email"])
            )
        ).scalar_one()
        user.is_active = False
        await session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_requires_login(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_normal_user_cannot_access_admin_endpoint(
    client: AsyncClient,
) -> None:
    await register(client)
    token = await login(client)

    response = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_list_and_disable_users(client: AsyncClient) -> None:
    registered = await register(client)
    async with AsyncSessionLocal() as session:
        await seed_admin(
            session,
            email="admin@example.com",
            username="admin",
            password="AdminPass123!",
        )
    admin_token = await login(
        client,
        email="admin@example.com",
        password="AdminPass123!",
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    list_response = await client.get("/api/v1/admin/users", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 2

    status_response = await client.patch(
        f"/api/v1/admin/users/{registered['id']}/status",
        json={"is_active": False},
        headers=headers,
    )
    assert status_response.status_code == 200
    assert status_response.json()["is_active"] is False
