"""Issue 创建、筛选、更新和状态流转接口。"""

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import CurrentUser
from app.database.dependencies import DatabaseSession
from app.schemas.issue import (
    IssueCreateRequest,
    IssueListResponse,
    IssuePriority,
    IssueResponse,
    IssueStatus,
    IssueStatusRequest,
    IssueType,
    IssueUpdateRequest,
)
from app.services.issue_service import IssueService


router = APIRouter(tags=["Issue"])


@router.post(
    "/projects/{project_id}/issues",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建 Issue",
)
async def create_issue(
    project_id: int,
    payload: IssueCreateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> IssueResponse:
    return await IssueService(session).create_issue(
        project_id,
        current_user,
        payload,
    )


@router.get("/issues", response_model=IssueListResponse, summary="筛选 Issue")
async def list_issues(
    current_user: CurrentUser,
    session: DatabaseSession,
    project_id: int | None = Query(default=None, gt=0),
    creator_id: int | None = Query(default=None, gt=0),
    assignee_id: int | None = Query(default=None, gt=0),
    status_filter: IssueStatus | None = Query(default=None, alias="status"),
    type_filter: IssueType | None = Query(default=None, alias="type"),
    priority: IssuePriority | None = None,
    keyword: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> IssueListResponse:
    items, total = await IssueService(session).list_issues(
        current_user,
        project_id=project_id,
        creator_id=creator_id,
        assignee_id=assignee_id,
        status=status_filter.value if status_filter else None,
        issue_type=type_filter.value if type_filter else None,
        priority=priority.value if priority else None,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return IssueListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/issues/{issue_id}",
    response_model=IssueResponse,
    summary="查询 Issue 详情",
)
async def get_issue(
    issue_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> IssueResponse:
    return await IssueService(session).get_issue(issue_id, current_user)


@router.patch(
    "/issues/{issue_id}",
    response_model=IssueResponse,
    summary="修改 Issue",
)
async def update_issue(
    issue_id: int,
    payload: IssueUpdateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> IssueResponse:
    return await IssueService(session).update_issue(
        issue_id,
        current_user,
        payload,
    )


@router.patch(
    "/issues/{issue_id}/status",
    response_model=IssueResponse,
    summary="流转 Issue 状态",
)
async def transition_issue_status(
    issue_id: int,
    payload: IssueStatusRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> IssueResponse:
    return await IssueService(session).transition_status(
        issue_id,
        current_user,
        payload.status,
    )


@router.delete(
    "/issues/{issue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="软删除 Issue",
)
async def delete_issue(
    issue_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Response:
    await IssueService(session).delete_issue(issue_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
