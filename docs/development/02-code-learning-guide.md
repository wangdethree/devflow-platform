# DevFlow 代码学习指南

## 1. 推荐阅读顺序

1. `app/main.py`：应用如何创建、注册路由和释放资源；
2. `app/core/config.py`、`app/database/session.py`：配置与数据库基础设施；
3. `app/models/` 与 `alembic/versions/`：12 张表如何映射和演进；
4. `app/schemas/`：API 输入输出边界；
5. `app/api/v1/auth.py` → `services/auth_service.py` → 对应 Repository；
6. `app/api/dependencies.py` 与 `services/rbac_service.py`：认证和系统 RBAC；
7. 项目、Issue、评论、Review、通知各自按 API → Service → Repository 阅读；
8. `app/tests/`：通过业务场景反向验证理解；
9. `docker/compose.yml`：最后理解运行环境组合。

不要一开始逐文件顺序阅读。先抓住一条请求链，再横向对比其他模块的相同分层。

## 2. 从 HTTP 到 MySQL

以创建 Issue 为例：

```text
POST /api/v1/projects/{project_id}/issues
  → Pydantic 校验 IssueCreateRequest
  → get_current_user 解析 JWT
  → IssueService.create_issue
  → 查询项目成员角色、校验负责人
  → IssueRepository.create
  → AsyncSession.flush 获取主键
  → 同事务写 Notification
  → AsyncSession.commit
  → Pydantic IssueResponse
```

API 不执行 SQL、不提交事务；Repository 不判断业务权限、不提交事务；Service 同时承担业务规则和事务边界。

## 3. 配置系统

`app/core/config.py` 使用 `pydantic-settings`。`BACKEND_DIR` 保证从任意工作目录都能定位 `backend/.env`，`get_settings()` 用缓存避免重复解析。

配置分为：

- 应用信息和 API 前缀；
- JWT 算法、密钥和过期时间；
- MySQL 地址；
- Redis、Celery Broker 和 Result Backend。

`.env.example` 只保存占位值，`.env` 被 Git 忽略。Docker Compose 用环境变量覆盖主机名，把本机的 `127.0.0.1` 改为容器服务名 `mysql`、`redis`。

应能回答：为什么不用在代码中拼接数据库 URL？`URL.create()` 能正确处理密码中的特殊字符。

## 4. 路由与依赖注入

`app/api/v1/router.py` 聚合所有业务路由，`main.py` 只注册一个 v1 总路由。

常用依赖：

- `DatabaseSession`：请求级 `AsyncSession`；
- `CurrentUser`：Bearer Token → 用户；
- `require_permission(code)`：声明式系统权限；
- 路径参数与 Schema：由 FastAPI/Pydantic 解析。

`OAuth2PasswordBearer` 的 `tokenUrl` 指向 `/api/v1/auth/login`，因此 Swagger 可以使用 Authorize。

## 5. AsyncSession 生命周期

`app/database/session.py` 创建全局 AsyncEngine 和 `async_sessionmaker`。`get_db()` 为每个请求创建独立会话：

```text
进入请求 → 创建 AsyncSession → Service 执行 commit/rollback
→ 请求结束 → async with 自动 close
```

`expire_on_commit=False` 让已提交对象继续保留属性；`autoflush=False` 要求代码在需要主键时明确 `flush()`。Repository 只 `flush()`，Service 决定 `commit()` 或 `rollback()`。

测试环境使用 `NullPool`，避免 pytest 的不同事件循环复用 asyncmy 连接。

应能回答：为什么不在 Repository 中 commit？因为创建项目、Owner 成员关系和通知等多个写入必须共享一个事务。

## 6. Alembic

`alembic/env.py` 导入 `app.models`，让所有模型注册到 `Base.metadata`。迁移运行时创建独立异步引擎，并用 `connection.run_sync()` 调用 Alembic 的同步迁移核心。

迁移不是 `create_all()` 的替代写法，而是可审查的结构版本历史。每份迁移必须人工确认：

- upgrade 的建表顺序；
- downgrade 的反向顺序；
- MySQL 外键支撑索引；
- 唯一约束和业务索引。

`test_migrations.py` 比较测试库版本和代码唯一 head。

## 7. 五层职责

| 层 | 代表文件 | 负责 | 不负责 |
| --- | --- | --- | --- |
| Model | `models/issue.py` | 表、字段、索引、外键 | HTTP 和业务流程 |
| Schema | `schemas/issue.py` | 输入校验和公开响应 | SQL |
| Repository | `repositories/issue_repository.py` | 查询、分页、持久化 | 权限和 commit |
| Service | `services/issue_service.py` | 权限、状态、事务 | HTTPException |
| API | `api/v1/issues.py` | HTTP 参数、依赖、响应 | SQL 和复杂规则 |

## 8. JWT 认证链

注册：

```text
RegisterRequest
→ 查重邮箱
→ Argon2 hash_password
→ 创建 User
→ 分配 User 角色
→ 同事务提交
```

登录：

```text
Redis 登录限流
→ 按邮箱加载用户
→ 校验 is_active / is_deleted
→ verify_password
→ create_access_token
```

受保护接口：

```text
Authorization: Bearer ...
→ OAuth2PasswordBearer
→ decode_access_token
→ 加载未删除且启用的 User
→ CurrentUser
```

Token 只保存用户 ID、签发时间、过期时间和类型，不保存密码或权限快照。

## 9. 系统 RBAC

授权链：

```text
User → UserRole → Role → RolePermission → Permission
```

`RBACService` 先读取 Redis 权限缓存，未命中或 Redis 故障时查询 MySQL，再缓存 5 分钟。`require_permission()` 把权限判断放在依赖中，普通用户访问管理员接口得到 403。

