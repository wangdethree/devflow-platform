<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { notificationsApi } from '@/api/notifications'
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import { useNotificationStore } from '@/stores/notifications'
import type { Notification } from '@/types/api'
import { getErrorMessage } from '@/utils/error'
import { relativeTime } from '@/utils/format'

const router = useRouter()
const notificationStore = useNotificationStore()
const loading = ref(false)
const items = ref<Notification[]>([])
const total = ref(0)
const filter = ref<'all' | 'unread' | 'read'>('all')
const pagination = reactive({ page: 1, pageSize: 15 })
const hasUnread = computed(() => items.value.some((item) => !item.is_read))

async function load() {
  loading.value = true
  try {
    const { data } = await notificationsApi.list({
      page: pagination.page,
      page_size: pagination.pageSize,
      is_read: filter.value === 'all' ? undefined : filter.value === 'read',
    })
    items.value = data.items
    total.value = data.total
    await notificationStore.refreshUnreadCount()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '通知加载失败'))
  } finally {
    loading.value = false
  }
}

async function openNotification(item: Notification) {
  try {
    if (!item.is_read) {
      await notificationsApi.markRead(item.id)
      item.is_read = true
      notificationStore.decrementUnread()
    }
    if (item.target_type.toLowerCase() === 'issue') await router.push(`/issues/${item.target_id}`)
    else if (item.target_type.toLowerCase() === 'project') await router.push(`/projects/${item.target_id}`)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '通知处理失败'))
  }
}

async function markAllRead() {
  try {
    const { data } = await notificationsApi.markAllRead()
    ElMessage.success(`已将 ${data.updated_count} 条通知标为已读`)
    notificationStore.clearUnread()
    await load()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '全部标记已读失败'))
  }
}

function changeFilter() {
  pagination.page = 1
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="通知中心" description="集中查看任务分配、状态变化与评审提醒。">
      <template #actions>
        <el-button :icon="Check" :disabled="!hasUnread && notificationStore.unreadCount === 0" @click="markAllRead">
          全部标为已读
        </el-button>
      </template>
    </PageHeader>

    <section class="surface-card">
      <div class="notification-toolbar">
        <el-segmented v-model="filter" :options="[
          { label: '全部', value: 'all' },
          { label: '未读', value: 'unread' },
          { label: '已读', value: 'read' },
        ]" @change="changeFilter" />
      </div>
      <div v-loading="loading">
        <div v-if="items.length" class="notification-list">
          <button v-for="item in items" :key="item.id" type="button" :class="{ unread: !item.is_read }" @click="openNotification(item)">
            <span class="notification-icon"><el-icon><Bell /></el-icon></span>
            <span class="notification-copy">
              <strong>{{ item.content }}</strong>
              <small>{{ item.type }} · {{ relativeTime(item.created_at) }}</small>
            </span>
            <span v-if="!item.is_read" class="unread-dot" aria-label="未读" />
          </button>
        </div>
        <EmptyState v-else title="没有通知" description="与你相关的任务和评审动态会出现在这里。" />
      </div>
      <div v-if="total > pagination.pageSize" class="pagination-row notification-pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          layout="total, prev, pager, next"
          :page-size="pagination.pageSize"
          :total="total"
          @current-change="load"
        />
      </div>
    </section>
  </div>
</template>

<style scoped>
.notification-toolbar {
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
}

.notification-list button {
  display: grid;
  width: 100%;
  grid-template-columns: 42px minmax(0, 1fr) 10px;
  align-items: center;
  gap: 14px;
  padding: 18px 22px;
  border: 0;
  border-bottom: 1px solid var(--border);
  background: white;
  cursor: pointer;
  text-align: left;
}

.notification-list button:hover {
  background: #f8faff;
}

.notification-list button.unread {
  background: #f5f8ff;
}

.notification-icon {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 10px;
  background: #eaf1ff;
  color: #2368df;
}

.notification-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
}

.notification-copy strong {
  overflow: hidden;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-copy small {
  color: var(--muted);
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2368df;
}

.notification-pagination {
  padding: 18px 22px;
}
</style>
