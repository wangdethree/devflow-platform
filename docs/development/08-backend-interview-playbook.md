# DevFlow 后端岗位面试作战手册

本文用于后端开发岗位的简历投递、项目介绍、技术深挖和模拟面试。所有表述都以仓库当前实现为边界，不虚构用户量、生产流量或性能提升比例。

不要逐字背答案。正确用法是先理解代码，再把每一段压缩成自己的表达。

## 一、项目定位

面试时把 DevFlow 定位为：

> 一个以 FastAPI 为核心的企业研发协作平台。我主要围绕认证、双层权限、项目与 Issue 协作、Review 状态联动、站内通知以及并发一致性完成后端设计，并补充了 MySQL 迁移、Redis/Celery、Prometheus、Docker 和自动化测试。Vue 管理端主要用于真实接口联调和业务闭环演示。

投递后端岗位时，建议时间分配：

- 后端架构、业务规则和一致性：70%
- 测试、可观测性与部署：20%
- 前端和页面：10%

不要从“我做了哪些页面”开始介绍，应从“系统解决什么协作问题、后端有什么约束”开始。

## 二、三种项目介绍话术

### 30 秒版本

> DevFlow 是一个前后端分离的研发协作平台，核心后端使用 FastAPI、SQLAlchemy Async 和 MySQL。我实现了 Access/Refresh Token 轮换与设备会话、系统 RBAC 和项目角色双层权限、Issue 状态机与乐观锁，以及 Review、Issue、通知的事务一致性。Redis 用于权限缓存和登录限流，Celery 用于事务提交后的通知事件分发，并通过 31 项后端测试、Prometheus 指标和 Docker Compose 完成验证与交付。

适用：自我介绍中快速带过项目。

### 1 分钟版本

> DevFlow 是我围绕企业研发协作场景完成的模块化单体项目。业务主线是用户注册登录、创建项目、添加 Owner/Developer/Viewer、创建和分配 Issue、进行评论、发起 Review，最后根据审批结果完成或退回 Issue。
>
> 后端采用 API、Service、Repository 分层。Service 负责权限、状态机和事务，Repository 只负责查询与持久化。认证不是只签发一个 JWT，而是通过 Access/Refresh Token、服务端设备会话、Refresh Token 摘要存储和轮换来支持主动注销与重放检测。并发方面，普通 Issue 更新使用版本号乐观锁，Review 审批使用行锁保证单次处理。
>
> Redis 和 Celery 被设计为可降级的增强能力，MySQL 是事实来源。项目还包含真实 MySQL 集成测试、Alembic 迁移、结构化日志、Prometheus 指标、压测脚本和 Docker Compose。Vue 前端用于验证完整业务链路。

适用：面试官问“介绍一下项目”。

### 3 分钟版本

> DevFlow 解决的是研发团队中项目成员、任务状态和评审结果难以统一追踪的问题。业务主线从用户身份开始，一个用户可以创建项目并成为 Owner，再添加 Developer 或 Viewer。Owner 和 Developer 可以创建 Issue，但 Developer 只能修改自己创建或负责的任务，Viewer 只读。Issue 只能按 OPEN、IN_PROGRESS、REVIEW、DONE 顺序流转，Review 通过后完成，拒绝后退回处理中。
>
> 架构上我选择模块化单体，而没有直接拆微服务。原因是当前规模下 Review、Issue 和 Notification 需要强事务一致性，单体能用本地事务直接保证，同时部署和调试成本更低。代码按 API、Service、Repository 分层，API 做协议转换与依赖注入，Service 承担业务规则和事务，Repository 不提交事务。
>
> 认证方面，密码使用 Argon2。Access Token 是短期 JWT，Refresh Token 每次刷新都会轮换；数据库只保存 Refresh Token 的 SHA-256 摘要和设备会话。Access Token 带 session id，每次鉴权除验证签名外还会检查服务端会话，因此注销后旧 Access Token 也会立即失效。如果旧 Refresh Token 被再次使用，会撤销整条会话。
>
> 一致性方面，Issue 修改使用 `WHERE id=? AND version=?` 的条件更新，成功后版本自增，避免并发覆盖。Review 审批对 Review 行执行 `SELECT FOR UPDATE`，同一结果重复请求幂等返回，不同结果返回冲突；Review、Issue 和通知在同一事务更新。通知先写 MySQL，提交后再由 Celery 发布事件，因此 Redis 或 Broker 故障不会回滚已经成功的主业务。
>
> 工程上使用 Alembic 管理 13 张业务表，31 项后端测试覆盖认证、权限、事务、并发和迁移；通过结构化日志、Request ID、Prometheus 和可复现压测脚本观察系统，再用 Docker Compose 编排 MySQL、Redis、API、Worker、Nginx 和 Prometheus。Vue 管理端直接使用真实 API，主要帮助展示和发现接口契约问题。

