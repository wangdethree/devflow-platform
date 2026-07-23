# DevFlow 前端学习指南

这份指南基于 `frontend/` 的真实代码，适合按“启动入口 → 基础设施 → 业务闭环”的顺序阅读。

## 1. Vue 工程如何启动

`npm run dev` 调用 Vite。Vite 读取 `vite.config.ts`，加载 Vue 插件、`@` 路径别名和开发端口，再以 `index.html` 为浏览器入口。`index.html` 中的 `#app` 是 Vue 根节点，`/src/main.ts` 是模块入口。

生产构建执行：

```text
npm run build
  ├─ vue-tsc -b     严格检查 TS 与 Vue 模板
  └─ vite build     编译、分包、压缩到 dist/
```

TypeScript 固定为 5.9，是因为当前 `vue-tsc 3.3.8` 不能加载 TypeScript 7 改动后的内部入口。

## 2. `main.ts` 的作用

阅读 `frontend/src/main.ts`：

1. `createApp(App)` 创建 Vue 应用。
2. 先安装 Pinia，让路由守卫可以取得 Auth Store。
3. 安装 Vue Router。
4. 全局安装 Element Plus 和中文语言包。
5. 引入 Element Plus 与项目全局样式。
6. 挂载到 `#app`。

Pinia 在 Router 之前安装是有意的，因为第一次导航时 `beforeEach` 会调用 `useAuthStore()`。

## 3. `App.vue` 的作用

`App.vue` 只保留 `<router-view />`。登录布局、主应用布局和 404 页面由 Router 决定。根组件保持很薄，避免把登录态判断和页面数据塞到同一个文件。

## 4. Vue Router 配置

`frontend/src/router/index.ts` 将路由分为：

- `AppLayout` 下的受保护业务页面；
- `AuthLayout` 下的登录、注册页面；
- 独立 404 页面。

业务路由使用懒加载，例如：

```ts
component: () => import('@/views/issues/IssueDetailView.vue')
```

这样各业务页面成为独立构建块。路由的 `meta.title` 同时驱动浏览器标题和顶部标题，`requiresAdmin` 控制管理员页面。

## 5. 路由守卫执行流程

每次导航按以下顺序执行：

```text
目标路由
  → Auth Store 是否初始化？
    → 否：loadSession()
      → 本地无 Token：结束
      → 有 Token：并发请求 /users/me 与 /users/me/permissions
  → 设置 document.title
  → 受保护路由但未登录：跳 /login?redirect=原地址
  → 已登录访问登录/注册：跳 /dashboard
  → 管理路由但无管理员权限：跳 /dashboard
  → 放行
```

登录成功会读取 `redirect` 并返回原目标地址。失效 Token 由 Axios 清理并跳登录，避免守卫和拦截器相互循环。

## 6. Pinia Auth Store

`frontend/src/stores/auth.ts` 只保存跨页面身份状态：

- `accessToken`
- `user`
- `permissions`
- `initialized`
- `isAuthenticated`
- `isAdmin`

Store 提供 `register`、`login`、`loadSession`、`logout`、`clearSession` 和 `updateUser`。项目、Issue 等页面数据没有塞进 Pinia，因为它们只属于单个页面。

管理员判断来自后端权限编码：

```ts
permissions.includes('user:read') || permissions.includes('user:manage')
```

没有硬编码用户 ID，也没有把项目角色 `Owner` 错当系统管理员。

## 7. Axios 请求拦截器

`frontend/src/api/client.ts` 创建唯一业务 Axios 实例：

- `baseURL` 来自 `VITE_API_BASE_URL`
- 超时为 15 秒
- 默认 JSON Content-Type
- 请求前从 Storage 读取最新 Access Token
- 自动拼接 `Authorization: Bearer ...`

登录 API 仍复用统一实例，但显式把请求体改成 `URLSearchParams` 和 `application/x-www-form-urlencoded`，严格匹配 FastAPI 的 `OAuth2PasswordRequestForm`。

## 8. Axios 响应拦截器

响应错误分三类：

1. **401**：对原请求标记 `_retry`，轮换 Token 后重放一次。
2. **403**：优先显示后端业务错误，不让页面白屏。
3. **其他错误**：交给页面捕获，使用 `getErrorMessage()` 展示 `message`、`detail` 或校验错误列表。

Refresh Token 是一次性的。如果多个请求同时 401，各自刷新会产生竞争。因此代码用模块级 `refreshPromise` 合并并发刷新：

