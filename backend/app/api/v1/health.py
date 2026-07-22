"""系统健康检查接口。

用于确认 API 服务是否正常运行。
后续可扩展数据库、Redis 等基础设施的健康状态检查。
"""

from fastapi import APIRouter


# 当前模块内所有接口统一使用 /health 前缀。
router = APIRouter(
    prefix="/health",
    tags=["系统"],
)


@router.get(
    "",
    summary="健康检查",
)
async def health_check() -> dict[str, str]:
    """返回 API 服务的基础运行状态。"""

    return {
        "status": "ok",
        "service": "devflow-api",
    }