适用：项目深挖轮开场。

## 三、简历表述

建议从下面选 4 条，不要全部塞进简历：

- 基于 FastAPI、Pydantic v2、SQLAlchemy 2.0 Async 和 MySQL 构建研发协作平台，采用 API/Service/Repository 分层并以 Service 作为事务边界；
- 设计 Admin/User 系统 RBAC 与 Owner/Developer/Viewer 项目级角色的双层授权模型，实现角色权限与资源属性权限组合校验；
- 实现 JWT Access/Refresh Token、Argon2 密码哈希、持久化设备会话、Refresh Token 轮换与重放检测，支持当前设备和全部设备主动注销；
- 基于版本号条件更新实现 Issue 乐观锁，使用 MySQL 行锁实现 Review 并发审批和幂等处理，保证 Review、Issue 与通知同事务一致；
- 使用 Redis 实现可降级权限缓存与登录限流，使用 Celery 在数据库事务提交后异步发布通知事件；
- 建立 Alembic 迁移、JSON 结构化日志、Prometheus 指标与 Docker Compose 交付流程，编写 31 项后端测试覆盖认证、权限、并发、迁移及异常场景。

### 面试官看完简历最可能圈出的词

你必须能解释：

- 为什么使用异步 SQLAlchemy；
- Service 为什么是事务边界；
- JWT 为什么还要服务端会话；
- Refresh Token 如何轮换和检测重放；
- 两层 RBAC 如何防止跨项目越权；
- 乐观锁和行锁的区别；
- Celery 为什么放在 commit 之后；
- Redis 故障后系统还能否工作；
- 31 项测试中哪些是真实 MySQL 并发测试；
- 为什么选择模块化单体而不是微服务。

## 四、白板架构讲解

### 请求链路

```text
Vue / Swagger / API Client
          │ HTTP + Bearer Token
          ▼
       Nginx
          ▼
FastAPI Middleware
  ├─ Request ID
  ├─ JSON Access Log
  └─ Prometheus Timing
          ▼
API Router + Dependency
  ├─ Pydantic Validation
  ├─ Authentication
  └─ System Permission
          ▼
Service
  ├─ Project Role
  ├─ Resource Ownership
  ├─ State Machine
  └─ Transaction Boundary
          ▼
Repository → AsyncSession → MySQL
          │
          ├─ Redis：权限缓存 / 登录限流
          └─ commit 后 → Celery → Redis Channel
```

### 模块边界

| 层 | 负责 | 不负责 |
|---|---|---|
| API | HTTP、Schema、依赖注入、状态码 | 复杂业务事务 |
| Service | 权限、状态机、事务、多仓库编排 | 拼接 HTTP 响应 |
| Repository | 查询、写入、`flush()` | `commit()` 和业务决策 |
| Model | 持久化映射 | API 暴露结构 |
| Schema | 请求校验、响应白名单 | 数据库事务 |

### 为什么不是“Controller 直接写 ORM”

回答：

> 创建项目、Review 审批这类动作会同时操作多个表。如果路由直接写 ORM，权限、事务和异常处理容易散落，测试也更难聚焦。把业务规则集中到 Service 后，API 只处理协议，Repository 可以复用，事务边界也更清楚。

## 五、五个重点 STAR 故事

### 故事 1：JWT 无法主动失效

**Situation**：纯 JWT 是无状态的，退出登录或禁用用户后，未过期 Access Token 仍可能继续访问。

**Task**：保留 JWT 的轻量传递，同时支持设备会话、主动注销和 Refresh Token 重放检测。

**Action**：

