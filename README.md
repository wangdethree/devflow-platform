# DevFlow 企业研发协作平台

DevFlow 是一个面向研发团队协作场景的前后端分离平台。系统以项目和 Issue 为核心，覆盖用户认证、双层权限、成员管理、任务流转、评论、Review 和站内通知，并提供 Vue 3 管理界面、MySQL 迁移、Redis 缓存、Celery 异步分发、自动化测试和 Docker 后端部署。

## 核心业务

```text
注册/登录
  → 创建项目（创建者自动成为 Owner）
  → 添加 Developer / Viewer
  → 创建和分配 Issue
  → OPEN → IN_PROGRESS
  → 发起 Review（Issue 进入 REVIEW）
  → APPROVED → DONE / REJECTED → IN_PROGRESS
  → 生成站内通知并异步发布事件
```

- JWT Access/Refresh Token、令牌轮换、设备会话撤销与 Argon2 密码哈希；
- Admin/User 系统 RBAC；
- Owner/Developer/Viewer 项目级权限；
- 项目及 Owner 成员关系原子创建；
- Issue 类型、优先级、筛选、关键词和分页；
- 受控 Issue 状态机；
- Issue 版本号乐观锁，防止并发请求静默覆盖更新；
- 评论作者修改和删除权限；
- Review 与 Issue 状态同事务联动及并发重复审批幂等保护；
- 所属用户隔离的站内通知；
- Redis 权限缓存和登录限流，故障时回退核心业务；
- Celery 负责已落库通知的可重试 Redis Channel 发布；
- JSON 结构化日志、Request ID、Prometheus HTTP/数据库/业务指标；
- 可复现异步压测脚本及真实 Docker 基线结果。

## 技术栈

| 分类 | 技术 |
| --- | --- |
| Web | Python 3.11、FastAPI、Uvicorn、Pydantic v2 |
| Database | MySQL 8.0、SQLAlchemy 2.0 Async、asyncmy |
| Migration | Alembic |
| Security | PyJWT、pwdlib Argon2、OAuth2 Bearer |
| Cache/Task | Redis、Celery |
| Observability | JSON Logs、Prometheus |
| Test | Pytest、pytest-asyncio、HTTPX、真实隔离 MySQL 测试库 |
| Deploy | Docker、Docker Compose、Nginx |
| Frontend | Vue 3、Vite、TypeScript、Vue Router、Pinia、Element Plus、Axios |

## 系统架构

代码调用方向固定为：

```text
HTTP → API → Service → Repository → AsyncSession → MySQL
```

- API：参数校验、依赖注入和响应；
- Service：权限、状态流转、事务与多仓库编排；
- Repository：查询和持久化，不提交事务；
- Model：13 张正式业务表的 ORM 映射；
- Schema：隔离 API 契约与内部持久化字段。

Redis 和 Celery 属于可降级增强能力。MySQL 通知写入与主业务处于同一事务；事务提交后才尽力投递 Celery 任务，因此 Broker 故障不会造成已提交主业务回滚。

## 目录结构

```text
backend/
├── alembic/                 # 数据库迁移
├── app/
│   ├── api/v1/              # HTTP API
│   ├── commands/            # 幂等 seed 命令
│   ├── core/                # 配置、安全、异常、日志、指标、缓存
│   ├── database/            # AsyncEngine、AsyncSession、依赖
│   ├── models/              # SQLAlchemy ORM
│   ├── repositories/        # 数据访问
│   ├── schemas/             # Pydantic 请求/响应
│   ├── services/            # 业务规则与事务
│   ├── tasks/               # Celery 任务
│   └── tests/               # 自动化测试
├── Dockerfile
└── requirements.txt
frontend/
├── src/
│   ├── api/                  # Axios 客户端与领域 API
│   ├── components/           # 通用表单和展示组件
│   ├── layouts/              # 登录与主应用布局
│   ├── router/               # 路由及权限守卫
│   ├── stores/               # Auth、通知未读状态
│   ├── types/                # API TypeScript 类型
│   └── views/                # 业务页面
├── README.md
└── package.json
docker/
├── compose.dev.yml          # 本机开发 MySQL/Redis
├── compose.yml              # 完整容器栈
├── nginx.conf
└── prometheus.yml
docs/development/            # 决策、学习、调试和面试文档
docs/performance/            # 压测方法、报告与原始结果
scripts/                     # 测试库准备和异步压测脚本
```

