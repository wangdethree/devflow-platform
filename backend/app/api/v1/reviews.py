"""Issue Review 发起、历史和处理接口。"""

from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser
from app.database.dependencies import DatabaseSession
from app.schemas.review import (
    ReviewCreateRequest,
    ReviewDecisionRequest,
    ReviewListResponse,
    ReviewResponse,
)
from app.services.review_service import ReviewService


router = APIRouter(tags=["Review"])


@router.post(
    "/issues/{issue_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="发起 Review",
)
async def create_review(
    issue_id: int,
    payload: ReviewCreateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ReviewResponse:
    return await ReviewService(session).create_review(
        issue_id,
        current_user,
        payload.reviewer_id,
        payload.issue_version,
    )


@router.get(
    "/issues/{issue_id}/reviews",
    response_model=ReviewListResponse,
    summary="查询 Review 历史",
)
async def list_reviews(
    issue_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ReviewListResponse:
    items = await ReviewService(session).list_reviews(issue_id, current_user)
    return ReviewListResponse(items=items)


@router.patch(
    "/reviews/{review_id}",
    response_model=ReviewResponse,
    summary="处理 Review",
)
async def decide_review(
    review_id: int,
    payload: ReviewDecisionRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ReviewResponse:
    return await ReviewService(session).decide_review(
        review_id,
        current_user,
        payload,
    )