1. Access/Refresh Token 都带 `sub`、`sid`、`jti` 和类型；
2. 登录时创建 `auth_sessions`；
3. 数据库只保存 Refresh Token SHA-256 摘要；
4. 每次刷新锁定会话、校验摘要并轮换；
5. 每次 Access Token 鉴权同时检查会话状态；
6. 旧 Refresh Token 重放时撤销会话。

**Result**：支持当前设备注销、全部设备注销、账号禁用立即失效和 Refresh Token 重放检测。

**主动说明的边界**：浏览器生产环境仍应把 Refresh Token 放入 Secure、HttpOnly、SameSite Cookie，并补充 CSRF、防 XSS 和密钥轮换。

### 故事 2：Issue 并发覆盖

**Situation**：两个开发者同时读取版本 1，一个改负责人，一个改优先级；后提交者可能覆盖先提交者。

**Task**：检测旧数据提交，避免静默丢失更新。

**Action**：

```sql
UPDATE issues
SET ..., version = version + 1
WHERE id = :id AND version = :expected_version;
```

检查受影响行数，0 行则返回并发冲突。

**Result**：只有一个基于旧版本的请求成功，另一个显式收到冲突并重新读取。

**为什么不用全程行锁**：普通编辑冲突概率低，乐观锁不会让用户思考期间占用数据库锁。

### 故事 3：Review 重复审批

**Situation**：审核按钮被重复点击或请求重试，两个审批请求可能同时更新 Review、Issue 和通知。

**Task**：审批只产生一次业务结果和一次通知，同时允许相同请求安全重试。

**Action**：

1. `SELECT ... FOR UPDATE` 锁定 Review；
2. 验证指定审核人；
3. 若仍为 PENDING，更新 Review、Issue 和 Notification；
4. 相同结果重复请求幂等返回；
5. 不同结果返回 409；
6. 三个对象同一事务提交。

**Result**：审批结果串行化，避免重复通知和状态撕裂。

### 故事 4：Redis/Celery 故障不能拖垮主业务

**Situation**：权限缓存、登录限流和异步通知都依赖 Redis，但 Redis 不是核心事实来源。

**Task**：基础设施故障时尽量保住登录、权限和站内通知查询。

**Action**：

- 权限缓存失败回源 MySQL；
- Redis 限流失败记录告警并跳过；
- Notification 随主事务先写 MySQL；
- commit 后才调用 Celery；
- Celery 入队失败不回滚已提交事务。

**Result**：Redis 故障降低缓存、限流和实时分发能力，但核心 MySQL 业务仍可用。

**边界**：当前 commit 后直接入队仍有进程崩溃窗口；生产级可以使用 Outbox Pattern。

### 故事 5：真实前端联调发现契约错误

**Situation**：静态阅读容易把 Review 处理和通知已读方法记错。

**Task**：确保管理端严格使用真实运行态接口。

**Action**：同时核对路由代码、Pydantic Schema 和 OpenAPI，并跑注册、登录、项目、Issue、Review、通知的真实链路。

**Result**：发现 Review 决策真实接口为 `PATCH /reviews/{id}`，通知已读也是 PATCH；及时修正前端并形成 API 映射文档。

**后端岗位价值**：说明契约测试和端到端验证能发现“代码能编译但协议不匹配”的问题。

## 六、核心技术追问

### 1. FastAPI 与异步

#### 为什么选择 FastAPI？

答题要点：

- Pydantic Schema 和类型提示直接形成输入校验与 OpenAPI；
- 原生支持 async；
- Depends 适合认证、数据库会话和权限声明；
- 对个人模块化单体开发效率高。

不要回答“因为 FastAPI 性能一定比所有框架高”。框架只是整体性能的一部分。

#### `async def` 一定更快吗？

> 不一定。异步适合数据库、网络这类 I/O 等待，可以在等待时处理其他请求；CPU 密集任务不会因为 async 自动加速，反而可能阻塞事件循环。CPU 密集任务应放线程池、进程池或任务队列。

#### 为什么不能在 async 路由中使用同步 MySQL 驱动？

同步 I/O 会阻塞事件循环，让同进程其他协程无法推进。项目使用 asyncmy 和 AsyncSession，保持调用链异步。

#### `expire_on_commit=False` 有什么作用？

提交后 ORM 属性不被立即标记过期，响应序列化时不会隐式访问数据库。异步环境尤其要避免不可控的隐式 I/O。

#### 为什么测试使用 `NullPool`？

