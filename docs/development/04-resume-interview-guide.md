# DevFlow 简历与面试指南

本文只描述仓库中可运行、可测试的实现，不代表真实公司生产系统，不包含虚构用户量、QPS 或性能提升比例。

## 1. 项目简介

DevFlow 是一个基于 FastAPI 的企业研发协作后端，采用 SQLAlchemy 2.0 Async 和 MySQL 实现用户认证、系统 RBAC、项目成员权限、Issue 状态流转、评论、Review 与站内通知闭环，并使用 Redis、Celery、Alembic、Pytest 和 Docker 补齐缓存、异步任务、迁移、测试与部署能力。

## 2. 中文简历描述

可以从以下内容选 3～5 条，并确保自己能解释对应代码：

- 基于 FastAPI、Pydantic v2 和 SQLAlchemy 2.0 Async 搭建 API/Service/Repository 分层后端，使用请求级 AsyncSession 和 Alembic 管理 12 张核心业务表；
- 使用 JWT、Argon2 与 Admin/User RBAC 实现认证和平台权限，并设计 Owner/Developer/Viewer 项目级权限，隔离不同项目的数据与操作范围；
- 设计 Issue 相邻状态机及 Review 审核流程，通过 Service 层事务保证 Review 状态、Issue 状态与数据库通知一致更新；
- 实现 Issue 多条件筛选、关键词查询与分页，依据实际查询场景为项目、负责人、状态和用户未读通知建立索引；
- 使用 Redis 缓存用户权限并实现可降级登录限流，使用 Celery 在事务提交后异步发布通知事件，完成 MySQL/Redis/API/Worker/Nginx 的 Docker Compose 编排。

不要写“高并发”“百万用户”“性能提升 80%”等仓库无法证明的表述。

## 3. 核心技术亮点与代码位置

| 亮点 | 实际代码 |
| --- | --- |
| 经典分层 | `app/api/v1/`、`app/services/`、`app/repositories/` |
| AsyncSession 生命周期 | `app/database/session.py`、`dependencies.py` |
| JWT/Argon2 | `app/core/security.py`、`services/auth_service.py` |
| 双层权限 | `api/dependencies.py`、`services/rbac_service.py`、`project_service.py` |
| 项目原子创建 | `ProjectService.create_project()` |
| Issue 状态机 | `services/issue_service.py` 的 `ALLOWED_TRANSITIONS` |
| Review 状态联动 | `ReviewService.create_review()`、`decide_review()` |
| 通知一致性 | Project/Issue/Review Service 与 `notification_repository.py` |
| Redis 降级 | `core/cache.py`、`core/rate_limit.py` |
| Celery 分发 | `tasks/celery_app.py`、`tasks/notifications.py` |
| 迁移 | `backend/alembic/versions/` |
| 集成测试 | `backend/app/tests/` |
| 部署 | `backend/Dockerfile`、`docker/compose.yml`、`nginx.conf` |

## 4. 项目难点

### 双层权限边界

系统 Admin/User 决定平台能力；项目 Owner/Developer/Viewer 决定具体项目资源权限。难点是不能因为用户在项目 A 为 Owner，就允许其管理项目 B。

实现通过 `ProjectMember(project_id, user_id, role_id)` 每次在资源所属项目内查询角色，避免使用全局项目角色。

### 多对象事务

创建项目至少写 Project 和 Owner 成员关系；Review 处理至少写 Review、Issue 和 Notification。任一写入失败都应回滚，不能出现半完成业务状态。

### 异步基础设施降级

Redis/Celery 是增强能力，MySQL 才是核心事实来源。权限缓存未命中回源 MySQL；通知先可靠写 MySQL，再在提交后入队分发。

### MySQL 迁移回滚

MySQL 会使用普通索引支撑外键。自动生成的 downgrade 若先删除该索引会失败，因此迁移人工调整为直接删表，由 MySQL 同时清理表内索引。

## 5. 事务设计

Service 是事务边界。Repository 可以 `flush()` 获取主键，但不 `commit()`。

创建项目：

```text
INSERT projects
→ flush 获取 project.id
→ INSERT project_members(Owner)
→ commit
```

发起 Review：

```text
INSERT reviews(PENDING)
→ UPDATE issues SET status=REVIEW
→ INSERT notifications
→ commit
→ Celery 入队
```

审核通过/拒绝采用相同模式。`get_db()` 在异常请求时补充 rollback，Service 在业务写方法中显式 rollback。

## 6. 权限设计

系统 RBAC 表：

```text
users → user_roles → roles → role_permissions → permissions
```

项目权限表：

```text
users → project_members → project_roles
```

Admin 权限通过 `require_permission()` 声明。项目权限集中在 Service，不散落 API。Developer 修改 Issue 时还要满足“本人创建或本人负责”，属于角色之上的资源属性授权。

## 7. 异步数据库设计

项目使用 `create_async_engine`、`async_sessionmaker`、`AsyncSession` 和 `asyncmy`。查询统一使用：

```python
await session.execute(select(Model).where(...))
```

关键配置：

- `pool_pre_ping=True`：复用前检查连接；
- `pool_recycle=1800`：降低 MySQL 空闲断连影响；
- `expire_on_commit=False`：提交后响应转换无需隐式重新加载；
- 测试用 `NullPool`：避免跨 pytest 事件循环复用连接。

没有使用同步 `session.query()`，也没有在 async 上下文依赖懒加载。

## 8. Alembic 迁移设计

迁移按领域拆分：

1. 用户权限；
2. 角色名称唯一约束；
3. 项目与成员；
4. Issue/评论/Review；
5. 通知。

