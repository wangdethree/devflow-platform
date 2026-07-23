"""用户请求、响应和管理 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    """不包含密码哈希的用户公开响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    avatar: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdateRequest(BaseModel):
    """当前用户资料更新请求。"""

    username: str | None = Field(default=None, min_length=2, max_length=50)
    email: EmailStr | None = None
    avatar: str | None = Field(default=None, max_length=255)


class UserStatusRequest(BaseModel):
    """管理员启用或禁用用户请求。"""

    is_active: bool


class UserListResponse(BaseModel):
    """管理员用户分页列表。"""

    items: list[UserResponse]
    page: int
    page_size: int
    total: int


class PermissionListResponse(BaseModel):
    """当前用户拥有的系统权限编码。"""

    permissions: list[str]
