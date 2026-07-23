# DevFlow Frontend

DevFlow 企业研发协作平台的 Vue 3 管理界面。前端直接对接仓库中的 FastAPI API，不包含 Mock 数据，覆盖认证、项目协作、Issue、评论、Review、通知、个人资料和管理员用户管理。

## 技术栈

- Vue 3、Composition API、`<script setup lang="ts">`
- Vite 8
- TypeScript 5.9（`vue-tsc` 当前兼容版本）
- Vue Router、Pinia
- Element Plus
- Axios
- Vitest

## 环境要求

- Node.js 22 或更高版本
- npm 10 或更高版本
- Python 3.11
- MySQL 8、Redis 7
- 已完成后端 Alembic 迁移和基础数据 seed

## 快速启动

先在仓库根目录启动依赖并初始化后端：

```bash
docker compose -f docker/compose.yml up -d mysql redis
cd backend
.venv/bin/alembic upgrade head
.venv/bin/python -m app.commands.seed
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开终端启动前端：

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

默认地址：

- 前端：<http://127.0.0.1:5173>
- 后端 API：<http://127.0.0.1:8000/api/v1>
- Swagger：<http://127.0.0.1:8000/docs>

`.env.local` 只需配置公开 API 地址：

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

不要在前端环境变量中放置 JWT 签名密钥、数据库密码或其他后端凭据。

## 常用命令

```bash
npm run dev
npm run typecheck
npm run test
npm run build
```

生产构建产物位于 `frontend/dist/`。当前项目未配置 ESLint，因此没有 `npm run lint`；严格 TypeScript 检查由 `vue-tsc` 执行。

## 目录结构

```text
frontend/
├── src/
│   ├── api/          # Axios 客户端和领域 API
│   ├── assets/       # 全局样式
│   ├── components/   # 通用表单、状态标签、空状态
│   ├── layouts/      # 登录布局和应用主布局
│   ├── router/       # 路由与登录/管理员守卫
│   ├── stores/       # 认证与通知未读数
│   ├── types/        # 与 Pydantic Schema 对应的类型
│   ├── utils/        # Token、错误、日期和标签工具
│   └── views/        # 业务页面
├── .env.example
├── package.json
└── vite.config.ts
```

## 页面与流程

- `/login`、`/register`：邮箱登录和注册。登录严格使用后端要求的 `application/x-www-form-urlencoded`。
- `/dashboard`：真实项目数、待处理任务、已完成任务、未读通知、最近项目和任务。
- `/projects`：参与项目、分页、当前页筛选、创建项目。
- `/projects/:id`：项目概览、Issue、成员，Owner 可编辑、删除和管理成员。
- `/issues`：跨项目分页与服务端筛选。
- `/issues/:id`：详情、编辑、软删除、评论、状态流转和 Review。
- `/notifications`：未读筛选、单条/全部已读、目标跳转。
- `/profile`：资料修改和退出全部设备。
- `/admin/users`：按权限显示，支持分页和启停用户。

Issue 不使用任意状态下拉框。页面只展示后端状态机允许的动作：

```text
OPEN → IN_PROGRESS → REVIEW
                         ├─ APPROVED → DONE
                         └─ REJECTED → IN_PROGRESS
```

## 登录与 Token

登录成功后保存 Access Token 和 Refresh Token。请求拦截器自动注入 Bearer Token；多个请求同时收到 401 时只发起一次 Refresh Token 轮换，其余请求等待并复用结果，避免一次性 Refresh Token 被并发重复消费。刷新失败会清理登录状态并返回登录页。

当前实现按项目演示需求使用 `localStorage`。生产系统更推荐由后端通过安全、HttpOnly、SameSite Cookie 保存 Refresh Token，并补充 CSP 与 XSS 防护。

## 权限说明

- 系统管理员入口由 `/users/me/permissions` 返回的 `user:read` / `user:manage` 判断，不硬编码用户 ID。
- 项目操作由成员列表中的 `Owner`、`Developer`、`Viewer` 判断。
- 前端隐藏按钮只改善交互；后端仍是最终安全边界。

当前后端没有返回用户的系统角色列表，因此管理员表格只展示真实可获得的账号状态，并明确提示角色字段缺口。项目列表 API 也没有名称/状态查询参数，页面会标注筛选仅作用于当前页。

## 常见问题

### 登录返回 `DATABASE_UNAVAILABLE`

先确认迁移已更新。认证会话功能需要 `auth_sessions` 表：

```bash
cd backend
.venv/bin/alembic upgrade head
```

### 创建项目提示项目角色未初始化

执行幂等 seed：

```bash
cd backend
.venv/bin/python -m app.commands.seed
```

### 浏览器提示 CORS

确认后端 `CORS_ORIGINS` 包含前端来源。默认示例允许：

```dotenv
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

不要把允许凭据的 CORS 配置与 `*` 来源组合使用。

### 添加成员时为什么输入用户 ID

当前后端只支持 `{ user_id, role }`，没有普通成员可用的用户搜索接口。管理员可以在用户管理页查询 ID。

### 发起 Review 为什么没有说明字段

真实 `ReviewCreateRequest` 只有 `reviewer_id` 和 `issue_version`。处理 Review 时可以通过 `comment` 提交审核意见；前端没有伪造后端不接收的发起说明。

更多调用链和学习建议见：

- `docs/development/06-frontend-learning-guide.md`
- `docs/development/07-frontend-api-mapping.md`