应用启动不会自动 `create_all()`。完整 Docker API 启动命令先执行 `alembic upgrade head`，再执行幂等 seed。

测试库真实验证了升级、回滚、重新升级，`test_migrations.py` 确认数据库版本等于代码 head。

## 9. Redis 和 Celery 的理由

Redis 权限缓存减少稳定 RBAC 关系的重复联表查询；登录限流使用 Redis 原子自增和过期键。Redis 不可用时缓存与限流降级，认证仍使用 MySQL。

Celery 不承载 CRUD。数据库通知随主事务提交后，Celery Worker 读取通知并发布用户专属 Redis Channel，可重试但不影响已提交核心业务。

当前没有 WebSocket 消费端，因此不能把它描述为“完整实时推送系统”；准确说法是“完成异步通知事件发布基础”。

## 10. Docker 部署设计

完整栈包含：

- MySQL：业务持久化和健康检查；
- Redis：缓存、Broker、结果后端和 Channel；
- API：非 root 用户，启动时迁移和 seed；
- Worker：非 root 用户、2 个并发进程；
- Nginx：统一 8088 入口，Docker DNS 动态解析 API。

Compose 用 health condition 控制依赖顺序，数据使用命名卷。密码和 JWT 密钥来自 `backend/.env`，不写入镜像和 Compose。

## 11. 可能的面试追问与参考回答

### 为什么 Service 负责 commit？

一个业务动作可能涉及多个 Repository。例如创建项目要写项目和 Owner 关系。若 Repository 各自 commit，第二步失败后第一步无法回滚，破坏原子性。

### flush 和 commit 有什么区别？

flush 把待写 SQL 发到当前事务并获得自增主键，但事务仍可回滚；commit 才结束并持久化事务。

### 为什么保留 projects.owner_id 和 project_members？

`owner_id` 表达项目主负责人这一核心属性，便于直接定位；`project_members` 表达用户加入项目及其项目角色。两者语义不同，创建时必须保持一致。

### 系统角色和项目角色为什么分开？

系统角色作用于整个平台，项目角色只在一个项目生效。合并后容易让某项目 Owner 获得其他项目或平台管理权限。

### JWT 被盗怎么办？

当前是短期 Access Token，降低泄露窗口，但未实现 Refresh Token、主动撤销列表和设备会话管理。这是当前版本边界，生产化应增加轮换、撤销和安全 Cookie 策略。

### 如何避免 N+1？

需要组合数据的项目成员列表一次 join User 和 ProjectRole；权限通过联表一次查询。项目中不依赖 ORM 懒加载。

### 为什么通知写入失败要回滚主业务？

站内通知是协作事件对用户可见的一部分。当前选择强一致，避免“已分配任务但负责人完全看不到通知”。外部实时发布失败则不回滚，因为数据库通知已经可查询。

### Redis 故障会怎样？

权限读取回源 MySQL，登录限流跳过，Celery 实时分发暂不可用；MySQL 业务与通知 API 保持可用。

### 如何防止 Review 重复处理？

处理前确认当前用户是指定 Reviewer，且 Review 仍为 PENDING、Issue 为 REVIEW。第一次提交后状态改变，第二次返回 409。

### 为什么测试使用真实 MySQL？

本项目依赖 MySQL 外键、索引和异步驱动行为。使用 SQLite 会掩盖 BIGINT 自增、外键索引和方言差异，因此使用隔离 MySQL 测试库。

### 软删除有什么代价？

所有普通查询必须统一过滤，唯一邮箱仍占用，历史关联保留。当前只对用户、项目和 Issue 使用，避免把软删除机械扩散到关联表。

### 登录限流的不足？

当前以客户端 IP 和邮箱为键、固定 60 秒窗口。反向代理场景要确保可信客户端 IP，生产中还可增加全局 IP 维度、滑动窗口和监控。

### 为什么不用微服务？

当前业务规模和个人项目目标适合模块化单体。单体事务能直接保证 Review/Issue/通知一致性，拆分服务会引入分布式事务和运维成本，没有需求依据。

## 12. 必须真正掌握的内容

- 一次 FastAPI 请求从依赖到数据库的完整路径；
- AsyncSession、flush、commit、rollback 的差异；
- JWT 签发与解析，不把密码放进 Token；
- RBAC 和资源属性授权的区别；
- 项目创建、Review 决策的事务边界；
- Issue 状态机合法和非法路径；
- Alembic upgrade/downgrade 与 MySQL 外键索引；
- Redis 故障降级和 Celery 的提交后入队策略；
- 测试库隔离与夹具清理顺序；
- Docker 健康检查和服务依赖。

如果不能用自己的话解释，不要只背简历句子。

## 13. 不应夸大的内容

- 未做真实流量压测，不声称具体 QPS；
- 未部署线上生产环境，不声称生产稳定性；
- 未实现 WebSocket 客户端，不声称端到端实时推送；
- 未实现 Refresh Token、审计日志、附件或 CI/CD；
- 没有前端；
- 没有微服务、Kafka、Elasticsearch 或完整 DevOps；
- Redis 缓存没有基准数据，不写性能提升百分比；
- 测试覆盖核心场景，但未计算语句或分支覆盖率。

## 14. 面试演示建议

1. 展示 Swagger 注册、登录；
2. 创建项目并查询自动生成的 Owner；
3. 添加 Developer 和 Viewer；
4. 用 Viewer 创建 Issue，展示 403；
5. 创建 Issue 并演示非法跳转 409；
6. 完成 Review 通过或拒绝联动；
7. 查看通知；
8. 展示对应测试；
9. 展示 Alembic head 和 Docker 服务健康；
10. 最后主动说明当前边界和下一步改进。
