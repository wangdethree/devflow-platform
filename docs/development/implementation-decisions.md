# DevFlow 实现决策记录

本文记录正式文档之间存在的差异，以及为保持当前数据库设计和业务闭环所做的最小实现决策。

## 1. 系统角色与项目角色

项目介绍早期版本提到 `Project Manager` 系统角色，需求与数据库正式设计则明确采用双层权限：系统角色为 `Admin`、`User`，项目角色为 `Owner`、`Developer`、`Viewer`。实现采用后者，避免把项目范围权限错误扩散到平台范围。

## 2. 角色名称唯一性

为了保证幂等初始化和避免同名角色造成授权歧义，`roles.name` 与 `project_roles.name` 增加唯一约束。该约束不改变既定字段和角色模型。

## 3. 项目状态

数据库文档只规定 `projects.status` 为字符串，未列出值域。当前版本收敛为 `ACTIVE`、`ARCHIVED`，默认 `ACTIVE`，避免任意字符串产生不可控状态。

## 4. 评论回复

项目介绍提到“评论回复”，但初始 12 表正式数据库模型的 `comments` 表没有 `parent_id`。当前版本实现平级 Issue 评论及本人修改、删除，不虚构树形回复关系；后续如需回复能力，应先通过独立迁移增加父评论字段。

## 5. Review 版本边界

需求分析把 Review 和通知列为 v1.1 增强能力，开发约束又将其列入本次完整验收。当前实现包含 Review 与通知，但保持模块化单体和 MySQL 持久化，不引入额外业务表。

## 6. 通知事务策略

项目邀请、Issue 分配、状态变化、Review 请求和审核结果通知都与对应主业务写入同一个 MySQL 事务。通知写入失败会回滚主业务，以保证协作事件和站内可见结果一致。事务提交成功后再尽力向 Celery 入队，由 Worker 将事件发布到用户 Redis Channel；Broker 或 Worker 不可用只影响实时分发，不回滚已经可靠落库的主业务与通知。

## 7. Issue 状态与 Review

通用状态接口仅允许相邻状态流转：`OPEN → IN_PROGRESS → REVIEW → DONE`。发起 Review 会原子地把 Issue 从 `IN_PROGRESS` 更新为 `REVIEW`；通过更新为 `DONE`，拒绝回到 `IN_PROGRESS`。重复提交相同审核结果幂等返回，不同结果返回冲突。

## 8. 认证会话

为支持 Refresh Token 轮换、重放检测与主动注销，新增第 13 张业务表 `auth_sessions`。Access Token 绑定会话 ID，受保护请求同时检查 JWT 和服务端会话；数据库只保存 Refresh Token SHA-256 摘要，不保存可直接使用的原始令牌。

## 9. 并发一致性

Issue 增加单调递增 `version`，普通修改通过条件更新实现乐观锁。Review 决策使用行锁串行判断处理状态：相同决策重试幂等成功，不重复写通知；不同决策返回冲突。发起和处理 Review 都会递增 Issue 版本。

## 10. 可观测性与压测

HTTP 指标使用路由模板而非资源 ID，控制 Prometheus 标签基数；SQL 指标只按 SELECT/INSERT/UPDATE/DELETE 等操作分类。压测结果记录环境和原始 JSON，只作为本机版本基线，不外推生产容量。

## 11. 测试数据库

自动化测试使用独立数据库 `devflow_migration_test`，每个测试按外键顺序清理数据并重新执行幂等基础数据初始化。测试不依赖开发数据库中的已有数据。