## 环境要求

- Python 3.11；
- pip；
- Docker Desktop 与 Docker Compose；
- 可用端口：开发模式 `3306`、`6379`；完整容器模式默认 `8088`、`9090`。

## 本地启动

1. 创建虚拟环境并安装依赖：

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

2. 创建本地配置：

```bash
cp .env.example .env
```

必须修改 `MYSQL_ROOT_PASSWORD`、`MYSQL_PASSWORD` 和 `JWT_SECRET_KEY`。生产环境应使用至少 32 字节随机 JWT 密钥，并设置 `DEBUG=false`。

3. 启动开发基础设施：

```bash
cd ..
docker compose -f docker/compose.dev.yml up -d mysql redis
```

4. 迁移和初始化：

```bash
cd backend
.venv/bin/alembic upgrade head
.venv/bin/python -m app.commands.seed
```

5. 启动 API 和可选 Worker：

```bash
.venv/bin/uvicorn app.main:app --reload
.venv/bin/celery -A app.tasks.celery_app:celery_app worker --loglevel=INFO
```

API 地址为 `http://127.0.0.1:8000`。

6. 启动 Vue 前端：

```bash
cd ../frontend
npm install
cp .env.example .env.local
npm run dev
```

前端地址为 `http://127.0.0.1:5173`。详细说明见 `frontend/README.md`。

## 完整 Docker 启动

先准备 `backend/.env`，然后执行：

```bash
docker compose -p devflow-full -f docker/compose.yml up -d --build
docker compose -p devflow-full -f docker/compose.yml ps
```

默认入口：

- API：`http://127.0.0.1:8088/api/v1`
- Swagger：`http://127.0.0.1:8088/docs`
- ReDoc：`http://127.0.0.1:8088/redoc`
- Metrics：`http://127.0.0.1:8088/metrics`
- Prometheus：`http://127.0.0.1:9090`

如 8088 已占用，可在仓库根目录 `.env` 设置：

```dotenv
DEVFLOW_HTTP_PORT=18080
```

停止容器但保留数据：

```bash
docker compose -p devflow-full -f docker/compose.yml down
```

## 环境变量

| 变量 | 作用 |
| --- | --- |
| `ENVIRONMENT` | `local`、`test` 或 `production` |
| `DEBUG` | SQL 和应用调试开关 |
| `LOG_LEVEL` / `LOG_FORMAT` | 日志级别及 `json`/`plain` 格式 |
| `API_V1_PREFIX` | 默认 `/api/v1` |
| `CORS_ORIGINS` | 逗号分隔的可信前端来源 |
| `JWT_SECRET_KEY` | JWT 签名密钥 |
| `JWT_ALGORITHM` | 默认 `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 有效期 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 与设备会话有效期 |
| `MYSQL_*` | MySQL 初始化及连接参数 |
| `REDIS_URL` | 权限缓存和登录限流 |
| `CELERY_BROKER_URL` | Celery Broker |
| `CELERY_RESULT_BACKEND` | Celery 结果后端 |
| `PROMETHEUS_PORT` | Prometheus 主机端口，默认 `9090` |

`.env` 已被 Git 忽略，仓库只提交安全占位值。

## Alembic

所有表结构都通过迁移管理，应用启动代码不会调用 `create_all()`。

```bash
cd backend
.venv/bin/alembic current
.venv/bin/alembic heads
.venv/bin/alembic upgrade head
.venv/bin/alembic downgrade -1
.venv/bin/alembic check
```

迁移链：

1. `58e9af26beed`：用户、角色、权限及关联表；
2. `066390522b4a`：系统角色名称唯一约束；
3. `f5096068578d`：项目、项目角色和项目成员；
4. `1429d98ec07c`：Issue、评论和 Review；
5. `759adf3f87a8`：站内通知；
6. `9d31f0b7a8c2`：认证设备会话和 Refresh Token 轮换；
7. `b741c6d2e903`：Issue 乐观锁版本号。

## 初始化数据

幂等初始化 Admin/User 系统角色、系统权限及 Owner/Developer/Viewer 项目角色：

```bash
cd backend
.venv/bin/python -m app.commands.seed
```

可选创建管理员，不在代码或文档中保存真实密码：

```bash
.venv/bin/python -m app.commands.seed \
  --admin-email admin@example.com \
  --admin-username admin \
  --admin-password '请替换为安全密码'