```text
请求 A 401 ─┐
请求 B 401 ─┼─ 等待同一个 refreshPromise → 获取新 Access Token → 分别重放
请求 C 401 ─┘
```

这是本项目很适合面试讲解的并发控制点。

## 9. Token 保存和恢复

`frontend/src/utils/storage.ts` 统一维护两个 key，页面不直接操作 `localStorage`。

恢复流程是：

1. 页面刷新；
2. Store 从 Storage 读取 Access Token；
3. 路由守卫调用 `loadSession()`；
4. 请求当前用户和权限；
5. 成功后进入页面，失败则清空状态。

刷新后的 Token 对由拦截器一次性覆盖保存。当前实现适合学习和项目演示；生产系统应优先用 HttpOnly Cookie 保存 Refresh Token。

## 10. 页面如何调用后端

以 `ProjectListView.vue` 为例：

```text
onMounted(load)
  → projectsApi.list({ page, page_size })
  → Axios 注入 Token
  → FastAPI list_projects
  → ProjectService.list_projects
  → ProjectRepository.list_for_user
  → ProjectListResponse
  → 页面更新 items / total
```

页面只负责加载状态、筛选交互和错误提示。路径与请求结构都放在 `src/api/`，响应形状放在 `src/types/api.ts`。

## 11. TypeScript 如何对应 Pydantic

映射示例：

| Pydantic | TypeScript |
|---|---|
| `UserResponse` | `User` |
| `ProjectResponse` | `Project` |
| `ProjectMemberResponse` | `ProjectMember` |
| `IssueResponse` | `Issue` |
| `ReviewResponse` | `Review` |
| `NotificationResponse` | `Notification` |
| `ProjectListResponse` 等 | `PageResponse<T>` / `ListResponse<T>` |

Python 的 `datetime` 在 JSON 中是 ISO 字符串，因此 TypeScript 使用 `string`，交给 `formatDateTime()` 转换。枚举被定义为字符串联合类型，避免把任意字符串传给 API。

## 12. 登录完整调用链

```text
LoginView.submit
  → 表单校验
  → authStore.login(email, password)
  → authApi.login
  → POST /auth/login（form-urlencoded）
  → saveTokens
  → loadSession
    → GET /users/me
    → GET /users/me/permissions
  → 跳 redirect 或 /dashboard
```

后端错误如“用户名或密码错误”由统一错误提取函数显示。按钮在接口完成前保持 loading，防止重复提交。

## 13. 项目列表完整调用链

项目列表 API 没有搜索或状态过滤参数，因此页面：

1. 服务端只处理分页；
2. 名称和状态只过滤当前页；
3. 页面明确提示这一限制；
4. 为展示当前角色，对当前页每个项目读取成员并找到当前用户。

这是权衡，不是理想终态。推荐后端给列表响应增加 `current_user_role`，同时增加 `keyword` 和 `status` Query 参数，减少 N+1 请求。

## 14. 创建 Issue 完整调用链

在全局 Issue 页，用户先选择项目；在项目详情页，项目已确定。页面读取该项目成员，只让负责人选择 Owner 或 Developer。

```text
IssueFormDialog
  → IssueForm 类型约束字段
  → issuesApi.create(projectId, payload)
  → POST /projects/{projectId}/issues
  → 后端确认创建者角色和 assignee 项目成员身份
  → 创建 Issue，并在有负责人时创建通知
  → 前端关闭 Dialog、提示成功、刷新列表
```

创建表单不提供 `status`，因为真实 `IssueCreateRequest` 不允许客户端设置状态。

## 15. Review 页面刷新逻辑

只有可写用户、且 Issue 为 `IN_PROGRESS` 时显示“发起 Review”。审核人来自项目中的 Owner/Developer，并排除当前用户。

发起请求：

```text
POST /issues/{issue_id}/reviews
{ reviewer_id, issue_version }
```

后端在同一事务中创建 Review，并把 Issue 改成 `REVIEW`。指定审核人用：

```text
PATCH /reviews/{review_id}
{ status: APPROVED | REJECTED, comment }
```

后端通过时把 Issue 改成 `DONE`，驳回时改回 `IN_PROGRESS`。每次发起或处理后，前端调用一次 `load()`，同时刷新 Issue、评论、成员和 Review，避免局部状态不一致。

## 16. 通知未读数量同步

`notificationStore` 只保存 `unreadCount`：

- 主布局挂载时刷新；
- 通知页加载时再次校准；
- 单条已读后本地减一；
- 全部已读后立即清零，再从后端校准。

