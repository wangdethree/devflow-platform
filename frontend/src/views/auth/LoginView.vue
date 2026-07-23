<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/utils/error'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({ email: '', password: '' })
const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function submit() {
  if (!(await formRef.value?.validate().catch(() => false))) return
  loading.value = true
  try {
    await auth.login(form.email, form.password)
    ElMessage.success('欢迎回来')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    await router.replace(redirect)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '登录失败，请检查邮箱和密码'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-card">
    <h2>登录 DevFlow</h2>
    <p>进入你的团队研发工作台</p>
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="auth-form" @keyup.enter="submit">
      <el-form-item label="邮箱" prop="email">
        <el-input v-model.trim="form.email" size="large" placeholder="name@company.com" autocomplete="email" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="form.password"
          size="large"
          type="password"
          show-password
          placeholder="输入登录密码"
          autocomplete="current-password"
        />
      </el-form-item>
      <el-button type="primary" size="large" class="auth-submit" :loading="loading" @click="submit">
        登录
      </el-button>
    </el-form>
    <p class="auth-switch">还没有账号？<router-link to="/register">立即注册</router-link></p>
  </div>
</template>
