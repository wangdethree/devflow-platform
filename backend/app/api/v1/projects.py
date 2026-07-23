"""项目与成员管理 HTTP 接口。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import CurrentUser, require_permission
from app.core.permissions import PROJECT_CREATE
from app.database.dependencies import DatabaseSession
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectMemberCreateRequest,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    ProjectMemberUpdateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services.project_service import ProjectService


router = APIRouter(prefix="/projects", tags=["项目"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
)
async def create_project(
    payload: ProjectCreateRequest,
    session: DatabaseSession,
    current_user: Annotated[User, Depends(require_permission(PROJECT_CREATE))],
) -> ProjectResponse:
    return await ProjectService(session).create_project(current_user, payload)


@router.get("", response_model=ProjectListResponse, summary="查询参与项目")
async def list_projects(
    current_user: CurrentUser,
    session: DatabaseSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ProjectListResponse:
    items, total = await ProjectService(session).list_projects(
        current_user,
        page=page,
        page_size=page_size,
    )
    return ProjectListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="查询项目详情",
)
async def get_project(
    project_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ProjectResponse:
    return await ProjectService(session).get_project(project_id, current_user)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="修改项目",
)
async def update_project(
    project_id: int,
    payload: ProjectUpdateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ProjectResponse:
    return await ProjectService(session).update_project(
        project_id,
        current_user,
        payload,
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="软删除项目",
)
async def delete_project(
    project_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Response:
    await ProjectService(session).delete_project(project_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="添加项目成员",
)
async def add_member(
    project_id: int,
    payload: ProjectMemberCreateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ProjectMemberResponse:
    return await ProjectService(session).add_member(
        project_id,
        current_user,
        payload,
    )


@router.get(
    "/{project_id}/members",
    response_model=ProjectMemberListResponse,
    summary="查询项目成员",
)
async def list_members(
    project_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ProjectMemberListResponse:
    items = await ProjectService(session).list_members(project_id, current_user)
    return ProjectMemberListResponse(items=items)


@router.patch(
    "/{project_id}/members/{user_id}",
    response_model=ProjectMemberResponse,
    summary="修改成员角色",
)
async def update_member(
    project_id: int,
    user_id: int,
    payload: ProjectMemberUpdateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ProjectMemberResponse:
    return await ProjectService(session).update_member(
        project_id,
        user_id,
        current_user,
        payload,
    )


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="移除项目成员",
)
async def remove_member(
    project_id: int,
    user_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Response:
    await ProjectService(session).remove_member(
        project_id,
        user_id,
        current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
