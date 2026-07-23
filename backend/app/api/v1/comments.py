"""Issue 评论接口。"""

from fastapi import APIRouter, Response, status

from app.api.dependencies import CurrentUser
from app.database.dependencies import DatabaseSession
from app.schemas.comment import (
    CommentCreateRequest,
    CommentListResponse,
    CommentResponse,
    CommentUpdateRequest,
)
from app.services.comment_service import CommentService


router = APIRouter(tags=["评论"])


@router.post(
    "/issues/{issue_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="发表评论",
)
async def create_comment(
    issue_id: int,
    payload: CommentCreateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> CommentResponse:
    return await CommentService(session).create_comment(
        issue_id,
        current_user,
        payload.content,
    )


@router.get(
    "/issues/{issue_id}/comments",
    response_model=CommentListResponse,
    summary="查询评论列表",
)
async def list_comments(
    issue_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> CommentListResponse:
    items = await CommentService(session).list_comments(issue_id, current_user)
    return CommentListResponse(items=items)


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    summary="修改自己的评论",
)
async def update_comment(
    comment_id: int,
    payload: CommentUpdateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> CommentResponse:
    return await CommentService(session).update_comment(
        comment_id,
        current_user,
        payload.content,
    )


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除自己的评论",
)
async def delete_comment(
    comment_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Response:
    await CommentService(session).delete_comment(comment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
