# DevFlow API 调试指南

下文默认从仓库根目录开始，开发 API 地址为 `http://127.0.0.1:8000`。完整 Docker 模式改为 `http://127.0.0.1:8088`。

## 1. 启动命令

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload
```

可选启动 Worker：

```bash
.venv/bin/celery -A app.tasks.celery_app:celery_app \
  worker --loglevel=INFO --concurrency=2
```

## 2. Docker 命令

只启动开发依赖：

```bash
docker compose -f docker/compose.dev.yml up -d mysql redis
docker compose -f docker/compose.dev.yml ps
```

完整栈：

```bash
docker compose -p devflow-full -f docker/compose.yml up -d --build
docker compose -p devflow-full -f docker/compose.yml ps
docker compose -p devflow-full -f docker/compose.yml logs -f api worker
```

健康验证：

```bash
curl http://127.0.0.1:8088/api/v1/health
curl http://127.0.0.1:8088/api/v1/health/database
docker compose -p devflow-full -f docker/compose.yml exec worker \
  celery -A app.tasks.celery_app:celery_app inspect ping
```

## 3. Alembic 命令

```bash
cd backend
.venv/bin/alembic current
.venv/bin/alembic heads
.venv/bin/alembic upgrade head
.venv/bin/alembic check
```

只在测试库检查回滚：

```bash
MYSQL_DATABASE=devflow_migration_test .venv/bin/alembic downgrade -1
MYSQL_DATABASE=devflow_migration_test .venv/bin/alembic upgrade head
```

不要随意在含业务数据的开发库降级建表迁移。

## 4. 初始化数据

```bash
cd backend
.venv/bin/python -m app.commands.seed
```

创建可登录管理员：

```bash
.venv/bin/python -m app.commands.seed \
  --admin-email admin@example.com \
  --admin-username admin \
  --admin-password '替换为自己的安全密码'
```

该命令可以重复执行。

## 5. Swagger 调试

1. 打开 `http://127.0.0.1:8000/docs`；
2. 展开“认证”并调用注册；
3. 点击右上角 **Authorize**；
4. `username` 填邮箱，`password` 塧密码；
5. 授权后调用项目、Issue、评论、Review 和通知接口；
6. 每个响应头的 `X-Request-ID` 可用于定位服务日志。

## 6. 注册和登录

注册：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "StrongPass123!"
  }'
```

登录使用 OAuth2 Form，不是 JSON：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'username=alice@example.com' \
  --data-urlencode 'password=StrongPass123!'
```

响应：

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## 7. JWT 使用

把登录响应中的 Token 保存为调试变量：

```bash
TOKEN='<粘贴 access_token>'
curl http://127.0.0.1:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

查询系统权限：

```bash
curl http://127.0.0.1:8000/api/v1/users/me/permissions \
  -H "Authorization: Bearer $TOKEN"
```

不要把真实 Token 写入仓库、截图或日志。

## 8. 创建项目

```bash
curl -X POST http://127.0.0.1:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "DevFlow API",
    "description": "研发协作后端",
    "status": "ACTIVE"
  }'
```

记下返回的 `id`：

```bash
PROJECT_ID=1
curl "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN"
curl "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/members" \
  -H "Authorization: Bearer $TOKEN"
```

成员列表中创建者应为 Owner。

## 9. 添加成员

先注册第二个用户，记下其 `id`：

```bash
MEMBER_ID=2
curl -X POST \
  "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/members" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{
    \"user_id\": $MEMBER_ID,
    \"role\": \"Developer\"
  }"
```

修改角色：

```bash
curl -X PATCH \
  "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/members/$MEMBER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"role":"Viewer"}'
```

主负责人不能被降级或移除。

## 10. 创建和筛选 Issue

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/issues" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{
    \"title\": \"实现 JWT 认证\",
    \"description\": \"完成注册、登录与当前用户依赖\",
    \"type\": \"FEATURE\",
    \"priority\": \"HIGH\",
    \"assignee_id\": $MEMBER_ID
  }"
```

```bash
ISSUE_ID=1
curl \
  "http://127.0.0.1:8000/api/v1/issues?project_id=$PROJECT_ID&type=FEATURE&priority=HIGH&keyword=JWT&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

状态流转：

```bash
curl -X PATCH \
  "http://127.0.0.1:8000/api/v1/issues/$ISSUE_ID/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"status":"IN_PROGRESS"}'
