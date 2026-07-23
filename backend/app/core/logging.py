"""应用日志与 HTTP 请求追踪配置。"""

import logging
import time
import uuid

from fastapi import FastAPI, Request, Response


access_logger = logging.getLogger("devflow.access")


def configure_logging() -> None:
    """初始化简洁的控制台日志格式。"""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def register_request_logging(app: FastAPI) -> None:
    """记录请求方法、路径、状态码、耗时和 Request ID。"""

    @app.middleware("http")
    async def request_logging_middleware(
        request: Request,
        call_next,
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            access_logger.exception(
                "未处理请求异常 method=%s path=%s request_id=%s",
                request.method,
                request.url.path,
                request_id,
            )
            raise

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        response.headers["X-Request-ID"] = request_id
        access_logger.info(
            "method=%s path=%s status=%s elapsed_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response
