"""结构化应用日志与 HTTP 请求追踪。"""

import contextvars
from datetime import UTC, datetime
import json
import logging
import time
import uuid

from fastapi import FastAPI, Request, Response

from app.core.config import settings
from app.core.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
)


request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="-",
)
access_logger = logging.getLogger("devflow.access")


class JsonFormatter(logging.Formatter):
    """输出适合日志平台采集的单行 JSON。"""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(
                record,
                "request_id",
                request_id_context.get(),
            ),
        }
        for field in ("method", "path", "route", "status", "elapsed_ms"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """按环境配置 JSON 或便于本地阅读的纯文本日志。"""

    handler = logging.StreamHandler()
    if settings.log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.log_level.upper())


def route_template(request: Request) -> str:
    """优先返回路由模板，避免实际资源 ID 造成指标标签高基数。"""

    route = request.scope.get("route")
    return getattr(route, "path", "unmatched")


def register_request_logging(app: FastAPI) -> None:
    """记录结构化访问日志，并采集请求计数、耗时和进行中数量。"""

    @app.middleware("http")
    async def request_logging_middleware(
        request: Request,
        call_next,
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        context_token = request_id_context.set(request_id)
        started_at = time.perf_counter()
        HTTP_REQUESTS_IN_PROGRESS.labels(request.method).inc()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            access_logger.exception(
                "未处理请求异常",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "request_id": request_id,
                },
            )
            raise
        finally:
            elapsed_seconds = time.perf_counter() - started_at
            route = route_template(request)
            HTTP_REQUESTS_IN_PROGRESS.labels(request.method).dec()
            HTTP_REQUESTS_TOTAL.labels(
                request.method,
                route,
                str(status_code),
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                request.method,
                route,
            ).observe(elapsed_seconds)
            access_logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "route": route,
                    "status": status_code,
                    "elapsed_ms": round(elapsed_seconds * 1000, 2),
                    "request_id": request_id,
                },
            )
            request_id_context.reset(context_token)
