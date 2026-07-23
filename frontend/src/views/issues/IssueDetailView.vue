<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotRound, Delete, Edit, Promotion } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { issuesApi } from '@/api/issues'
import { projectsApi } from '@/api/projects'
import EmptyState from '@/components/EmptyState.vue'
import IssueFormDialog from '@/components/IssueFormDialog.vue'
import StatusTag from '@/components/StatusTag.vue'
import { useAuthStore } from '@/stores/auth'
import type { Comment, Issue, Project, ProjectMember, Review, ReviewStatus } from '@/types/api'
import { getErrorMessage } from '@/utils/error'
import { formatDateTime, initials } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const issueId = Number(route.params.id)
const loading = ref(true)
const actionLoading = ref(false)
const issue = ref<Issue | null>(null)
const project = ref<Project | null>(null)
const members = ref<ProjectMember[]>([])
const comments = ref<Comment[]>([])
const reviews = ref<Review[]>([])
const editOpen = ref(false)
const reviewOpen = ref(false)
const reviewerId = ref<number>()
const commentContent = ref('')
const commentLoading = ref(false)
const editingCommentId = ref<number>()
const editingContent = ref('')

const currentMember = computed(() => members.value.find((member) => member.user_id === auth.user?.id))
const canEdit = computed(() => {
  if (!issue.value || !currentMember.value) return false
  return (
    currentMember.value.role === 'Owner' ||
    (currentMember.value.role === 'Developer' &&
      [issue.value.creator_id, issue.value.assignee_id].includes(auth.user?.id || -1))
  )
})
const canComment = computed(() => ['Owner', 'Developer'].includes(currentMember.value?.role || ''))
const reviewerCandidates = computed(() =>
  members.value.filter(
    (member) => ['Owner', 'Developer'].includes(member.role) && member.user_id !== auth.user?.id,
  ),
)
const pendingReview = computed(() => reviews.value.find((review) => review.status === 'PENDING'))

function memberName(userId: number | null) {
  if (!userId) return '未分配'
  return members.value.find((member) => member.user_id === userId)?.username || `用户 #${userId}`
}

async function load() {
  if (!Number.isInteger(issueId)) {
    await router.replace('/issues')
    return
  }
  loading.value = true
  try {
    const issueResponse = await issuesApi.get(issueId)
    issue.value = issueResponse.data
    const [projectResponse, memberResponse, commentResponse, reviewResponse] = await Promise.all([
      projectsApi.get(issue.value.project_id),
      projectsApi.members(issue.value.project_id),
      issuesApi.comments(issueId),
      issuesApi.reviews(issueId),
    ])
    project.value = projectResponse.data
    members.value = memberResponse.data.items
    comments.value = commentResponse.data.items
    reviews.value = reviewResponse.data.items
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '任务详情加载失败'))
  } finally {
    loading.value = false
  }
}

async function advanceToInProgress() {
  if (!issue.value) return
  actionLoading.value = true
  try {
    const { data } = await issuesApi.updateStatus(issue.value.id, 'IN_PROGRESS', issue.value.version)
    issue.value = data
    ElMessage.success('任务已开始处理')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '状态更新失败'))
    await load()
  } finally {
    actionLoading.value = false
  }
}

async function createReview() {
  if (!issue.value || !reviewerId.value) {
    ElMessage.warning('请选择审核人')
    return
  }
  actionLoading.value = true
  try {
    await issuesApi.createReview(issue.value.id, reviewerId.value, issue.value.version)
    reviewOpen.value = false
    reviewerId.value = undefined
    ElMessage.success('Review 已发起')
    await load()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '发起 Review 失败'))
    await load()
  } finally {
    actionLoading.value = false
  }
}

async function decideReview(review: Review, status: ReviewStatus) {
  try {
    const action = status === 'APPROVED' ? '通过' : '驳回'
    const { value } = await ElMessageBox.prompt(`填写${action}意见（可选）`, `${action} Review`, {
      inputType: 'textarea',
      confirmButtonText: `确认${action}`,
      cancelButtonText: '取消',
    })
    actionLoading.value = true
    await issuesApi.decideReview(review.id, status, value)
    ElMessage.success(`Review 已${action}`)
    await load()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(getErrorMessage(error, 'Review 处理失败'))
  } finally {
    actionLoading.value = false
  }
}

async function removeIssue() {
  if (!issue.value) return
  await ElMessageBox.confirm('删除后任务将不可见，确认继续吗？', '删除任务', { type: 'warning' })
  try {
    await issuesApi.remove(issue.value.id, issue.value.version)
    ElMessage.success('任务已删除')
    await router.replace(project.value ? `/projects/${project.value.id}` : '/issues')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '删除任务失败'))
    await load()
  }
}

