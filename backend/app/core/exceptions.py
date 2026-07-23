"""业务异常与全局异常响应。

Service 层只抛出与 HTTP 无关的业务异常，由本模块统一转换状态码，
避免把数据库细节、内部路径或堆栈信息返回给客户端。
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class BusinessError(Exception):
    """所有可预期业务异常的基类。"""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "BUSINESS_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthenticationError(BusinessError):
    """身份凭证缺失、无效或账号不可用。"""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "AUTHENTICATION_FAILED"


class PermissionDeniedError(BusinessError):
    """当前用户没有执行目标操作的权限。"""

    status_code = status.HTTP_403_FORBIDDEN
    code = "PERMISSION_DENIED"


class ResourceNotFoundError(BusinessError):
    """业务资源不存在或已经退出正常业务范围。"""

    status_code = status.HTTP_404_NOT_FOUND
    code = "RESOURCE_NOT_FOUND"


class ConflictError(BusinessError):
    """唯一资源或业务关系发生冲突。"""

    status_code = status.HTTP_409_CONFLICT
    code = "RESOURCE_CONFLICT"


class InvalidStateTransitionError(BusinessError):
    """业务对象状态不允许按目标方式流转。"""

    status_code = status.HTTP_409_CONFLICT
    code = "INVALID_STATE_TRANSITION"


def register_exception_handlers(app: FastAPI) -> None:
    """注册业务异常、数据库异常和未预期异常处理器。"""

    @app.exception_handler(BusinessError)
    async def handle_business_error(
        request: Request,
        exc: BusinessError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", None),
            },
            headers=(
                {"WWW-Authenticate": "Bearer"}
                if isinstance(exc, AuthenticationError)
                else None
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(
        request: Request,
        exc: SQLAlchemyError,
    ) -> JSONResponse:
        logger.exception(
            "数据库操作失败 request_id=%s",
            getattr(request.state, "request_id", "-"),
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "code": "DATABASE_UNAVAILABLE",
                "message": "数据库服务暂时不可用",
                "request_id": getattr(request.state, "request_id", None),
            },
        )
