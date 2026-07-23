<script setup lang="ts">
import { reactive, ref, watchEffect } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authApi } from '@/api/auth'
import { usersApi } from '@/api/users'
import PageHeader from '@/components/PageHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/utils/error'
import { formatDateTime, initials } from '@/utils/format'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const formRef = ref<FormInstance>()
const saving = ref(false)
const form = reactive({ username: '', email: '', avatar: '' })
const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名需为 2–50 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' },
  ],
  avatar: [{ type: 'url', message: '请输入有效的头像 URL', trigger: 'blur' }],
}

watchEffect(() => {
  form.username = auth.user?.username || ''
  form.email = auth.user?.email || ''
  form.avatar = auth.user?.avatar || ''
})

async function save() {
  if (!(await formRef.value?.validate().catch(() => false))) return
  saving.value = true
  try {
    const { data } = await usersApi.updateMe({
      username: form.username,
      email: form.email,
      avatar: form.avatar || null,
    })
    auth.updateUser(data)
    ElMessage.success('个人资料已更新')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '个人资料更新失败'))
  } finally {
    saving.value = false
  }
}

async function logoutAll() {
  await ElMessageBox.confirm('这会让所有设备上的登录会话失效，确认继续吗？', '退出全部设备', {
    type: 'warning',
  })
  try {
    const { data } = await authApi.logoutAll()
    auth.clearSession()
    ElMessage.success(`已注销 ${data.revoked_sessions} 个会话`)
    await router.replace('/login')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '注销全部设备失败'))
  }
}
</script>

<template>
  <div>
    <PageHeader title="个人中心" description="维护账号资料与登录安全。" />
    <div class="profile-grid">
      <section class="surface-card profile-summary">
        <el-avatar :size="82" :src="auth.user?.avatar || undefined">{{ initials(auth.user?.username) }}</el-avatar>
        <h2>{{ auth.user?.username }}</h2>
        <p>{{ auth.user?.email }}</p>
        <el-tag :type="auth.user?.is_active ? 'success' : 'danger'">
          {{ auth.user?.is_active ? '账号正常' : '账号已停用' }}
        </el-tag>
        <dl>
          <div><dt>用户 ID</dt><dd>#{{ auth.user?.id }}</dd></div>
          <div><dt>加入时间</dt><dd>{{ formatDateTime(auth.user?.created_at) }}</dd></div>
        </dl>
      </section>

      <div class="profile-main">
        <section class="surface-card card-padding">
          <div class="section-heading"><h2>基本资料</h2></div>
          <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
            <el-form-item label="用户名" prop="username">
              <el-input v-model.trim="form.username" maxlength="50" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model.trim="form.email" />
            </el-form-item>
            <el-form-item label="头像 URL" prop="avatar">
              <el-input v-model.trim="form.avatar" placeholder="https://example.com/avatar.png" />
            </el-form-item>
            <el-button type="primary" :loading="saving" @click="save">保存修改</el-button>
          </el-form>
        </section>

        <section class="surface-card card-padding danger-zone">
          <div>
            <h2>账号安全</h2>
            <p>撤销当前账号在所有设备上的会话，需要重新登录。</p>
          </div>
          <el-button type="danger" plain @click="logoutAll">退出全部设备</el-button>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  align-items: start;
  gap: 18px;
}

.profile-summary {
  padding: 30px 24px;
  text-align: center;
}

.profile-summary h2 {
  margin: 16px 0 5px;
}

.profile-summary > p {
  color: var(--muted);
}

.profile-summary dl {
  margin: 28px 0 0;
  text-align: left;
}

.profile-summary dl div {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-top: 1px solid var(--border);
}

.profile-summary dt {
  color: var(--muted);
}

.profile-summary dd {
  margin: 0;
}

.profile-main {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.profile-main form {
  max-width: 620px;
}

.danger-zone {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.danger-zone h2 {
  margin-bottom: 6px;
  font-size: 17px;
}

.danger-zone p {
  margin: 0;
  color: var(--muted);
}

@media (max-width: 760px) {
  .profile-grid { grid-template-columns: 1fr; }
  .danger-zone { align-items: stretch; flex-direction: column; }
}
</style>