pytest 可能为测试创建不同事件循环。复用旧循环创建的异步连接容易出错；NullPool 让连接及时释放，也提升测试隔离性。

### 2. 事务与 SQLAlchemy

#### `flush()`、`commit()`、`refresh()` 分别是什么？

- `flush()`：发送 SQL 到当前事务，可获取自增主键，仍可回滚；
- `commit()`：提交事务，使修改持久化；
- `refresh()`：重新从数据库加载对象字段。

#### 为什么 Repository 不 commit？

一次业务动作可能跨多个 Repository。若各自提交，后续步骤失败无法整体回滚。Service 最了解完整业务边界。

#### FastAPI 请求结束时为什么还要兜底 rollback？

Service 已对写路径显式回滚，但数据库依赖在异常时兜底 rollback，可以确保未完成事务不会污染连接归还后的后续请求。

#### 事务隔离级别如何影响项目？

回答建议：

> MySQL InnoDB 默认常见配置是 Repeatable Read，但项目没有依赖“读快照自动解决写冲突”。Issue 用显式版本条件更新，Review 用行锁，把关键并发语义写进业务操作。这样比仅凭隔离级别猜测更清楚。

### 3. 认证与安全

#### 为什么密码使用 Argon2？

Argon2 是专门用于密码哈希的内存困难算法，带随机盐，能提高离线暴力破解成本。不能使用普通 SHA-256 直接保存密码。

#### Refresh Token 为什么数据库只存摘要？

数据库泄露时，原始 Refresh Token 可以直接换取新 Token。存摘要后只能用于比较，不能反推出原 Token。

#### 既然每次都查会话，JWT 的意义是什么？

> JWT 仍负责签名保护和承载用户、会话、过期时间等声明；服务端会话用于撤销和轮换。这里选择的是“可控会话”而不是完全无状态，以换取安全和主动失效能力。

#### 为什么 Refresh 时要加行锁？

两个刷新请求可能同时拿到同一个旧 Refresh Token。锁定会话后只有一个先完成轮换，另一个读到的新摘要与旧 Token 不匹配，从而触发重放处理。

#### 这种并发刷新会不会误伤？

会。浏览器多个请求同时刷新同一个一次性 Token，后到请求可能被判重放。因此前端通过共享 `refreshPromise` 合并并发刷新。生产中还可以设计极短宽限窗口，但会增加安全和实现复杂度。

#### 登录错误为什么统一说“邮箱或密码错误”？

避免向攻击者泄露某邮箱是否注册，降低用户枚举风险。

### 4. 权限模型

#### RBAC 和 ACL 有什么区别？

RBAC 通过角色聚合权限；ACL 更接近资源到主体的授权列表。项目使用系统 RBAC 控制平台能力，同时通过 `project_members` 建立资源范围内的角色关系。

#### Developer 为什么还要检查 creator/assignee？

角色只是粗粒度能力。“只能修改自己创建或负责的 Issue”属于资源属性授权，需要结合当前资源字段判断。

#### 前端隐藏按钮能否保证权限安全？

不能。前端可以被绕过。所有系统权限、项目角色和资源属性都必须由后端重新验证。

#### 如何避免项目 A 的 Owner 操作项目 B？

每次从目标资源确定 `project_id`，再用 `(project_id, user_id)` 查询当前项目角色，不能只看用户是否在任意项目拥有 Owner。

### 5. 并发控制

#### 乐观锁适合什么场景？

读多写少、冲突概率较低、用户操作时间长的场景。失败时需要客户端重新读取并提示冲突。

#### 悲观锁适合什么场景？

冲突必须串行化且事务很短的场景，例如审批时检查并改变唯一状态。

#### 乐观锁会不会出现 ABA 问题？

只要 `version` 单调递增且不回退，即使字段值改回原值，版本仍不同，因此能检测发生过修改。

#### 行锁锁的是什么？

InnoDB 实际锁行为与索引和查询条件有关。通过主键查单条 Review 的 `SELECT FOR UPDATE` 会锁定对应索引记录；若查询条件缺少合适索引，锁范围可能扩大。

#### 为什么状态流转不能由前端随意传任意状态？

前端只改善交互，后端必须基于当前状态和允许集合验证。否则用户可以绕过 UI 从 OPEN 直接改成 DONE。

