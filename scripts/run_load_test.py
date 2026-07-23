#!/usr/bin/env python3
"""无额外压测框架依赖的 DevFlow 异步 HTTP 基线测试。"""

import argparse
import asyncio
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
import statistics
import time

import httpx


def percentile(values: list[float], ratio: float) -> float:
    """使用最近秩计算百分位，结果单位为毫秒。"""

    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = max(0, min(len(ordered) - 1, int(len(ordered) * ratio + 0.999) - 1))
    return ordered[index]


async def execute(args: argparse.Namespace) -> dict:
    latencies: list[float] = []
    status_codes: Counter[str] = Counter()
    access_token = args.access_token
    if args.email:
        async with httpx.AsyncClient(
            base_url=args.base_url.rstrip("/"),
            timeout=args.timeout,
            trust_env=False,
        ) as login_client:
            login_response = await login_client.post(
                "/api/v1/auth/login",
                data={"username": args.email, "password": args.password},
            )
            login_response.raise_for_status()
            access_token = login_response.json()["access_token"]
    headers = (
        {"Authorization": f"Bearer {access_token}"}
        if access_token
        else {}
    )
    endpoints = (
        ["/api/v1/users/me", "/api/v1/issues?page=1&page_size=20"]
        if access_token
        else ["/api/v1/health/database"]
    )
    limits = httpx.Limits(
        max_connections=args.concurrency,
        max_keepalive_connections=args.concurrency,
    )

    async with httpx.AsyncClient(
        base_url=args.base_url.rstrip("/"),
        headers=headers,
        limits=limits,
        timeout=args.timeout,
        # 本地基线测试不能继承开发机 HTTP_PROXY，否则请求可能绕过本机 Nginx。
        trust_env=False,
    ) as client:
        started_at = time.perf_counter()
        deadline = started_at + args.duration

        async def worker(worker_id: int) -> None:
            request_index = worker_id
            while time.perf_counter() < deadline:
                endpoint = endpoints[request_index % len(endpoints)]
                started_at = time.perf_counter()
                try:
                    response = await client.get(endpoint)
                    status_codes[str(response.status_code)] += 1
                except httpx.HTTPError:
                    status_codes["transport_error"] += 1
                latencies.append((time.perf_counter() - started_at) * 1000)
                request_index += 1

        await asyncio.gather(
            *(worker(worker_id) for worker_id in range(args.concurrency))
        )
        elapsed_seconds = time.perf_counter() - started_at

    total = len(latencies)
    succeeded = sum(
        count
        for code, count in status_codes.items()
        if code.isdigit() and 200 <= int(code) < 400
    )
    return {
        "measured_at": datetime.now(UTC).isoformat(),
        "base_url": args.base_url,
        "scenario": "authenticated_read" if access_token else "database_health",
        "configuration": {
            "concurrency": args.concurrency,
            "requested_duration_seconds": args.duration,
            "timeout_seconds": args.timeout,
        },
        "result": {
            "elapsed_seconds": round(elapsed_seconds, 3),
            "requests": total,
            "succeeded": succeeded,
            "failed": total - succeeded,
            "requests_per_second": round(total / elapsed_seconds, 2),
            "status_codes": dict(status_codes),
            "latency_ms": {
                "min": round(min(latencies, default=0), 2),
                "mean": round(statistics.fmean(latencies) if latencies else 0, 2),
                "p50": round(percentile(latencies, 0.50), 2),
                "p95": round(percentile(latencies, 0.95), 2),
                "p99": round(percentile(latencies, 0.99), 2),
                "max": round(max(latencies, default=0), 2),
            },
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DevFlow 可复现 HTTP 基线压测")
    parser.add_argument("--base-url", default="http://127.0.0.1:8088")
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--duration", type=float, default=15)
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument(
        "--access-token",
        help="提供时交替压测 /users/me 与 /issues，否则压测数据库健康接口",
    )
    parser.add_argument("--email", help="通过邮箱密码登录后执行认证读场景")
    parser.add_argument("--password", help="仅与 --email 同时使用")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.concurrency < 1 or args.duration <= 0 or args.timeout <= 0:
        parser.error("concurrency、duration 和 timeout 必须大于 0")
    if bool(args.email) != bool(args.password):
        parser.error("--email 和 --password 必须同时提供")
    if args.access_token and args.email:
        parser.error("--access-token 与 --email/--password 不能同时使用")
    return args


def main() -> None:
    args = parse_args()
    result = asyncio.run(execute(args))
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
