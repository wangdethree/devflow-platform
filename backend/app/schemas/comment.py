"""Issue 评论请求与响应 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentUpdateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_id: int
    user_id: int
    content: str
    created_at: datetime


class CommentListResponse(BaseModel):
    items: list[CommentResponse]