系统角色只有 Admin/User。Owner/Developer/Viewer 不进入系统 `roles` 表。

## 10. 项目级权限

授权链：

```text
User + Project → ProjectMember → ProjectRole
```

`ProjectService.require_project()` 统一检查项目存在、未软删除、成员身份和允许角色。Owner 管理项目与成员；Developer 创建和处理被授权 Issue；Viewer 只读。

主负责人由 `projects.owner_id` 表示，同时也存在一条 Owner `project_members` 关系。前者是项目核心属性，后者是权限关系。

## 11. 创建项目事务

`ProjectService.create_project()` 的事务步骤：

1. 查询 Owner 项目角色；
2. 新建 Project 并 flush 得到 ID；
3. 新建创建者的 ProjectMember；
4. commit；
5. 任意步骤异常则 rollback。

这样不会出现“项目存在但没有 Owner”的半完成数据。

## 12. Issue 状态机

`ALLOWED_TRANSITIONS` 集中定义：

```text
OPEN → IN_PROGRESS → REVIEW → DONE
```

状态接口不允许跳级或回退。Review 拒绝回到 `IN_PROGRESS` 是审核业务的明确例外，由 `ReviewService` 在同一事务中处理。

Owner 可处理项目全部 Issue；Developer 只能修改自己创建或负责的 Issue；Viewer 无写权限。软删除 Issue 在普通 Repository 查询中不可见。

## 13. Review 联动

发起 Review：

1. Issue 必须为 `IN_PROGRESS`；
2. 发起人必须是有权处理该 Issue 的 Owner/Developer；
3. Reviewer 必须是 Owner/Developer，且不能是发起人；
4. 创建 `PENDING` Review；
5. Issue 更新为 `REVIEW`；
6. 写审核请求通知；
7. 同一事务提交。

审核通过：Review → `APPROVED`，Issue → `DONE`。

审核拒绝：Review → `REJECTED`，Issue → `IN_PROGRESS`。

已处理 Review 不能重复修改。

## 14. 通知生成

通知触发点包括：

- 添加项目成员；
- 分配 Issue；
- Issue 状态变化；
- 发起 Review；
- Review 通过或拒绝。

数据库 Notification 与主业务同事务写入。提交后调用 `enqueue_notification_delivery()`；Celery Worker 重新读取已提交记录，发布到 `devflow:notifications:{user_id}` Redis Channel。

Broker 入队失败不影响已落库通知。用户仍可通过通知 API 查询；这是一种“可靠存储优先、实时分发可重试”的取舍。

## 15. Redis 和 Celery

Redis 只用于：

- 用户系统权限缓存；
- 登录限流；
- Celery Broker/Result Backend；
- 通知事件 Channel。

Celery 不执行普通 CRUD。它只处理事务提交后的非核心通知分发。API 启动不主动连接 Redis；缓存和限流捕获 Redis 连接错误后降级。

## 16. 测试结构

`conftest.py` 在导入应用前设置 `ENVIRONMENT=test` 和独立测试库，并为每个测试：

1. 按外键顺序清理数据；
2. 幂等初始化角色与权限；
3. 创建 HTTPX ASGI 客户端；
4. 测试结束再次清理。

测试分为健康检查、认证/RBAC、项目、Issue、评论/Review、通知和迁移版本。

## 17. Docker 启动

开发模式只启动 MySQL/Redis，本机运行 API。完整模式：

```text
Nginx :8088
  → API :8000
      → MySQL
      → Redis
      → Celery Broker
  Celery Worker
      → MySQL
      → Redis Channel
```

Compose 健康检查控制启动顺序。API 启动前执行 Alembic 和幂等 seed；Nginx 使用 Docker DNS 动态解析 API 容器。

## 18. 分阶段阅读重点

| 阶段 | 重点文件 |
| --- | --- |
| 基础设施 | `config.py`、`session.py`、`main.py`、`health.py` |
| 认证 | `security.py`、`auth_service.py`、`dependencies.py` |
| RBAC | `rbac_repository.py`、`rbac_service.py`、`admin.py` |
| 项目 | `project_service.py`、项目三张 Model |
| Issue | `issue_service.py`、`issue_repository.py` |
| 评论/Review | `comment_service.py`、`review_service.py` |
| 通知 | `notification_service.py`、`tasks/notifications.py` |
| 部署 | `Dockerfile`、两个 Compose、`nginx.conf` |

## 19. 每阶段应该能回答的问题

- 配置：敏感信息从哪里来，为什么不会提交？
- 数据库：一个请求使用几个 Session，事务由谁提交？
- 认证：密码为何无法恢复，Token 如何过期？
- RBAC：系统角色和项目角色为什么不能合并？
- 项目：创建项目失败时 Owner 关系会怎样？
- Issue：为什么不能从 OPEN 直接跳 DONE？
- Review：如何保证 Review 与 Issue 一致？
- 通知：Celery 停止时用户是否还能看到通知？
- 测试：为什么测试库不会污染开发库？
- Docker：MySQL 未健康时 API 会不会提前启动？

## 20. 推荐练习

1. 手工调试注册、登录和 `/users/me`；
2. 跟断点观察一次项目创建事务；
3. 写一个 Viewer 修改 Issue 的失败测试；
4. 给 Review 重复处理测试增加断言；
5. 暂停 Redis，验证登录和权限查询仍可回源；
6. 观察 Celery Worker 消费通知任务；
7. 在测试库执行一次迁移 downgrade/upgrade；
8. 最后尝试设计“权限变更主动清缓存”，但不要直接复制实现。
