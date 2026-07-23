"""认证接口请求与响应 Schema。"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """用户注册请求。"""

    username: str = Field(min_length=2, max_length=50, description="用户名")
    email: EmailStr = Field(description="唯一邮箱")
    password: str = Field(min_length=8, max_length=128, description="登录密码")


class TokenResponse(BaseModel):
    """JWT 登录响应。"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="有效期，单位为秒")
