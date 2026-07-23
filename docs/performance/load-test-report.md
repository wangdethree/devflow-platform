# DevFlow 本地性能基线报告

本报告保存可复现的本机短时基线，用于发现明显错误、比较后续版本，不代表生产容量或 SLA。

## 测试环境

- 时间：2026-07-23；
- 主机：macOS 15.7.7，x86_64；
- Docker Engine：29.5.3；
- 部署：Nginx → 单 Uvicorn API 进程 → MySQL 8.0；
- API 容器：未显式限制 CPU 或内存；
- 并发：20；
- 持续时间：15 秒；
- 超时：5 秒；
- 客户端：`scripts/run_load_test.py`，HTTP keep-alive，显式禁用开发机代理。

## 结果

| 场景 | 请求 | 成功率 | 吞吐量 | P50 | P95 | P99 | 最大 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 数据库健康读 | 2102 | 100% | 139.31 req/s | 71.29 ms | 492.99 ms | 1355.83 ms | 1710.74 ms |
| 认证业务读 | 2042 | 100% | 135.35 req/s | 123.66 ms | 295.66 ms | 485.47 ms | 876.01 ms |

数据库健康读每次执行 `SELECT 1`。认证业务读在同一登录会话下交替访问 `/api/v1/users/me` 与 `/api/v1/issues`，会经过 JWT 验证、服务端会话检查、用户状态读取以及 Issue 查询。

原始结果：

- `load-test-baseline.json`
- `load-test-authenticated.json`

## 复现

公共数据库读：

```bash
backend/.venv/bin/python scripts/run_load_test.py \
  --base-url http://127.0.0.1:8088 \
  --concurrency 20 \
  --duration 15 \
  --output docs/performance/load-test-baseline.json
```

认证读使用专门的测试账号：

```bash
backend/.venv/bin/python scripts/run_load_test.py \
  --base-url http://127.0.0.1:8088 \
  --concurrency 20 \
  --duration 15 \
  --email loadtest@example.com \
  --password '替换为测试密码' \
  --output docs/performance/load-test-authenticated.json
```

## 如何解释

这两组数据证明在当前本机 Docker 环境、单进程和 20 并发的短时读场景中没有请求错误，并提供了可重复比较的延迟基线。它们不能证明：

- 线上也能达到相同吞吐量；
- 系统可承受长期或更高并发；
- 写接口、锁竞争和 Celery 已完成容量验证；
- 当前 P95/P99 已达到某个业务 SLA。

下一轮应分别测试 10/20/50/100 并发，延长至 10～30 分钟，加入 Issue 创建、更新冲突和 Review 决策场景，同时记录 CPU、内存、连接池等待和 MySQL 慢查询。
