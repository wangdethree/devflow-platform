"""评论作者权限与 Review 状态联动集成测试。"""

import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.database.session import AsyncSessionLocal
from app.models.notification import Notification
from app.tests.test_issues import add_member, create_issue
from app.tests.test_projects import create_project, create_user


@pytest.mark.asyncio
async def test_user_cannot_modify_another_users_comment(
    client: AsyncClient,
) -> None:
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
    issue = await create_issue(
        client,
        project_id=project["id"],
        headers=owner_headers,
    )
    comment = await client.post(
        f"/api/v1/issues/{issue['id']}/comments",
        json={"content": "Owner 的评论"},
        headers=owner_headers,
    )

    response = await client.patch(
        f"/api/v1/comments/{comment.json()['id']}",
        json={"content": "越权修改"},
        headers=developer_headers,
    )
    assert response.status_code == 403


async def prepare_review(
    client: AsyncClient,
) -> tuple[dict, dict[str, str], dict[str, str]]:
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
    reviewer, reviewer_headers = await create_user(
        client,
        username="reviewer",
        email="reviewer@example.com",
    )
    project = await create_project(client, owner_headers)
    for user in (developer, reviewer):
        await add_member(
            client,
            project_id=project["id"],
            owner_headers=owner_headers,
            user_id=user["id"],
            role="Developer",
        )
    issue = await create_issue(
        client,
        project_id=project["id"],
        headers=developer_headers,
        assignee_id=developer["id"],
    )
    transition = await client.patch(
        f"/api/v1/issues/{issue['id']}/status",
        json={"status": "IN_PROGRESS", "version": issue["version"]},
        headers=developer_headers,
    )
    assert transition.status_code == 200
    review = await client.post(
        f"/api/v1/issues/{issue['id']}/reviews",
        json={
            "reviewer_id": reviewer["id"],
            "issue_version": transition.json()["version"],
        },
        headers=developer_headers,
    )
    assert review.status_code == 201
    return review.json(), developer_headers, reviewer_headers


@pytest.mark.asyncio
async def test_review_approval_atomically_completes_issue(
    client: AsyncClient,
) -> None:
    review, requester_headers, reviewer_headers = await prepare_review(client)

    response = await client.patch(
        f"/api/v1/reviews/{review['id']}",
        json={"status": "APPROVED", "comment": "审核通过"},
        headers=reviewer_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"

    issue_response = await client.get(
        f"/api/v1/issues/{review['issue_id']}",
        headers=requester_headers,
    )
    assert issue_response.json()["status"] == "DONE"

    duplicate = await client.patch(
        f"/api/v1/reviews/{review['id']}",
        json={"status": "REJECTED", "comment": "重复处理"},
        headers=reviewer_headers,
    )
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_review_rejection_returns_issue_to_in_progress(
    client: AsyncClient,
) -> None:
    review, requester_headers, reviewer_headers = await prepare_review(client)

    response = await client.patch(
        f"/api/v1/reviews/{review['id']}",
        json={"status": "REJECTED", "comment": "需要修改"},
        headers=reviewer_headers,
    )
    assert response.status_code == 200

    issue_response = await client.get(
        f"/api/v1/issues/{review['issue_id']}",
        headers=requester_headers,
    )
    assert issue_response.json()["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_concurrent_same_review_decision_is_idempotent(
    client: AsyncClient,
) -> None:
    review, _, reviewer_headers = await prepare_review(client)

    async def approve():
        return await client.patch(
            f"/api/v1/reviews/{review['id']}",
            json={"status": "APPROVED", "comment": "并发审批"},
            headers=reviewer_headers,
        )

    first, second = await asyncio.gather(approve(), approve())
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == second.json()["status"] == "APPROVED"

    async with AsyncSessionLocal() as session:
        notification_count = await session.scalar(
            select(func.count(Notification.id)).where(
                Notification.target_type == "review",
                Notification.target_id == review["id"],
                Notification.type == "REVIEW_APPROVED",
            )
        )
    assert notification_count == 1
