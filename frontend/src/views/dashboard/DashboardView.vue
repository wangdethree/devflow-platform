<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, Briefcase, CircleCheck, Clock } from '@element-plus/icons-vue'
import { issuesApi } from '@/api/issues'
import { notificationsApi } from '@/api/notifications'
import { projectsApi } from '@/api/projects'
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import type { Issue, Project } from '@/types/api'
import { formatDateTime } from '@/utils/format'
import { getErrorMessage } from '@/utils/error'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(true)
const projects = ref<Project[]>([])
const recentIssues = ref<Issue[]>([])
const stats = ref({ projects: 0, assigned: 0, done: 0, unread: 0 })

const firstName = computed(() => auth.user?.username || '伙伴')

async function load() {
  loading.value = true
  try {
    const userId = auth.user?.id
    const [projectResponse, issueResponse, assignedResponse, doneResponse, unreadResponse] =
      await Promise.all([
        projectsApi.list({ page: 1, page_size: 5 }),
        issuesApi.list({ page: 1, page_size: 6 }),
        issuesApi.list({ page: 1, page_size: 1, assignee_id: userId }),
        issuesApi.list({ page: 1, page_size: 1, assignee_id: userId, status: 'DONE' }),
        notificationsApi.unreadCount(),
      ])
    projects.value = projectResponse.data.items
    recentIssues.value = issueResponse.data.items
    stats.value = {
      projects: projectResponse.data.total,
      assigned: Math.max(assignedResponse.data.total - doneResponse.data.total, 0),
      done: doneResponse.data.total,
      unread: unreadResponse.data.unread_count,
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '工作台加载失败'))
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <PageHeader
      :title="`你好，${firstName}`"
      :description="`${auth.user?.email || ''} · 这是团队当前的研发协作概览。`"
    />

    <section class="stat-grid">
      <article class="stat-card">
        <span class="stat-icon blue"><el-icon><Briefcase /></el-icon></span>
        <div><small>参与项目</small><strong>{{ stats.projects }}</strong></div>
      </article>
      <article class="stat-card">
        <span class="stat-icon amber"><el-icon><Clock /></el-icon></span>
        <div><small>待处理任务</small><strong>{{ stats.assigned }}</strong></div>
      </article>
      <article class="stat-card">
        <span class="stat-icon green"><el-icon><CircleCheck /></el-icon></span>
        <div><small>已完成任务</small><strong>{{ stats.done }}</strong></div>
      </article>
      <article class="stat-card">
        <span class="stat-icon red"><el-icon><Bell /></el-icon></span>
        <div><small>未读通知</small><strong>{{ stats.unread }}</strong></div>
      </article>
    </section>

    <div class="dashboard-grid">
      <section class="surface-card card-padding">
        <div class="section-heading">
          <h2>最近任务</h2>
          <el-button link type="primary" @click="router.push('/issues')">查看全部</el-button>
        </div>
        <el-table v-if="recentIssues.length" :data="recentIssues" style="width: 100%" @row-click="(row: Issue) => router.push(`/issues/${row.id}`)">
          <el-table-column label="任务" min-width="210">
            <template #default="{ row }">
              <span class="table-link">#{{ row.id }} {{ row.title }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="105">
            <template #default="{ row }"><StatusTag :value="row.status" /></template>
          </el-table-column>
          <el-table-column label="优先级" width="90">
            <template #default="{ row }"><StatusTag :value="row.priority" /></template>
          </el-table-column>
          <el-table-column label="更新于" width="160">
            <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
          </el-table-column>
        </el-table>
        <EmptyState v-else title="暂无任务" description="项目中的新任务会出现在这里。" />
      </section>

      <section class="surface-card card-padding">
        <div class="section-heading">
          <h2>最近项目</h2>
          <el-button link type="primary" @click="router.push('/projects')">查看全部</el-button>
        </div>
        <div v-if="projects.length" class="project-stack">
          <button v-for="project in projects" :key="project.id" type="button" @click="router.push(`/projects/${project.id}`)">
            <span class="project-initial">{{ project.name.slice(0, 1).toUpperCase() }}</span>
            <span>
              <strong>{{ project.name }}</strong>
              <small>{{ project.description || '暂无项目说明' }}</small>
            </span>
            <StatusTag :value="project.status" />
          </button>
        </div>
        <EmptyState v-else title="暂无项目" description="创建项目后即可组织团队研发工作。" />
      </section>
    </div>
  </div>
</template>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: white;
}

.stat-icon {
  display: grid;
  width: 46px;
  height: 46px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 11px;
  font-size: 22px;
}

.stat-icon.blue { color: #2368df; background: #eaf1ff; }
.stat-icon.amber { color: #b66a00; background: #fff2d9; }
.stat-icon.green { color: #16835c; background: #e4f7ef; }
.stat-icon.red { color: #c33b45; background: #fdebed; }

.stat-card div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-card small {
  color: var(--muted);
}

.stat-card strong {
  font-size: 25px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(300px, 0.85fr);
  gap: 20px;
}

.project-stack {
  display: flex;
  flex-direction: column;
}

.project-stack button {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  border: 0;
  border-bottom: 1px solid var(--border);
  background: none;
  cursor: pointer;
  text-align: left;
}

.project-stack button:last-child {
  border-bottom: 0;
}

.project-stack button > span:nth-child(2) {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.project-stack small {
  overflow: hidden;
  color: var(--muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-initial {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 9px;
  background: #edf2fa;
  color: #35527d;
  font-weight: 750;
}

@media (max-width: 1120px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .dashboard-grid { grid-template-columns: 1fr; }
}

@media (max-width: 560px) {
  .stat-grid { grid-template-columns: 1fr; }
}
</style>
