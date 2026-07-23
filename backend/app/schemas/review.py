"""Review 发起、处理与响应 Schema。"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReviewStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReviewCreateRequest(BaseModel):
    reviewer_id: int = Field(gt=0)


class ReviewDecisionRequest(BaseModel):
    status: ReviewStatus
    comment: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_decision(self):
        if self.status == ReviewStatus.PENDING:
            raise ValueError("不能将 Review 重新设置为 PENDING")
        return self


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_id: int
    requester_id: int
    reviewer_id: int
    status: str
    comment: str | None
    created_at: datetime


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
