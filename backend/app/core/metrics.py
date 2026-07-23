"""Prometheus HTTP、数据库与核心业务指标。"""

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine


HTTP_REQUESTS_TOTAL = Counter(
    "devflow_http_requests_total",
    "HTTP 请求总数",
    ("method", "route", "status"),
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "devflow_http_request_duration_seconds",
    "HTTP 请求耗时",
    ("method", "route"),
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "devflow_http_requests_in_progress",
    "正在处理的 HTTP 请求数",
    ("method",),
)
DB_QUERY_DURATION_SECONDS = Histogram(
    "devflow_db_query_duration_seconds",
    "数据库查询耗时",
    ("operation",),
)
DB_QUERY_ERRORS_TOTAL = Counter(
    "devflow_db_query_errors_total",
    "数据库查询错误总数",
    ("operation",),
)
AUTH_SESSION_EVENTS_TOTAL = Counter(
    "devflow_auth_session_events_total",
    "认证会话事件总数",
    ("event",),
)
ISSUE_CONFLICTS_TOTAL = Counter(
    "devflow_issue_conflicts_total",
    "Issue 乐观锁冲突总数",
    ("operation",),
)
REVIEW_DECISIONS_TOTAL = Counter(
    "devflow_review_decisions_total",
    "Review 审批结果与幂等命中总数",
    ("result",),
)


def sql_operation(statement: str | None) -> str:
    """将 SQL 归一化为低基数操作标签。"""

    operation = (statement or "").lstrip().split(maxsplit=1)
    candidate = operation[0].upper() if operation else "OTHER"
    return (
        candidate
        if candidate in {"SELECT", "INSERT", "UPDATE", "DELETE", "SHOW"}
        else "OTHER"
    )


def register_database_metrics(engine: AsyncEngine) -> None:
    """监听 SQLAlchemy 引擎事件，采集真实数据库操作耗时和错误。"""

    sync_engine = engine.sync_engine
    if getattr(sync_engine, "_devflow_metrics_registered", False):
        return
    sync_engine._devflow_metrics_registered = True

    @event.listens_for(sync_engine, "before_cursor_execute")
    def before_cursor_execute(
        _connection: Any,
        _cursor: Any,
        statement: str,
        _parameters: Any,
        context: Any,
        _executemany: bool,
    ) -> None:
        context._devflow_query_started_at = time.perf_counter()
        context._devflow_query_operation = sql_operation(statement)

    @event.listens_for(sync_engine, "after_cursor_execute")
    def after_cursor_execute(
        _connection: Any,
        _cursor: Any,
        _statement: str,
        _parameters: Any,
        context: Any,
        _executemany: bool,
    ) -> None:
        started_at = getattr(context, "_devflow_query_started_at", None)
        if started_at is not None:
            DB_QUERY_DURATION_SECONDS.labels(
                getattr(context, "_devflow_query_operation", "OTHER")
            ).observe(time.perf_counter() - started_at)

    @event.listens_for(sync_engine, "handle_error")
    def handle_error(exception_context: Any) -> None:
        execution_context = exception_context.execution_context
        operation = getattr(
            execution_context,
            "_devflow_query_operation",
            sql_operation(exception_context.statement),
        )
        DB_QUERY_ERRORS_TOTAL.labels(operation).inc()
