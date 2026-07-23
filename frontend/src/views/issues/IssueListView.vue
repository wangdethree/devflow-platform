<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { issuesApi } from '@/api/issues'
import { projectsApi } from '@/api/projects'
import EmptyState from '@/components/EmptyState.vue'
import IssueFormDialog from '@/components/IssueFormDialog.vue'
import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import { useAuthStore } from '@/stores/auth'
import type { Issue, IssuePriority, IssueStatus, IssueType, Project, ProjectMember } from '@/types/api'
import { getErrorMessage } from '@/utils/error'
import { formatDateTime } from '@/utils/format'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const createOpen = ref(false)
const issues = ref<Issue[]>([])
const projects = ref<Project[]>([])
const selectedMembers = ref<ProjectMember[]>([])
const total = ref(0)
const filters = reactive<{
  keyword: string
  project_id?: number
  assignee_id?: number
  status?: IssueStatus
  type?: IssueType
  priority?: IssuePriority
}>({ keyword: '' })
const pagination = reactive({ page: 1, pageSize: 15 })
const selectedProject = computed(() => projects.value.find((item) => item.id === filters.project_id))
const selectedRole = computed(
  () => selectedMembers.value.find((member) => member.user_id === auth.user?.id)?.role,
)
const canCreateInSelectedProject = computed(() => ['Owner', 'Developer'].includes(selectedRole.value || ''))
const projectNames = computed(() => Object.fromEntries(projects.value.map((project) => [project.id, project.name])))

async function loadProjects() {
  const { data } = await projectsApi.list({ page: 1, page_size: 100 })
  projects.value = data.items
}

async function load() {
  loading.value = true
  try {
    const { data } = await issuesApi.list({
      ...filters,
      keyword: filters.keyword || undefined,
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    issues.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '任务列表加载失败'))
  } finally {
    loading.value = false
  }
}

function search() {
  pagination.page = 1
  load()
}

function reset() {
  filters.keyword = ''
  filters.project_id = undefined
  filters.assignee_id = undefined
  filters.status = undefined
  filters.type = undefined
  filters.priority = undefined
  search()
}

async function prepareCreate() {
  if (!filters.project_id) {
    ElMessage.info('请先在筛选区选择一个项目')
    return
  }
  try {
    if (!selectedMembers.value.length) await loadSelectedMembers(filters.project_id)
    if (!canCreateInSelectedProject.value) {
      ElMessage.warning('Viewer 角色不能创建任务')
      return
    }
    createOpen.value = true
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '项目成员加载失败'))
  }
}

async function loadSelectedMembers(projectId?: number) {
  selectedMembers.value = []
  if (!projectId) return
  const { data } = await projectsApi.members(projectId)
  selectedMembers.value = data.items
}

watch(
  () => filters.project_id,
  (projectId) => {
    filters.assignee_id = undefined
    loadSelectedMembers(projectId).catch((error) => {
      ElMessage.error(getErrorMessage(error, '项目成员加载失败'))
    })
  },
)

onMounted(async () => {
  try {
    await Promise.all([loadProjects(), load()])
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '页面加载失败'))
  }
})
</script>

<template>
  <div>
    <PageHeader title="任务" description="跨项目检索、筛选并跟踪研发任务。">
      <template #actions>
        <el-button
          v-if="!filters.project_id || canCreateInSelectedProject"
          type="primary"
          :icon="Plus"
          @click="prepareCreate"
        >
          创建任务
        </el-button>
      </template>
    </PageHeader>

    <section class="surface-card card-padding filter-card">
      <div class="issue-filters">
        <el-input
          v-model.trim="filters.keyword"
          :prefix-icon="Search"
          clearable
          placeholder="搜索任务标题或描述"
          @keyup.enter="search"
        />
        <el-select v-model="filters.project_id" clearable filterable placeholder="全部项目">
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-select v-model="filters.status" clearable placeholder="全部状态">
          <el-option label="待处理" value="OPEN" />
          <el-option label="处理中" value="IN_PROGRESS" />
          <el-option label="待评审" value="REVIEW" />
          <el-option label="已完成" value="DONE" />
        </el-select>
        <el-select v-model="filters.type" clearable placeholder="全部类型">
          <el-option label="任务" value="TASK" />
          <el-option label="需求" value="FEATURE" />
          <el-option label="缺陷" value="BUG" />
        </el-select>
        <el-select v-model="filters.priority" clearable placeholder="全部优先级">
          <el-option label="低" value="LOW" />
          <el-option label="中" value="MEDIUM" />
          <el-option label="高" value="HIGH" />
          <el-option label="紧急" value="CRITICAL" />
        </el-select>
        <el-input-number v-model="filters.assignee_id" :min="1" controls-position="right" placeholder="负责人 ID" />
        <div class="toolbar filter-actions">
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="reset">重置</el-button>
        </div>
      </div>
    </section>

    <section class="surface-card card-padding issue-table-card">
      <el-table
        v-loading="loading"
        :data="issues"
        style="width: 100%"
        @row-click="(row: Issue) => router.push(`/issues/${row.id}`)"
      >
        <el-table-column label="任务" min-width="270">
          <template #default="{ row }">
            <div class="issue-title-cell">
              <strong class="table-link">#{{ row.id }} {{ row.title }}</strong>
              <small>{{ projectNames[row.project_id] || `项目 #${row.project_id}` }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="90">
          <template #default="{ row }"><StatusTag :value="row.type" /></template>
        </el-table-column>
        <el-table-column label="优先级" width="90">
          <template #default="{ row }"><StatusTag :value="row.priority" /></template>
        </el-table-column>
        <el-table-column label="状态" width="105">
          <template #default="{ row }"><StatusTag :value="row.status" /></template>
        </el-table-column>
        <el-table-column label="负责人" width="125">
          <template #default="{ row }">{{ row.assignee_id ? `用户 #${row.assignee_id}` : '未分配' }}</template>
        </el-table-column>
        <el-table-column label="创建者" width="115">
          <template #default="{ row }">用户 #{{ row.creator_id }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="175">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <template #empty>
          <EmptyState title="没有匹配的任务" description="调整筛选条件，或在选定项目中创建任务。" />
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

    <IssueFormDialog
      v-if="selectedProject"
      v-model="createOpen"
      :project-id="selectedProject.id"
      :members="selectedMembers"
      @saved="load"
    />
  </div>
</template>

<style scoped>
.filter-card {
  margin-bottom: 18px;
}

.issue-filters {
  display: grid;
  grid-template-columns: minmax(230px, 1.6fr) repeat(4, minmax(130px, 0.8fr));
  gap: 10px;
}

.issue-filters .el-input-number {
  width: 100%;
}

.filter-actions {
  grid-column: 1 / -1;
  justify-content: flex-end;
}

.issue-title-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.issue-title-cell small {
  color: var(--muted);
}

@media (max-width: 1200px) {
  .issue-filters { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 720px) {
  .issue-filters { grid-template-columns: 1fr; }
  .filter-actions { grid-column: auto; }
}
</style>