async function addComment() {
  const content = commentContent.value.trim()
  if (!content) return
  commentLoading.value = true
  try {
    await issuesApi.createComment(issueId, content)
    commentContent.value = ''
    const { data } = await issuesApi.comments(issueId)
    comments.value = data.items
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '评论发布失败'))
  } finally {
    commentLoading.value = false
  }
}

function beginEditComment(comment: Comment) {
  editingCommentId.value = comment.id
  editingContent.value = comment.content
}

async function saveComment(comment: Comment) {
  if (!editingContent.value.trim()) return
  try {
    await issuesApi.updateComment(issueId, comment.id, editingContent.value.trim())
    editingCommentId.value = undefined
    const { data } = await issuesApi.comments(issueId)
    comments.value = data.items
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '评论更新失败'))
  }
}

async function removeComment(comment: Comment) {
  await ElMessageBox.confirm('确认删除这条评论吗？', '删除评论', { type: 'warning' })
  try {
    await issuesApi.removeComment(issueId, comment.id)
    comments.value = comments.value.filter((item) => item.id !== comment.id)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '评论删除失败'))
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <template v-if="issue && project">
      <el-breadcrumb separator="/" class="issue-breadcrumb">
        <el-breadcrumb-item :to="{ path: '/projects' }">项目</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: `/projects/${project.id}` }">{{ project.name }}</el-breadcrumb-item>
        <el-breadcrumb-item>#{{ issue.id }}</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="issue-heading">
        <div>
          <div class="issue-kicker">
            <StatusTag :value="issue.type" />
            <StatusTag :value="issue.priority" />
            <StatusTag :value="issue.status" />
          </div>
          <h1>{{ issue.title }}</h1>
          <p>由 {{ memberName(issue.creator_id) }} 创建 · 更新于 {{ formatDateTime(issue.updated_at) }}</p>
        </div>
        <div v-if="canEdit" class="toolbar">
          <el-button v-if="issue.status === 'OPEN'" type="primary" :loading="actionLoading" @click="advanceToInProgress">
            开始处理
          </el-button>
          <el-button
            v-if="issue.status === 'IN_PROGRESS'"
            type="primary"
            :icon="Promotion"
            :disabled="!reviewerCandidates.length"
            @click="reviewOpen = true"
          >
            发起 Review
          </el-button>
          <el-button :icon="Edit" @click="editOpen = true">编辑</el-button>
          <el-button :icon="Delete" type="danger" plain @click="removeIssue">删除</el-button>
        </div>
      </div>

      <div class="issue-layout">
        <div class="issue-main-column">
          <section class="surface-card card-padding">
            <div class="section-heading"><h2>任务描述</h2></div>
            <p v-if="issue.description" class="issue-description">{{ issue.description }}</p>
            <EmptyState v-else title="暂无任务描述" description="任务创建者尚未补充详细说明。" />
          </section>

          <section class="surface-card card-padding">
            <div class="section-heading">
              <h2>讨论（{{ comments.length }}）</h2>
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div v-if="comments.length" class="comment-list">
              <article v-for="comment in comments" :key="comment.id">
                <el-avatar :size="36">{{ initials(memberName(comment.user_id)) }}</el-avatar>
                <div class="comment-body">
                  <header>
                    <strong>{{ memberName(comment.user_id) }}</strong>
                    <time>{{ formatDateTime(comment.created_at) }}</time>
                    <span v-if="comment.user_id === auth.user?.id" class="comment-actions">
                      <el-button link @click="beginEditComment(comment)">编辑</el-button>
                      <el-button link type="danger" @click="removeComment(comment)">删除</el-button>
                    </span>
                  </header>
                  <template v-if="editingCommentId === comment.id">
                    <el-input v-model="editingContent" type="textarea" :rows="3" maxlength="5000" />
                    <div class="inline-actions">
                      <el-button size="small" @click="editingCommentId = undefined">取消</el-button>
                      <el-button size="small" type="primary" @click="saveComment(comment)">保存</el-button>
                    </div>
                  </template>
                  <p v-else>{{ comment.content }}</p>
                </div>
              </article>
            </div>
            <EmptyState v-else title="还没有讨论" description="围绕任务留下第一条评论。" />
            <div v-if="canComment" class="comment-compose">
              <el-input
                v-model="commentContent"
                type="textarea"
                :rows="3"
                maxlength="5000"
                show-word-limit
                placeholder="输入评论内容…"
              />
              <el-button type="primary" :loading="commentLoading" @click="addComment">发表评论</el-button>
            </div>
            <el-alert v-else title="Viewer 角色可查看讨论，但不能发表评论。" type="info" :closable="false" />
          </section>
        </div>

        <aside class="issue-side-column">
          <section class="surface-card card-padding">
            <div class="section-heading"><h2>任务信息</h2></div>
            <dl class="meta-list">
              <div><dt>所属项目</dt><dd><router-link :to="`/projects/${project.id}`">{{ project.name }}</router-link></dd></div>
              <div><dt>负责人</dt><dd>{{ memberName(issue.assignee_id) }}</dd></div>
              <div><dt>创建者</dt><dd>{{ memberName(issue.creator_id) }}</dd></div>
              <div><dt>版本</dt><dd>v{{ issue.version }}</dd></div>
              <div><dt>创建时间</dt><dd>{{ formatDateTime(issue.created_at) }}</dd></div>
            </dl>
          </section>

          <section class="surface-card card-padding">
            <div class="section-heading"><h2>Review 历史</h2></div>
            <div v-if="reviews.length" class="review-list">
              <article v-for="review in reviews" :key="review.id">
                <div class="review-header">
                  <StatusTag :value="review.status" />
                  <time>{{ formatDateTime(review.created_at) }}</time>
                </div>
                <p>{{ memberName(review.requester_id) }} → {{ memberName(review.reviewer_id) }}</p>
                <blockquote v-if="review.comment">{{ review.comment }}</blockquote>
                <div
                  v-if="review.status === 'PENDING' && review.reviewer_id === auth.user?.id"
                  class="review-actions"
                >
                  <el-button size="small" type="success" :loading="actionLoading" @click="decideReview(review, 'APPROVED')">
                    通过
                  </el-button>
                  <el-button size="small" type="danger" plain :loading="actionLoading" @click="decideReview(review, 'REJECTED')">
                    驳回
                  </el-button>
                </div>
              </article>
            </div>
            <EmptyState v-else title="暂无 Review" description="任务进入处理状态后可发起评审。" />
          </section>
        </aside>
      </div>

      <IssueFormDialog
        v-model="editOpen"
        :issue="issue"
        :project-id="project.id"
        :members="members"
        @saved="load"
      />

      <el-dialog v-model="reviewOpen" title="发起 Review" width="min(460px, 92vw)">
        <el-alert
          v-if="!reviewerCandidates.length"
          title="项目中没有其他可担任审核人的 Owner 或 Developer。"
          type="warning"
          :closable="false"
        />
        <el-form label-position="top">
          <el-form-item label="审核人">
            <el-select v-model="reviewerId" placeholder="选择审核人" style="width: 100%">
              <el-option
                v-for="member in reviewerCandidates"
                :key="member.user_id"
                :label="`${member.username} · ${member.role}`"
                :value="member.user_id"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="reviewOpen = false">取消</el-button>
          <el-button type="primary" :loading="actionLoading" @click="createReview">确认发起</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<style scoped>