```

从 OPEN 直接改为 DONE 会返回 `INVALID_STATE_TRANSITION`。

## 11. 评论

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/v1/issues/$ISSUE_ID/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"content":"已完成接口和测试，请协助 Review。"}'
```

用户只能修改或删除自己的评论；Viewer 只能查看。

## 12. Review

使用 Issue 创建人或负责人 Token，在 Issue 为 `IN_PROGRESS` 时发起：

```bash
REVIEWER_ID=3
curl -X POST \
  "http://127.0.0.1:8000/api/v1/issues/$ISSUE_ID/reviews" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"reviewer_id\":$REVIEWER_ID}"
```

此时 Issue 自动进入 `REVIEW`。审核人使用自己的 Token：

```bash
REVIEW_ID=1
REVIEWER_TOKEN='<审核人 Token>'
curl -X PATCH \
  "http://127.0.0.1:8000/api/v1/reviews/$REVIEW_ID" \
  -H "Authorization: Bearer $REVIEWER_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"status":"APPROVED","comment":"实现符合要求"}'
```

通过后 Issue 为 `DONE`；使用 `REJECTED` 时回到 `IN_PROGRESS`。已处理 Review 再次提交返回 409。

## 13. 通知

```bash
curl "http://127.0.0.1:8000/api/v1/notifications?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
curl http://127.0.0.1:8000/api/v1/notifications/unread-count \
  -H "Authorization: Bearer $TOKEN"
```

单条已读：

```bash
NOTIFICATION_ID=1
curl -X PATCH \
  "http://127.0.0.1:8000/api/v1/notifications/$NOTIFICATION_ID/read" \
  -H "Authorization: Bearer $TOKEN"
```

全部已读：

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/notifications/read-all \
  -H "Authorization: Bearer $TOKEN"
```

操作他人通知返回 403。

## 14. 管理员接口

普通用户调用 `/api/v1/admin/users` 返回 403。使用 seed 创建的 Admin：

```bash
curl "http://127.0.0.1:8000/api/v1/admin/users?page=1&page_size=20" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
curl -X PATCH http://127.0.0.1:8000/api/v1/admin/users/2/status \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"is_active":false}'
```

禁用用户不能再次登录。

## 15. 常见错误排查

### 数据库健康接口 503

- `docker compose -f docker/compose.dev.yml ps`；
- 检查 `backend/.env` 的主机、端口、用户和数据库；
- 查看 `docker logs devflow-mysql`；
- 在 `backend/` 执行 `.venv/bin/alembic current`。

### 注册提示基础角色未初始化

执行：

```bash
cd backend
.venv/bin/python -m app.commands.seed
```

### 401

- 登录表单的 `username` 必须填写邮箱；
- 检查 Bearer 前缀；
- Token 可能已经过期；
- 用户可能已禁用或软删除。

### 403

- 区分系统权限与项目角色；
- 检查当前用户是否仍为项目成员；
- Viewer 没有写权限；
- Developer 只能修改自己创建或负责的 Issue。

### 409

常见原因：重复邮箱、重复项目成员、非法状态跳转、重复处理 Review、尝试移除项目主负责人。

### Redis 不可用

核心 API 应继续工作，但权限缓存、登录限流和实时通知分发降级。检查：

```bash
docker compose -f docker/compose.dev.yml exec redis redis-cli ping
```

### Worker 没消费任务

```bash
docker compose -p devflow-full -f docker/compose.yml exec worker \
  celery -A app.tasks.celery_app:celery_app inspect ping
docker compose -p devflow-full -f docker/compose.yml logs --tail=100 worker
```

### Nginx 502

先确认 API 为 healthy。Nginx 配置使用 Docker DNS 动态解析；API 刚重启时可重试几秒。若端口冲突，在根 `.env` 修改 `DEVFLOW_HTTP_PORT`。

### 测试失败或污染开发库

必须先执行 `scripts/create_test_database.sh`。`conftest.py` 会在导入应用前强制使用 `devflow_migration_test`，不要手工修改为开发库。