### 6. MySQL 与数据建模

#### 为什么 `projects.owner_id` 和 Owner 成员关系同时存在？

前者是项目主负责人这一核心实体属性，后者是成员及角色授权关系。创建项目时在同一事务写入，保证两者一致。

#### 为什么评论物理删除，而项目和 Issue 软删除？

当前设计认为项目和 Issue 有较强历史关联，需要保留关系；评论只允许作者删除且没有恢复需求。软删除并非所有表都应该使用。

#### 软删除的风险是什么？

- 所有读取必须过滤；
- 唯一值仍被占用；
- 关联查询容易漏条件；
- 数据量持续增长；
- 需要恢复、归档和清理策略。

#### 如何设计索引？

先从真实查询条件出发，而不是“给所有字段加索引”。项目重点查询：

- 用户参与项目；
- project + status/type/priority；
- assignee/creator；
- 用户未读通知；
- 唯一邮箱、角色名和成员关系。

解释联合索引时要说明最左前缀、选择性、排序和写放大。

#### 为什么不用 SQLite 做全部测试？

项目依赖 MySQL 外键、索引、自增和行锁语义。SQLite 可能让测试通过但生产 MySQL 失败，因此集成测试使用隔离 MySQL。

### 7. Redis 与 Celery

#### 权限为什么适合缓存？

权限关系读取频繁、变化相对少，适合短 TTL 缓存。但必须接受短暂不一致，或在权限变更时主动失效。

#### 当前缓存失效策略够不够？

> 当前主要依赖 TTL，没有完成所有权限变更后的主动失效。作为项目边界已经记录；生产中应在角色或权限变更事务成功后删除相关用户缓存。

#### 登录限流有什么问题？

当前使用 IP+邮箱、固定 60 秒窗口、每分钟 10 次。边界包括代理 IP 可信问题、固定窗口突刺、Redis 降级后保护消失。可升级为滑动窗口、令牌桶和多维限流。

#### Celery 任务如何保证不丢？

准确回答：

> 当前保证数据库 Notification 与主业务同事务，但 commit 到 Celery 入队之间仍有进程崩溃窗口，因此不能声称绝对不丢实时事件。更严格的方案是 Outbox 表和独立投递器。

#### 为什么不用 Kafka？

当前只有单体通知事件分发，Redis/Celery 的运维成本更低。Kafka 适合更高吞吐、可回放、多消费者日志流，但项目没有足够需求证明必须引入。

### 8. 可观测性、测试与部署

#### Request ID 有什么用？

让客户端错误响应、访问日志和内部异常日志可以关联同一次请求，便于排查跨层问题。

#### Prometheus 标签为什么不能放 user_id/issue_id？

资源 ID 无上限，会产生高基数时间序列。应使用有限集合，如方法、路由模板、状态码和业务结果。

#### 单元测试和集成测试如何划分？

- 纯函数、Schema、状态映射适合单元测试；
- API、事务、权限、MySQL 行锁和迁移必须集成测试；
- 前后端完整行为适合 E2E。

#### 31 项测试是否代表覆盖率高？

不能直接等同。测试数量不代表语句或分支覆盖率。准确说法是覆盖了核心业务和异常路径，但没有计算覆盖率。

#### Docker Compose 的启动顺序如何控制？

依赖服务配置健康检查，API 等待 MySQL 健康后执行迁移和 seed，再启动 Uvicorn；Nginx 等 API 健康。

#### 为什么容器不用 root 运行？

降低应用进程被利用后对容器和挂载资源的权限，属于最小权限原则。

## 七、系统设计升级题

### 如果项目增长到百万通知，怎么改？

建议回答顺序：

1. 先确认访问模式和真实容量；
2. 通知表按 `user_id, is_read, created_at` 建联合索引；
3. 使用游标分页替代深 offset；
4. 冷热数据归档或分区；
5. Outbox 保证事件可靠投递；
6. WebSocket 网关消费消息；
7. 未读数可使用 Redis 计数，但以数据库或可重建事件为准；
8. 根据证据考虑分库分表，而不是一开始就拆。

### 如果拆微服务，优先拆什么？

可以把通知投递作为较早拆分候选，因为它有独立伸缩和异步边界。项目、Issue 和 Review 强事务关联，不应为了“微服务”标签过早拆开。

