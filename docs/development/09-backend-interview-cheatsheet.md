# DevFlow 后端面试速记卡

面试前 10 分钟快速复习。详细答案见 `08-backend-interview-playbook.md`。

## 一句话定位

> DevFlow 是一个以 FastAPI 为核心的研发协作平台，重点实现了双层权限、可撤销 Token 会话、Issue 乐观锁、Review 并发审批、通知事务一致性以及可降级的 Redis/Celery 基础设施。

## 六个数字

- 13 张核心业务表；
- 7 个领域迁移阶段；
- 31 项后端自动化测试；
- 3 个项目角色：Owner、Developer、Viewer；
- 4 个 Issue 状态：OPEN、IN_PROGRESS、REVIEW、DONE；
- 2 层权限：系统 RBAC + 项目资源权限。

## 核心链路

```text
HTTP → API → Service → Repository → AsyncSession → MySQL
```

- API：协议和校验；
- Service：权限、状态机、事务；
- Repository：数据访问，不 commit；
- MySQL：事实来源；
- Redis/Celery：可降级增强能力。

## 三个必讲亮点

### 1. 双层权限

```text
系统：User → Role → Permission
项目：User → ProjectMember → ProjectRole
```

Developer 还要满足本人是 Issue creator 或 assignee。

### 2. Issue 乐观锁

```sql
UPDATE issues
SET version = version + 1, ...
WHERE id = :id AND version = :expected_version;
```

0 行更新代表旧版本冲突，拒绝静默覆盖。

### 3. Review 行锁

```text
SELECT Review FOR UPDATE
→ 校验 reviewer 和 PENDING
→ 更新 Review
→ 更新 Issue
→ 写 Notification
→ commit
```

相同结果重复请求幂等，不同结果返回冲突。

## 认证时序

```text
登录
→ Argon2 验证密码
→ 创建 auth_session
→ 签发 Access + Refresh

刷新
→ 解码 Refresh
→ 锁定 auth_session
→ 对比 Token 摘要
→ 轮换 Refresh
→ 签发新 Token 对

鉴权
→ 验证 Access 签名和类型
→ 检查 sid 对应会话
→ 检查用户状态
```

关键声明：

- `sub`：用户 ID
- `sid`：设备会话 ID
- `jti`：Token 唯一 ID
- `type`：access / refresh

## 事务口诀

> Repository flush，Service commit；跨表业务一个事务，外部投递放 commit 后。

- flush：发送 SQL，可获得主键，可回滚；
- commit：持久化事务；
- rollback：撤销当前事务；
- refresh：重新读取数据库值。

## 基础设施故障

| 故障 | 结果 |
|---|---|
| Redis 缓存失败 | 权限回源 MySQL |
| Redis 限流失败 | 记录告警，跳过限流 |
| Celery/Broker 失败 | 数据库通知仍存在，实时事件暂不可用 |
| MySQL 失败 | 核心业务不可用 |

当前消息可靠性边界：commit 与 Celery 入队之间存在窗口，可用 Outbox 改进。

## 高频问题一句话回答

- **为什么不是微服务？** 当前强事务业务更多，模块化单体更简单可靠。
- **为什么 JWT 还查数据库？** 用服务端会话换取主动撤销和账号禁用立即生效。
- **为什么 Refresh Token 存摘要？** 数据库泄露后不能直接拿它换新 Token。
- **为什么两种锁都用？** 普通编辑低冲突用乐观锁，短事务唯一审批用行锁。
- **为什么真实 MySQL 测试？** SQLite 无法准确覆盖 MySQL 外键、索引和行锁语义。
- **为什么 Service commit？** 业务动作可能跨多个 Repository，需要统一原子性。
- **为什么通知失败回滚主业务？** 数据库站内通知属于当前强一致业务结果。
- **为什么 Celery 失败不回滚？** 数据库事务已经提交，实时分发是增强能力。
- **为什么 Prometheus 不放 issue_id？** 会产生高基数时间序列。
- **前端权限安全吗？** 不安全，后端必须重新验证全部权限。

## 真实边界

- 没有生产流量，不声称高并发或百万用户；
- 没有 Outbox，不声称消息绝对不丢；
- 没有 WebSocket 消费端，不声称完整实时推送；
- 没有覆盖率数据，不声称 100% 覆盖；
- 没有微服务、Kafka、Elasticsearch；
- 已有 Vue 管理端，但没有浏览器 E2E 和公网部署。

## 代码位置

```text
认证      core/security.py + services/auth_service.py
鉴权      api/dependencies.py
项目权限  services/project_service.py
Issue     services/issue_service.py
乐观锁    repositories/issue_repository.py
Review    services/review_service.py
Redis     core/cache.py + core/rate_limit.py
Celery    tasks/notifications.py
数据库    database/session.py
测试      app/tests/
部署      docker/compose.yml
```

## 结束项目介绍时的收束

> 这个项目对我最大的训练不是堆接口，而是明确事务、权限和故障边界：哪些数据必须强一致，哪些能力可以降级，以及并发请求下如何避免静默错误。如果继续迭代，我会优先补 Outbox、权限主动失效、CI 和浏览器 E2E。
