<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usersApi } from '@/api/users'
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import { useAuthStore } from '@/stores/auth'
import type { User } from '@/types/api'
import { getErrorMessage } from '@/utils/error'
import { formatDateTime, initials } from '@/utils/format'

const auth = useAuthStore()
const loading = ref(false)
const users = ref<User[]>([])
const total = ref(0)
const keyword = ref('')
const pagination = reactive({ page: 1, pageSize: 15 })
const visibleUsers = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return users.value
  return users.value.filter(
    (user) =>
      user.username.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query) ||
      String(user.id) === query,
  )
})

async function load() {
  loading.value = true
  try {
    const { data } = await usersApi.list({ page: pagination.page, page_size: pagination.pageSize })
    users.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '用户列表加载失败'))
  } finally {
    loading.value = false
  }
}

async function toggleStatus(user: User) {
  const nextActive = !user.is_active
  const action = nextActive ? '启用' : '停用'
  await ElMessageBox.confirm(`确认${action}用户“${user.username}”吗？`, `${action}用户`, {
    type: nextActive ? 'info' : 'warning',
  })
  try {
    await usersApi.updateStatus(user.id, nextActive)
    ElMessage.success(`用户已${action}`)
    await load()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, `${action}用户失败`))
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="用户管理" description="查看平台用户并维护账号启用状态。" />
    <section class="surface-card card-padding">
      <div class="admin-toolbar">
        <el-input v-model.trim="keyword" clearable placeholder="筛选当前页用户名、邮箱或 ID" />
        <span class="subtle">当前接口未返回系统角色；管理员入口依据权限编码控制。</span>
      </div>
      <el-table v-loading="loading" :data="visibleUsers">
        <el-table-column label="用户" min-width="250">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="38" :src="row.avatar || undefined">{{ initials(row.username) }}</el-avatar>
              <div><strong>{{ row.username }}</strong><small>{{ row.email }}</small></div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="id" label="用户 ID" width="100">
          <template #default="{ row }">#{{ row.id }}</template>
        </el-table-column>
        <el-table-column label="账号状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '正常' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="175">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" align="right">
          <template #default="{ row }">
            <el-button
              link
              :type="row.is_active ? 'danger' : 'primary'"
              :disabled="row.id === auth.user?.id"
              @click="toggleStatus(row)"
            >
              {{ row.is_active ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
        <template #empty><EmptyState title="没有匹配用户" description="调整当前页筛选条件。" /></template>
      </el-table>
      <div v-if="total > pagination.pageSize" class="pagination-row">
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
.admin-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.admin-toolbar .el-input {
  width: min(360px, 100%);
}

.admin-toolbar span {
  font-size: 12px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-cell div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.user-cell small {
  color: var(--muted);
}

@media (max-width: 720px) {
  .admin-toolbar { align-items: stretch; flex-direction: column; }
}
</style>