### 如果要求审计日志，怎么做？

- 记录操作者、动作、目标、请求 ID、前后值摘要和时间；
- 审计记录尽量追加写，不允许普通业务修改；
- 敏感字段脱敏；
- 与核心操作的一致性要明确；
- 大量审计可通过 Outbox 后异步落独立存储，但关键动作需保证可追溯。

### 如果要支持附件，注意什么？

- 文件内容放对象存储，数据库保存元数据；
- 使用预签名上传；
- 校验大小、类型、扩展名和内容；
- 隔离私有对象访问权限；
- 病毒扫描；
- 删除与业务对象解绑、生命周期清理。

### 如果要支持多租户，怎么改？

所有核心表增加 tenant_id，并让唯一约束、索引、查询和权限都包含租户边界。不能只在前端或少数查询加租户条件；可通过 Repository 规范、数据库策略或独立库加强隔离。

## 八、代码定位题

面试前至少亲自打开以下位置：

| 问题 | 代码位置 |
|---|---|
| Access/Refresh Token 声明 | `backend/app/core/security.py` |
| 登录、刷新、重放检测 | `backend/app/services/auth_service.py` |
| Access Token + 会话鉴权 | `backend/app/api/dependencies.py` |
| 权限缓存 | `backend/app/services/rbac_service.py` |
| 登录限流 | `backend/app/core/rate_limit.py` |
| 项目事务和成员权限 | `backend/app/services/project_service.py` |
| Issue 状态机和乐观锁 | `backend/app/services/issue_service.py`、`repositories/issue_repository.py` |
| Review 行锁和幂等 | `backend/app/services/review_service.py`、`repositories/review_repository.py` |
| 通知事务与任务入队 | 各领域 Service、`backend/app/tasks/notifications.py` |
| 数据库会话 | `backend/app/database/session.py`、`dependencies.py` |
| 异常映射 | `backend/app/core/exceptions.py` |
| 日志和指标 | `backend/app/core/logging.py`、`metrics.py` |
| 迁移 | `backend/alembic/versions/` |
| 测试 | `backend/app/tests/` |
| Docker | `backend/Dockerfile`、`docker/compose.yml` |

练习方式：面试官随机说一个亮点，你应在 30 秒内说出调用链和关键文件。

## 九、模拟面试题单

### 第一轮：项目基础，约 20 分钟

1. 用一分钟介绍 DevFlow。
2. 为什么选择模块化单体？
3. 一次创建项目请求经过哪些层？
4. Service 为什么负责 commit？
5. 系统角色和项目角色有什么区别？
6. Developer 修改 Issue 的完整鉴权条件是什么？
7. Issue 状态机在哪里校验？
8. 为什么前端不能决定权限安全？
9. 项目中最难的一个问题是什么？
10. 如果重新做一次，你最先改什么？

合格标准：不看文档，可以画出请求链、权限模型和事务边界。

### 第二轮：后端深挖，约 35 分钟

1. Access Token 和 Refresh Token 分别包含什么？
2. Refresh Token 轮换如何工作？
3. 为什么只存 Token 摘要？
4. 两个刷新请求并发会怎样？
5. JWT 为什么仍需查数据库？
6. Issue 乐观锁的 SQL 是什么？
7. 受影响行数为 0 可能有哪些原因？
8. Review 为什么使用行锁？
9. 相同重复审批和不同重复审批如何处理？
10. Redis 故障后哪些功能降级？
11. commit 后 Celery 入队有什么可靠性窗口？
12. 如何用 Outbox 改进？
13. AsyncSession 有哪些常见坑？
14. 为什么测试使用真实 MySQL？
15. 如何验证迁移可以回滚？

合格标准：能说出具体 SQL、竞争顺序、失败窗口和改进方案。

### 第三轮：系统设计，约 30 分钟

1. 如何把通知扩展到百万级？
2. 如何设计 WebSocket 在线推送？
3. 如何保证消息不丢、不重复？
4. 如果拆微服务，服务边界如何选？
5. 如何支持多租户？
6. 如何支持审计日志？
7. 数据库慢查询如何定位？
8. 如何设计容量压测？
9. 如何做灰度发布和回滚？
10. 如果 MySQL 主库故障，系统如何恢复？

