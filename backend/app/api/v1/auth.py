"""注册和 JWT 登录接口。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database.dependencies import DatabaseSession
from app.core.rate_limit import check_login_rate_limit
from app.schemas.auth import RegisterRequest, TokenResponse
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
    return await AuthService(session).login(form.username, form.password)
