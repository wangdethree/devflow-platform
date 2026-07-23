<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { issuesApi } from '@/api/issues'
import type { Issue, IssueForm, ProjectMember } from '@/types/api'
import { getErrorMessage } from '@/utils/error'

const props = defineProps<{
  modelValue: boolean
  projectId: number
  members: ProjectMember[]
  issue?: Issue | null
}>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean]; saved: [issue: Issue] }>()
const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive<IssueForm>({
  title: '',
  description: '',
  type: 'TASK',
  priority: 'MEDIUM',
  assignee_id: null,
})
const assignees = computed(() => props.members.filter((member) => member.role !== 'Viewer'))
const rules: FormRules = {
  title: [
    { required: true, message: '请输入任务标题', trigger: 'blur' },
    { min: 2, max: 200, message: '标题需为 2–200 个字符', trigger: 'blur' },
  ],
}

watch(
  () => [props.modelValue, props.issue] as const,
  () => {
    if (!props.modelValue) return
    form.title = props.issue?.title || ''
    form.description = props.issue?.description || ''
    form.type = props.issue?.type || 'TASK'
    form.priority = props.issue?.priority || 'MEDIUM'
    form.assignee_id = props.issue?.assignee_id || null
    formRef.value?.clearValidate()
  },
  { immediate: true },
)

async function submit() {
  if (!(await formRef.value?.validate().catch(() => false))) return
  loading.value = true
  try {
    const payload = { ...form, description: form.description || null }
    const { data } = props.issue
      ? await issuesApi.update(props.issue.id, { ...payload, version: props.issue.version })
      : await issuesApi.create(props.projectId, payload)
    ElMessage.success(props.issue ? '任务已更新' : '任务已创建')
    emit('saved', data)
    emit('update:modelValue', false)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '保存任务失败'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="issue ? '编辑任务' : '创建任务'"
    width="min(600px, 92vw)"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="任务标题" prop="title">
        <el-input v-model.trim="form.title" maxlength="200" show-word-limit />
      </el-form-item>
      <el-form-item label="任务描述">
        <el-input v-model="form.description" type="textarea" :rows="5" maxlength="5000" show-word-limit />
      </el-form-item>
      <div class="form-grid">
        <el-form-item label="类型">
          <el-select v-model="form.type">
            <el-option label="任务" value="TASK" />
            <el-option label="需求" value="FEATURE" />
            <el-option label="缺陷" value="BUG" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority">
            <el-option label="低" value="LOW" />
            <el-option label="中" value="MEDIUM" />
            <el-option label="高" value="HIGH" />
            <el-option label="紧急" value="CRITICAL" />
          </el-select>
        </el-form-item>
      </div>
      <el-form-item label="负责人">
        <el-select v-model="form.assignee_id" clearable placeholder="暂不分配">
          <el-option
            v-for="member in assignees"
            :key="member.user_id"
            :label="`${member.username} · ${member.role}`"
            :value="member.user_id"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.el-select {
  width: 100%;
}
</style>
