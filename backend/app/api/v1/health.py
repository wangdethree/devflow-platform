"""系统健康检查接口。

用于检查 API 服务及数据库等基础设施是否正常运行。
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.dependencies import DatabaseSession


router = APIRouter(
    prefix="/health",
    tags=["系统"],
)


@router.get(
    "",
    summary="服务健康检查",
)
async def health_check() -> dict[str, str]:
    """返回 DevFlow API 的基础运行状态。"""

    return {
        "status": "ok",
        "service": "devflow-api",
    }


@router.get(
    "/database",
    summary="数据库健康检查",
)
async def database_health_check(
    session: DatabaseSession,
) -> dict[str, str]:
    """检查应用是否能够正常连接 MySQL。"""

    try:
        # 执行最小查询，验证数据库连接和 SQL 执行能力。
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        # 对外隐藏底层数据库异常，避免泄露连接信息。
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable",
        ) from exc

    return {
        "status": "ok",
        "database": "mysql",
    }