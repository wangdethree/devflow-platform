<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { projectsApi } from '@/api/projects'
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import ProjectFormDialog from '@/components/ProjectFormDialog.vue'
import StatusTag from '@/components/StatusTag.vue'
import { useAuthStore } from '@/stores/auth'
import type { Project, ProjectRole } from '@/types/api'
import { getErrorMessage } from '@/utils/error'
import { formatDateTime } from '@/utils/format'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const dialogOpen = ref(false)
const items = ref<Project[]>([])
const roles = ref<Record<number, ProjectRole>>({})
const total = ref(0)
const filters = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 10 })

const visibleItems = computed(() => {
  const keyword = filters.keyword.toLowerCase()
  return items.value.filter(
    (project) =>
      (!filters.status || project.status === filters.status) &&
      (!keyword ||
        project.name.toLowerCase().includes(keyword) ||
        project.description?.toLowerCase().includes(keyword)),
  )
})

async function load() {
  loading.value = true
  try {
    const { data } = await projectsApi.list({ page: pagination.page, page_size: pagination.pageSize })
    items.value = data.items
    total.value = data.total
    const rolePairs = await Promise.all(
      data.items.map(async (project) => {
        try {
          const response = await projectsApi.members(project.id)
          const member = response.data.items.find((item) => item.user_id === auth.user?.id)
          return [project.id, member?.role] as const
        } catch {
          return [project.id, undefined] as const
        }
      }),
    )
    roles.value = Object.fromEntries(rolePairs.filter((pair): pair is readonly [number, ProjectRole] => Boolean(pair[1])))
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '项目列表加载失败'))
  } finally {
    loading.value = false
  }
}

function handleSaved() {
  pagination.page = 1
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="项目" description="集中管理团队项目、成员与交付任务。">
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="dialogOpen = true">创建项目</el-button>
      </template>
    </PageHeader>

    <section class="surface-card card-padding">
      <div class="toolbar project-toolbar">
        <el-input v-model.trim="filters.keyword" :prefix-icon="Search" clearable placeholder="筛选当前页项目" />
        <el-select v-model="filters.status" clearable placeholder="全部状态">
          <el-option label="进行中" value="ACTIVE" />
          <el-option label="已归档" value="ARCHIVED" />
        </el-select>
        <span class="subtle client-filter-tip">名称和状态筛选作用于当前页</span>
      </div>

      <el-table
        v-loading="loading"
        :data="visibleItems"
        style="width: 100%"
        @row-click="(row: Project) => router.push(`/projects/${row.id}`)"
      >
        <el-table-column label="项目" min-width="230">
          <template #default="{ row }">
            <div class="project-cell">
              <span>{{ row.name.slice(0, 1).toUpperCase() }}</span>
              <div>
                <strong class="table-link">{{ row.name }}</strong>
                <small>{{ row.description || '暂无项目说明' }}</small>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="我的角色" width="110">
          <template #default="{ row }">
            <StatusTag v-if="roles[row.id]" :value="roles[row.id] || '未知'" />
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="105">
          <template #default="{ row }"><StatusTag :value="row.status" /></template>
        </el-table-column>
        <el-table-column label="创建时间" width="175">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="router.push(`/projects/${row.id}`)">进入</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <EmptyState title="没有匹配的项目" description="调整筛选条件，或创建一个新项目。" />
        </template>
      </el-table>

      <div v-if="total > pagination.pageSize" class="pagination-row">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          layout="total, prev, pager, next"
          :total="total"
          @current-change="load"
        />
      </div>
    </section>

    <ProjectFormDialog v-model="dialogOpen" @saved="handleSaved" />
  </div>
</template>

<style scoped>
.project-toolbar {
  margin-bottom: 18px;
}

.project-toolbar .el-input {
  width: min(320px, 100%);
}

.project-toolbar .el-select {
  width: 150px;
}

.client-filter-tip {
  margin-left: auto;
  font-size: 12px;
}

.project-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-cell > span {
  display: grid;
  width: 38px;
  height: 38px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 9px;
  background: #edf2fa;
  color: #35527d;
  font-weight: 700;
}

.project-cell div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.project-cell small {
  max-width: 560px;
  overflow: hidden;
  color: var(--muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