合格标准：先澄清规模与一致性要求，再提出方案和权衡，不要直接堆中间件名词。

## 十、面试中的高风险回答

以下说法不要出现：

- “用了 async，所以一定高并发。”
- “JWT 是无状态的，所以完全不查数据库。”
- “Redis 挂了系统没有任何影响。”  
  应说核心业务可用，但缓存、限流和实时事件分发降级。
- “Celery 保证消息绝对不丢。”  
  当前没有 Outbox。
- “加了版本号就不会有任何并发问题。”
- “用了事务就不会重复审批。”  
  还需要锁、状态检查和幂等规则。
- “31 个测试所以覆盖率 100%。”
- “用了 Prometheus 就具备完整可观测性。”
- “这是微服务项目。”
- “支持百万用户、高并发、生产落地。”

## 十一、项目演示脚本

建议演示控制在 8 分钟：

1. 展示架构和业务状态机，1 分钟；
2. 登录并说明 Token/会话，1 分钟；
3. 创建项目，展示自动 Owner，1 分钟；
4. 添加 Developer/Viewer，说明双层权限，1 分钟；
5. 创建 Issue 并开始处理，1 分钟；
6. 发起 Review，用另一账号通过或驳回，1.5 分钟；
7. 展示通知和状态联动，0.5 分钟；
8. 打开乐观锁/Review Service 测试与 Prometheus，1 分钟。

如果现场时间不足，只演示：

```text
双层权限 → 乐观锁 → Review 事务联动
```

这三项最能体现后端能力。

## 十二、反问面试官

项目讲完后，可以自然反问：

- 团队目前更常见的是单体内事务，还是跨服务一致性问题？
- 线上认证采用纯 JWT、服务端 Session，还是混合方案？
- 团队如何做数据库迁移审核和回滚演练？
- 后端岗位对可观测性、压测和故障演练的参与程度如何？
- 新人进入团队后，通常会从业务接口、基础设施还是稳定性治理开始？

避免一上来只问加班和薪资；这些可以在合适轮次询问。

## 十三、七天准备计划

### 第 1 天：项目主线

- 不看文档讲 30 秒、1 分钟、3 分钟版本；
- 画架构图和数据模型；
- 跑一遍完整演示。

### 第 2 天：FastAPI 与 SQLAlchemy

- 读 API → Service → Repository 调用链；
- 掌握 Depends、AsyncSession、flush/commit/rollback；
- 手写创建项目事务伪代码。

### 第 3 天：认证与权限

- 手画登录、刷新、注销时序；
- 解释 `sub/sid/jti/type`；
- 讲清系统 RBAC、项目角色、资源属性授权。

### 第 4 天：事务与并发

- 手写乐观锁 SQL；
- 推演两个并发刷新、两个并发 Issue 更新、两个并发 Review；
- 解释幂等和行锁。

### 第 5 天：MySQL、Redis、Celery

- 复习索引、事务隔离、行锁；
- 解释缓存失效、限流和降级；
- 讲清 commit 后入队窗口与 Outbox。

### 第 6 天：测试、监控和部署

- 读 5 个代表性测试；
- 解释真实 MySQL 测试、Alembic 回滚；
- 打开指标和 Docker Compose。

### 第 7 天：完整模拟

- 手机录制一次 30 分钟模拟面试；
- 删除口头禅和模糊词；
- 对每个“不知道”补一条准确边界；
- 最后只保留自己真正能解释的简历条目。

## 十四、面试前最终检查

- [ ] 能在 1 分钟内完整介绍项目；
- [ ] 能画 API/Service/Repository 分层；
- [ ] 能解释双层权限和跨项目隔离；
- [ ] 能写出 Issue 乐观锁 SQL；
- [ ] 能推演 Review 并发审批；
- [ ] 能解释 JWT 服务端会话和轮换；
- [ ] 能说明 Redis/Celery 故障边界；
- [ ] 能说明 Outbox 是当前可改进点；
- [ ] 能讲出 3 个真实测试；
- [ ] 能主动说清项目没有生产流量和浏览器 E2E；
- [ ] 能快速定位核心代码；
- [ ] 简历中的每个技术名词都能接受连续三次追问。

当以上内容都能脱稿表达时，DevFlow 就不仅是“写在简历上的项目”，而是可以在后端面试中真正展开讨论的项目。
