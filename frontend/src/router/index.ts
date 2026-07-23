import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/layouts/AppLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/dashboard' },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
          meta: { title: '工作台' },
        },
        {
          path: 'projects',
          name: 'projects',
          component: () => import('@/views/projects/ProjectListView.vue'),
          meta: { title: '项目' },
        },
        {
          path: 'projects/:id',
          name: 'project-detail',
          component: () => import('@/views/projects/ProjectDetailView.vue'),
          meta: { title: '项目详情' },
        },
        {
          path: 'issues',
          name: 'issues',
          component: () => import('@/views/issues/IssueListView.vue'),
          meta: { title: '任务' },
        },
        {
          path: 'issues/:id',
          name: 'issue-detail',
          component: () => import('@/views/issues/IssueDetailView.vue'),
          meta: { title: '任务详情' },
        },
        {
          path: 'notifications',
          name: 'notifications',
          component: () => import('@/views/notifications/NotificationView.vue'),
          meta: { title: '通知' },
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/profile/ProfileView.vue'),
          meta: { title: '个人中心' },
        },
        {
          path: 'admin/users',
          name: 'admin-users',
          component: () => import('@/views/admin/UserAdminView.vue'),
          meta: { title: '用户管理', requiresAdmin: true },
        },
      ],
    },
    {
      path: '/',
      component: AuthLayout,
      children: [
        {
          path: 'login',
          name: 'login',
          component: () => import('@/views/auth/LoginView.vue'),
          meta: { title: '登录', guestOnly: true },
        },
        {
          path: 'register',
          name: 'register',
          component: () => import('@/views/auth/RegisterView.vue'),
          meta: { title: '注册', guestOnly: true },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/error/NotFoundView.vue'),
      meta: { title: '页面未找到' },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  // 首次导航先恢复用户与权限，确保刷新受保护页面时不会误跳登录。
  if (!auth.initialized) await auth.loadSession()

  document.title = `${to.meta.title || '研发协作'} · DevFlow`

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && auth.isAuthenticated) return { name: 'dashboard' }
  if (to.meta.requiresAdmin && !auth.isAdmin) return { name: 'dashboard' }
})

export default router
