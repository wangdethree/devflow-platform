"""DevFlow FastAPI 应用入口。

负责创建应用实例、加载基础配置并注册顶层路由。
具体业务逻辑应放在对应的 API、Service 和 Repository 层。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, register_request_logging
from app.core.cache import close_redis
from app.database.session import engine
from app.core.metrics import register_database_metrics


configure_logging()
register_database_metrics(engine)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用退出时主动释放数据库连接池。"""

    yield
    await close_redis()
    await engine.dispose()


# 创建 FastAPI 应用实例。
app = FastAPI(
    title=settings.app_name,
    description="DevFlow 企业研发协作平台后端 API",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

register_exception_handlers(app)
register_request_logging(app)

# 注册 API v1 总路由，并统一添加版本前缀。
app.include_router(
    api_router,
    prefix=settings.api_v1_prefix,
)


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """暴露 Prometheus 文本格式指标。"""

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get(
    "/",
    tags=["系统"],
    summary="服务首页",
)
async def root() -> dict[str, str]:
    """返回应用名称和当前运行环境。"""

    return {
        "message": f"{settings.app_name} API is running",
        "environment": settings.environment,
    }