```

重复执行不会生成重复角色、权限或管理员关联。

## 测试

测试使用独立 MySQL 数据库，不读取开发库随机数据：

```bash
chmod +x scripts/create_test_database.sh
./scripts/create_test_database.sh
cd backend
.venv/bin/pytest -q
```

当前共 31 项后端自动化测试，覆盖认证、Refresh Token 轮换与撤销、RBAC、项目事务、项目成员权限、Issue 状态机与并发冲突、筛选分页、评论作者权限、Review 状态联动与并发幂等、通知归属、CORS、Prometheus 指标及 Alembic head。前端另使用 Vitest 做基础工具测试，并以 `vue-tsc` 和 Vite 生产构建作为类型与编译门禁。

## 可观测性与压测

API 默认输出单行 JSON 日志，包含时间、级别、logger、Request ID、路由模板、状态码和耗时。`/metrics` 暴露：

- HTTP 请求量、耗时直方图和进行中请求；
- SQL 操作耗时及错误计数；
- 登录会话、Refresh Token 重放、Issue 冲突和 Review 幂等事件。

执行可复现基线测试：

```bash
backend/.venv/bin/python scripts/run_load_test.py \
  --base-url http://127.0.0.1:8088 \
  --concurrency 20 \
  --duration 15
```

认证读场景可额外提供 `--email` 和 `--password`。实际环境、原始 JSON 和结果解释见 `docs/performance/load-test-report.md`，这些本机短时数据不能等同于生产容量。

## API 文档与认证

启动后打开 `/docs`。先调用 `POST /api/v1/auth/register`，再点击 Swagger 右上角 **Authorize**。OAuth2 表单的 `username` 字段填写用户邮箱，密码填写注册密码。

主要 API：

- `/api/v1/auth`：注册、登录、令牌轮换、当前/全部设备注销；
- `/api/v1/users`：个人资料、当前权限；
- `/api/v1/admin`：管理员用户管理；
- `/api/v1/projects`：项目和成员；
- `/api/v1/issues`：Issue 查询、更新、状态；
- `/api/v1/comments`：评论；
- `/api/v1/reviews`：Review；
- `/api/v1/notifications`：通知。

完整请求示例见 `docs/development/03-api-debug-guide.md`。

## 核心约束

- 系统角色与项目角色严格分离；
- 软删除仅用于用户、项目和 Issue；
- Developer 只修改自己创建或负责的 Issue；
- Viewer 只读；
- 主项目负责人不可被移除或降级；
- Issue 只能相邻状态流转；
- 修改、流转和删除 Issue 必须携带当前 `version`；
- Review 请求、结果与 Issue 状态保持同事务一致；
- 同一 Review 的相同重复决策幂等返回，不重复生成通知；
- 用户只能读取和修改自己的通知。

## 当前版本边界

已实现 Vue 前端与后端核心闭环、数据库通知、Redis/Celery 增强、会话撤销、并发控制、Prometheus 采集和后端容器化部署。未实现真实 Git 仓库托管、附件、标签、WebSocket 网关、邮件/短信通知、前端容器镜像、CI/CD 或微服务。评论当前为平级讨论，正式数据库设计没有回复树所需的 `parent_id`。

## 后续方向

- 增加权限变更后的 Redis 主动失效；
- 为通知事件接入 WebSocket 或邮件消费者；
- 增加 CI 中的临时 MySQL 服务与覆盖率报告；
- 增加审计日志与可恢复软删除管理；
- 增加多档并发、长稳和写场景压测，再依据证据调整进程数、连接池和索引。

## 进一步阅读

- `docs/development/implementation-decisions.md`
- `docs/development/02-code-learning-guide.md`
- `docs/development/03-api-debug-guide.md`
- `docs/development/04-resume-interview-guide.md`
- `docs/development/06-frontend-learning-guide.md`
- `docs/development/07-frontend-api-mapping.md`
