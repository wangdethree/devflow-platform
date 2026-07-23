<script setup lang="ts">
import { computed } from 'vue'
import {
  issueStatusLabels,
  issueTypeLabels,
  priorityLabels,
  projectStatusLabels,
  reviewStatusLabels,
  roleLabels,
  tagType,
} from '@/utils/labels'

const props = defineProps<{ value: string }>()

const labels: Record<string, string> = {
  ...projectStatusLabels,
  ...roleLabels,
  ...issueTypeLabels,
  ...priorityLabels,
  ...issueStatusLabels,
  ...reviewStatusLabels,
}
const label = computed(() => labels[props.value] || props.value)
</script>

<template>
  <el-tag :type="tagType(value)" effect="light" round>{{ label }}</el-tag>
</template>
