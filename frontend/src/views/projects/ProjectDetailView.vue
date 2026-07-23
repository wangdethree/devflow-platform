<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Delete, Edit, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { issuesApi } from '@/api/issues'
import { projectsApi } from '@/api/projects'
import EmptyState from '@/components/EmptyState.vue'
import IssueFormDialog from '@/components/IssueFormDialog.vue'
import ProjectFormDialog from '@/components/ProjectFormDialog.vue'
import StatusTag from '@/components/StatusTag.vue'
import { useAuthStore } from '@/stores/auth'
import type { Issue, Project, ProjectMember, ProjectRole } from '@/types/api'
import { getErrorMessage } from '@/utils/error'
import { formatDateTime, initials } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const projectId = Number(route.params.id)
const loading = ref(true)
const project = ref<Project | null>(null)
const members = ref<ProjectMember[]>([])
const issues = ref<Issue[]>([])
const activeTab = ref('issues')
const editOpen = ref(false)
const issueOpen = ref(false)
const memberOpen = ref(false)
const memberSaving = ref(false)
const memberForm = reactive<{ user_id: number | undefined; role: ProjectRole }>({
  user_id: undefined,
  role: 'Developer',
})

const currentMember = computed(() => members.value.find((member) => member.user_id === auth.user?.id))
const canManageProject = computed(() => currentMember.value?.role === 'Owner')
const canWrite = computed(() => ['Owner', 'Developer'].includes(currentMember.value?.role || ''))

async function load() {
  if (!Number.isInteger(projectId)) {
    await router.replace('/projects')
    return
  }
  loading.value = true
  try {
    const [projectResponse, memberResponse, issueResponse] = await Promise.all([
      projectsApi.get(projectId),
      projectsApi.members(projectId),
      issuesApi.list({ project_id: projectId, page: 1, page_size: 100 }),
    ])
    project.value = projectResponse.data
    members.value = memberResponse.data.items
    issues.value = issueResponse.data.items
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '项目详情加载失败'))
  } finally {
    loading.value = false
  }
}

async function removeProject() {
  if (!project.value) return
  await ElMessageBox.confirm(
    `删除“${project.value.name}”后将无法恢复，确认继续吗？`,
    '删除项目',
    { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
  )
  try {
    await projectsApi.remove(projectId)
    ElMessage.success('项目已删除')
    await router.replace('/projects')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '删除项目失败'))
  }
}

async function addMember() {
  if (!memberForm.user_id) {
    ElMessage.warning('请输入有效用户 ID')
    return
  }
  memberSaving.value = true
  try {
    await projectsApi.addMember(projectId, {
      user_id: memberForm.user_id,
      role: memberForm.role,
    })
    ElMessage.success('成员已添加')
    memberOpen.value = false
    memberForm.user_id = undefined
    await load()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '添加成员失败'))
  } finally {
    memberSaving.value = false
  }
}

async function changeRole(member: ProjectMember, role: ProjectRole) {
  try {
    await projectsApi.updateMember(projectId, member.user_id, role)
    ElMessage.success('成员角色已更新')
    await load()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '更新角色失败'))
    await load()
  }
}

