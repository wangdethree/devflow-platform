<script setup lang="ts">
import { Files } from '@element-plus/icons-vue'

withDefaults(
  defineProps<{
    title?: string
    description?: string
  }>(),
  {
    title: '这里还没有内容',
    description: '创建第一条记录，开始推进工作。',
  },
)
</script>

<template>
  <div class="empty-state">
    <el-icon><Files /></el-icon>
    <strong>{{ title }}</strong>
    <p>{{ description }}</p>
    <slot />
  </div>
</template>
