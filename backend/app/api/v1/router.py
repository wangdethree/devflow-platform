"""API v1 路由聚合模块。

统一注册 v1 版本下的各业务路由，
避免 main.py 直接依赖所有业务接口模块。
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router


# API v1 的总路由对象。
api_router = APIRouter()

# 注册系统健康检查路由。
api_router.include_router(health_router)