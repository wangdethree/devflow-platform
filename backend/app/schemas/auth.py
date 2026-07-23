"""认证接口请求与响应 Schema。"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """用户注册请求。"""

    username: str = Field(min_length=2, max_length=50, description="用户名")
    email: EmailStr = Field(description="唯一邮箱")
    password: str = Field(min_length=8, max_length=128, description="登录密码")


class TokenResponse(BaseModel):
    """Access/Refresh Token 对及其有效期。"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access Token 有效期，单位为秒")
    refresh_expires_in: int = Field(description="Refresh Token 有效期，单位为秒")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求。"""

    refresh_token: str = Field(min_length=20)


class LogoutResponse(BaseModel):
    """注销结果。"""

    revoked_sessions: int = Field(ge=0)