未知 `target_type` 不跳转，只标记已读并保留内容。Review 通知目前也不跳转，因为其目标 ID 是 Review ID，而后端没有按 Review ID 返回所属 Issue 的查询接口。

## 17. 推荐断点位置

建议在浏览器 DevTools 或 IDE 中设置以下断点：

1. `api/client.ts` 请求拦截器：观察 Token 注入。
2. `api/client.ts` 401 分支：观察 `_retry` 和 `refreshPromise`。
3. `stores/auth.ts` 的 `loadSession`：观察刷新恢复。
4. `router/index.ts` 的 `beforeEach`：观察 redirect。
5. `IssueFormDialog.vue` 的 `submit`：观察请求字段。
6. `IssueDetailView.vue` 的 `createReview` / `decideReview`：观察 version 和状态刷新。
7. `NotificationView.vue` 的 `openNotification`：观察已读数同步。

后端可对应断在 `AuthService.login`、`IssueService.transition_status`、`ReviewService.decide_review`。

## 18. 推荐代码阅读顺序

1. `frontend/src/main.ts`
2. `frontend/src/App.vue`
3. `frontend/src/router/index.ts`
4. `frontend/src/stores/auth.ts`
5. `frontend/src/api/client.ts`
6. `frontend/src/types/api.ts`
7. `frontend/src/layouts/AppLayout.vue`
8. `frontend/src/views/auth/LoginView.vue`
9. `frontend/src/views/projects/ProjectListView.vue`
10. `frontend/src/views/projects/ProjectDetailView.vue`
11. `frontend/src/views/issues/IssueListView.vue`
12. `frontend/src/views/issues/IssueDetailView.vue`
13. 通知、资料和管理员页面
14. `docs/development/07-frontend-api-mapping.md`

## 19. 每个模块的小修改练习

1. **入口**：在浏览器标题中增加当前环境标记。
2. **Router**：增加无需登录的“关于”页面。
3. **Auth Store**：增加会话恢复的骨架屏状态。
4. **Axios**：对用户主动取消请求不显示错误 Toast。
5. **类型**：为 API 错误码定义字符串联合类型。
6. **工作台**：增加“分配给我且处于 REVIEW”的真实数量。
7. **项目列表**：在后端新增关键词参数后移除当前页筛选提示。
8. **项目详情**：把成员添加改为后端用户搜索选择器。
9. **Issue 列表**：选择项目后把负责人 ID 输入框改成成员选择器。
10. **Issue 详情**：给 409 冲突增加专门提示和差异对比。
11. **评论**：增加 Ctrl/Cmd + Enter 提交。
12. **Review**：后端增加发起说明后扩展 Schema 和表单。
13. **通知**：后端返回 `link` 或 `issue_id` 后完善 Review 通知跳转。
14. **管理员**：后端返回系统角色后增加角色标签。
15. **测试**：给错误提取和状态按钮可见性增加单元测试。

## 20. 前端面试可能追问

### 为什么不把所有数据放 Pinia？

项目和 Issue 列表属于路由页面，离开后不一定需要保留。放组件内部可减少全局状态同步和缓存失效问题。只有身份和通知未读数跨页面共享。

### 为什么 401 只重试一次？

`_retry` 防止刷新接口失败或新 Token 仍无效时无限递归。失败后统一清理会话并跳登录。

### 为什么要合并并发刷新？

后端采用 Refresh Token 轮换。多个请求同时消费同一个一次性 Token，只有第一个可能成功，其余会误判登录失效。共享 Promise 保证只刷新一次。

### 前端权限能保证安全吗？

不能。前端权限只隐藏无效操作；请求可被手工构造。项目角色和系统权限必须由后端再次校验，本项目的 Service 层就是最终边界。

### 为什么 Issue 更新携带 version？

这是乐观锁。两个用户同时读取 v1 后，先提交者得到 v2，后提交者仍携带 v1 时后端返回冲突，避免静默覆盖。

### 为什么不直接提供状态下拉框？

后端有明确状态机。任意选择会制造大量必然失败的请求，也弱化业务含义。前端只暴露合理的下一动作，后端仍做最终校验。

### 如何继续提升工程质量？

可以增加按路由粒度的组件测试、Playwright 端到端测试、自动生成 OpenAPI 类型、细粒度 Element Plus 按需引入、错误监控与基于权限声明的操作组件。当前版本优先保证业务闭环和代码可读性。
