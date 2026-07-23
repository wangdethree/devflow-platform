"""Issue 请求、筛选、状态和分页响应 Schema。"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class IssueType(StrEnum):
    BUG = "BUG"
    FEATURE = "FEATURE"
    TASK = "TASK"


class IssuePriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"


class IssueCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    type: IssueType = IssueType.TASK
    priority: IssuePriority = IssuePriority.MEDIUM
    assignee_id: int | None = Field(default=None, gt=0)


class IssueUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    type: IssueType | None = None
    priority: IssuePriority | None = None
    assignee_id: int | None = Field(default=None, gt=0)


class IssueStatusRequest(BaseModel):
    status: IssueStatus


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    creator_id: int
    assignee_id: int | None
    title: str
    description: str | None
    type: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime


class IssueListResponse(BaseModel):
    items: list[IssueResponse]
    page: int
    page_size: int
    total: int
