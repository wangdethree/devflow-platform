<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { projectsApi } from '@/api/projects'
import type { Project, ProjectForm } from '@/types/api'
import { getErrorMessage } from '@/utils/error'

const props = defineProps<{ modelValue: boolean; project?: Project | null }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean]; saved: [project: Project] }>()
const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive<ProjectForm>({ name: '', description: '', status: 'ACTIVE' })
const rules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 100, message: '项目名称需为 2–100 个字符', trigger: 'blur' },
  ],
}

watch(
  () => [props.modelValue, props.project] as const,
  () => {
    if (!props.modelValue) return
    form.name = props.project?.name || ''
    form.description = props.project?.description || ''
    form.status = props.project?.status || 'ACTIVE'
    formRef.value?.clearValidate()
  },
  { immediate: true },
)

async function submit() {
  if (!(await formRef.value?.validate().catch(() => false))) return
  loading.value = true
  try {
    const payload = { ...form, description: form.description || null }
    const { data } = props.project
      ? await projectsApi.update(props.project.id, payload)
      : await projectsApi.create(payload)
    ElMessage.success(props.project ? '项目已更新' : '项目已创建')
    emit('saved', data)
    emit('update:modelValue', false)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '保存项目失败'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="project ? '编辑项目' : '创建项目'"
    width="min(520px, 92vw)"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="项目名称" prop="name">
        <el-input v-model.trim="form.name" maxlength="100" show-word-limit placeholder="例如：移动端重构" />
      </el-form-item>
      <el-form-item label="项目说明">
        <el-input v-model="form.description" type="textarea" :rows="4" maxlength="2000" show-word-limit />
      </el-form-item>
      <el-form-item v-if="project" label="项目状态">
        <el-radio-group v-model="form.status">
          <el-radio-button value="ACTIVE">进行中</el-radio-button>
          <el-radio-button value="ARCHIVED">已归档</el-radio-button>
        </el-radio-group>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>
