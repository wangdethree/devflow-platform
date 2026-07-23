"""项目与项目成员请求、响应 Schema。"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ProjectStatus(StrEnum):
    """当前版本支持的项目状态。"""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ProjectRoleName(StrEnum):
    """固定项目角色名称。"""

    OWNER = "Owner"
    DEVELOPER = "Developer"
    VIEWER = "Viewer"


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    page: int
    page_size: int
    total: int


class ProjectMemberCreateRequest(BaseModel):
    user_id: int = Field(gt=0)
    role: ProjectRoleName


class ProjectMemberUpdateRequest(BaseModel):
    role: ProjectRoleName


class ProjectMemberResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    username: str
    email: str
    role: str
    joined_at: datetime


class ProjectMemberListResponse(BaseModel):
    items: list[ProjectMemberResponse]