.issue-breadcrumb {
  margin-bottom: 20px;
}

.issue-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}

.issue-kicker {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.issue-heading h1 {
  margin-bottom: 8px;
  font-size: 28px;
  letter-spacing: -0.03em;
}

.issue-heading p {
  margin: 0;
  color: var(--muted);
}

.issue-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(310px, 0.8fr);
  align-items: start;
  gap: 18px;
}

.issue-main-column,
.issue-side-column {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.issue-description {
  min-height: 110px;
  margin: 0;
  line-height: 1.8;
  white-space: pre-wrap;
}

.comment-list article {
  display: flex;
  gap: 12px;
  padding: 18px 0;
  border-bottom: 1px solid var(--border);
}

.comment-body {
  min-width: 0;
  flex: 1;
}

.comment-body header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.comment-body time,
.review-header time {
  color: var(--muted);
  font-size: 12px;
}

.comment-actions {
  margin-left: auto;
}

.comment-body p {
  margin: 0;
  line-height: 1.7;
  white-space: pre-wrap;
}

.comment-compose {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.inline-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.meta-list {
  margin: 0;
}

.meta-list div {
  display: grid;
  grid-template-columns: 88px 1fr;
  padding: 11px 0;
  border-bottom: 1px solid var(--border);
}

.meta-list div:last-child {
  border-bottom: 0;
}

.meta-list dt {
  color: var(--muted);
}

.meta-list dd {
  margin: 0;
  text-align: right;
}

.review-list article {
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}

.review-list article:last-child {
  border-bottom: 0;
}

.review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.review-list p {
  margin: 10px 0 0;
  font-size: 13px;
}

.review-list blockquote {
  margin: 10px 0 0;
  padding: 10px;
  border-left: 3px solid #cbd6e6;
  background: #f6f8fb;
  color: var(--muted);
  font-size: 13px;
}

.review-actions {
  display: flex;
  margin-top: 12px;
}

@media (max-width: 1020px) {
  .issue-layout { grid-template-columns: 1fr; }
}

@media (max-width: 650px) {
  .issue-heading { align-items: stretch; flex-direction: column; }
  .comment-compose { align-items: stretch; flex-direction: column; }
}
</style>
