<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Bell,
  Briefcase,
  Expand,
  Fold,
  House,
  List,
  Setting,
  User,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notifications'
import { initials } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const notifications = useNotificationStore()
const collapsed = ref(false)
const drawerOpen = ref(false)

const menuItems = computed(() => [
  { path: '/dashboard', label: '工作台', icon: House },
  { path: '/projects', label: '项目', icon: Briefcase },
  { path: '/issues', label: '任务', icon: List },
  { path: '/notifications', label: '通知', icon: Bell },
  { path: '/profile', label: '个人资料', icon: User },
  ...(auth.isAdmin ? [{ path: '/admin/users', label: '用户管理', icon: Setting }] : []),
])

function navigate(path: string) {
  drawerOpen.value = false
  router.push(path)
}

async function handleCommand(command: string) {
  if (command === 'profile') await router.push('/profile')
  if (command === 'logout') {
    await auth.logout()
    await router.replace('/login')
  }
}

onMounted(() => {
  notifications.refreshUnreadCount().catch(() => undefined)
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar desktop-sidebar" :class="{ collapsed }">
      <div class="sidebar-logo" @click="navigate('/dashboard')">
        <span class="brand-mark small">DF</span>
        <span v-if="!collapsed" class="brand-name">DevFlow</span>
      </div>
      <nav class="side-nav" aria-label="主导航">
        <button
          v-for="item in menuItems"
          :key="item.path"
          type="button"
          :class="{ active: route.path.startsWith(item.path) }"
          @click="navigate(item.path)"
        >
          <el-badge
            :value="item.path === '/notifications' ? notifications.unreadCount : 0"
            :hidden="item.path !== '/notifications' || notifications.unreadCount === 0"
            :max="99"
          >
            <el-icon><component :is="item.icon" /></el-icon>
          </el-badge>
          <span v-if="!collapsed">{{ item.label }}</span>
        </button>
      </nav>
      <button class="collapse-button" type="button" @click="collapsed = !collapsed">
        <el-icon><component :is="collapsed ? Expand : Fold" /></el-icon>
        <span v-if="!collapsed">收起导航</span>
      </button>
    </aside>

    <el-drawer v-model="drawerOpen" direction="ltr" size="248px" :with-header="false" class="mobile-drawer">
      <aside class="sidebar mobile-sidebar">
        <div class="sidebar-logo">
          <span class="brand-mark small">DF</span>
          <span class="brand-name">DevFlow</span>
        </div>
        <nav class="side-nav">
          <button
            v-for="item in menuItems"
            :key="item.path"
            type="button"
            :class="{ active: route.path.startsWith(item.path) }"
            @click="navigate(item.path)"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </button>
        </nav>
      </aside>
    </el-drawer>

    <div class="app-main" :class="{ 'sidebar-collapsed': collapsed }">
      <header class="topbar">
        <button class="mobile-menu-button" type="button" aria-label="打开导航" @click="drawerOpen = true">
          <el-icon><Expand /></el-icon>
        </button>
        <div class="topbar-title">
          <span>{{ route.meta.title }}</span>
        </div>
        <div class="topbar-actions">
          <button class="icon-button" type="button" aria-label="查看通知" @click="navigate('/notifications')">
            <el-badge :value="notifications.unreadCount" :hidden="notifications.unreadCount === 0" :max="99">
              <el-icon><Bell /></el-icon>
            </el-badge>
          </button>
          <el-dropdown trigger="click" @command="handleCommand">
            <button type="button" class="user-trigger">
              <el-avatar :size="34" :src="auth.user?.avatar || undefined">{{ initials(auth.user?.username) }}</el-avatar>
              <span class="user-copy">
                <strong>{{ auth.user?.username }}</strong>
                <small>{{ auth.user?.email }}</small>
              </span>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      <main class="page-container">
        <router-view />
      </main>
    </div>
  </div>
</template>
