"""注册和 JWT 登录接口。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import CurrentAuth
from app.core.rate_limit import check_login_rate_limit
from app.database.dependencies import DatabaseSession
from app.schemas.auth import (
    LogoutResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="注册用户",
)
async def register(
    payload: RegisterRequest,
    session: DatabaseSession,
) -> UserResponse:
    """创建普通用户并分配默认 User 角色。"""

    return await AuthService(session).register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用户登录",
)
async def login(
    request: Request,
    session: DatabaseSession,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    """使用邮箱和密码登录；表单 username 字段填写邮箱。"""

    client_ip = request.client.host if request.client else "unknown"
    await check_login_rate_limit(f"{client_ip}:{form.username.lower()}")
    return await AuthService(session).login(
        form.username,
        form.password,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/refresh", response_model=TokenResponse, summary="轮换访问令牌")
async def refresh(
    payload: RefreshTokenRequest,
    session: DatabaseSession,
) -> TokenResponse:
    """使用一次性 Refresh Token 获取新令牌对。"""

    return await AuthService(session).refresh(payload.refresh_token)


@router.post("/logout", response_model=LogoutResponse, summary="注销当前设备")
async def logout(
    auth: CurrentAuth,
    session: DatabaseSession,
) -> LogoutResponse:
    """撤销当前 Access Token 绑定的设备会话。"""

    count = await AuthService(session).revoke_session(auth.claims)
    return LogoutResponse(revoked_sessions=count)


@router.post(
    "/logout-all",
    response_model=LogoutResponse,
    summary="注销全部设备",
)
async def logout_all(
    auth: CurrentAuth,
    session: DatabaseSession,
) -> LogoutResponse:
    """撤销当前用户全部设备会话。"""

    count = await AuthService(session).revoke_all_sessions(auth.user.id)
    return LogoutResponse(revoked_sessions=count)