async function removeMember(member: ProjectMember) {
  await ElMessageBox.confirm(`确认将 ${member.username} 移出项目吗？`, '移除成员', {
    type: 'warning',
  })
  try {
    await projectsApi.removeMember(projectId, member.user_id)
    ElMessage.success('成员已移除')
    await load()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '移除成员失败'))
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <template v-if="project">
      <div class="detail-heading">
        <div>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/projects' }">项目</el-breadcrumb-item>
            <el-breadcrumb-item>{{ project.name }}</el-breadcrumb-item>
          </el-breadcrumb>
          <div class="title-row">
            <h1>{{ project.name }}</h1>
            <StatusTag :value="project.status" />
          </div>
          <p>{{ project.description || '暂无项目说明' }}</p>
        </div>
        <div v-if="canManageProject" class="toolbar">
          <el-button :icon="Edit" @click="editOpen = true">编辑</el-button>
          <el-button :icon="Delete" type="danger" plain @click="removeProject">删除</el-button>
        </div>
      </div>

      <section class="surface-card">
        <el-tabs v-model="activeTab" class="detail-tabs">
          <el-tab-pane label="任务" name="issues">
            <div class="tab-toolbar">
              <div>
                <h2>项目任务</h2>
                <p>共 {{ issues.length }} 条任务</p>
              </div>
              <el-button v-if="canWrite" type="primary" :icon="Plus" @click="issueOpen = true">创建任务</el-button>
            </div>
            <el-table v-if="issues.length" :data="issues" @row-click="(row: Issue) => router.push(`/issues/${row.id}`)">
              <el-table-column label="任务" min-width="260">
                <template #default="{ row }"><span class="table-link">#{{ row.id }} {{ row.title }}</span></template>
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
              <el-table-column label="负责人" width="130">
                <template #default="{ row }">
                  {{ members.find((member) => member.user_id === row.assignee_id)?.username || '未分配' }}
                </template>
              </el-table-column>
            </el-table>
            <EmptyState v-else title="项目还没有任务" description="创建第一条任务，开始跟踪交付进度。">
              <el-button v-if="canWrite" type="primary" @click="issueOpen = true">创建任务</el-button>
            </EmptyState>
          </el-tab-pane>

          <el-tab-pane :label="`成员 (${members.length})`" name="members">
            <div class="tab-toolbar">
              <div><h2>项目成员</h2><p>负责人可以维护成员及项目角色。</p></div>
              <el-button v-if="canManageProject" type="primary" :icon="Plus" @click="memberOpen = true">添加成员</el-button>
            </div>
            <el-table :data="members">
              <el-table-column label="成员" min-width="230">
                <template #default="{ row }">
                  <div class="member-cell">
                    <el-avatar :size="36">{{ initials(row.username) }}</el-avatar>
                    <div><strong>{{ row.username }}</strong><small>{{ row.email }}</small></div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="角色" width="180">
                <template #default="{ row }">
                  <el-select
                    v-if="canManageProject && row.role !== 'Owner'"
                    :model-value="row.role"
                    @change="(role: ProjectRole) => changeRole(row, role)"
                  >
                    <el-option label="开发者" value="Developer" />
                    <el-option label="访客" value="Viewer" />
                  </el-select>
                  <StatusTag v-else :value="row.role" />
                </template>
              </el-table-column>
              <el-table-column label="加入时间" width="175">
                <template #default="{ row }">{{ formatDateTime(row.joined_at) }}</template>
              </el-table-column>
              <el-table-column v-if="canManageProject" label="操作" width="90" align="right">
                <template #default="{ row }">
                  <el-button v-if="row.role !== 'Owner'" link type="danger" @click.stop="removeMember(row)">移除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="概览" name="overview">
            <div class="overview-grid">
              <div><small>项目 ID</small><strong>#{{ project.id }}</strong></div>
              <div><small>负责人</small><strong>{{ members.find((m) => m.role === 'Owner')?.username || `用户 #${project.owner_id}` }}</strong></div>
              <div><small>创建时间</small><strong>{{ formatDateTime(project.created_at) }}</strong></div>
              <div><small>最近更新</small><strong>{{ formatDateTime(project.updated_at) }}</strong></div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </section>
    </template>

    <ProjectFormDialog v-model="editOpen" :project="project" @saved="load" />
    <IssueFormDialog v-if="project" v-model="issueOpen" :project-id="project.id" :members="members" @saved="load" />

    <el-dialog v-model="memberOpen" title="添加项目成员" width="min(460px, 92vw)">
      <el-alert
        title="当前后端未提供用户搜索接口，请填写用户 ID。管理员可在用户管理页查询 ID。"
        type="info"
        :closable="false"
        show-icon
      />
      <el-form label-position="top" class="member-form">
        <el-form-item label="用户 ID">
          <el-input-number v-model="memberForm.user_id" :min="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="项目角色">
          <el-radio-group v-model="memberForm.role">
            <el-radio-button value="Developer">开发者</el-radio-button>
            <el-radio-button value="Viewer">访客</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="memberOpen = false">取消</el-button>
        <el-button type="primary" :loading="memberSaving" @click="addMember">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.detail-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}

.detail-heading .el-breadcrumb {
  margin-bottom: 18px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-row h1 {
  margin-bottom: 8px;
  font-size: 27px;
}

.detail-heading p,
.tab-toolbar p {
  margin: 0;
  color: var(--muted);
}

.detail-tabs {
  padding: 4px 22px 22px;
}

.tab-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin: 10px 0 20px;
}

.tab-toolbar h2 {
  margin-bottom: 5px;
  font-size: 17px;
}

.member-cell {
  display: flex;
  align-items: center;
  gap: 11px;
}

.member-cell div {
  display: flex;
  flex-direction: column;
}

.member-cell small {
  color: var(--muted);
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--border);
}

.overview-grid div {
  display: flex;
  min-height: 110px;
  flex-direction: column;
  gap: 10px;
  padding: 24px;
  background: white;
}

.overview-grid small {
  color: var(--muted);
}

.member-form {
  margin-top: 18px;
}

@media (max-width: 650px) {
  .detail-heading { align-items: stretch; flex-direction: column; }
  .overview-grid { grid-template-columns: 1fr; }
}
</style>
