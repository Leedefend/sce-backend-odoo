<template>
  <ScErrorSummary
    v-if="errors.length || conflict"
    :errors="errors"
    :title="conflict ? '记录已被其他操作更新' : '请检查以下内容'"
    @select="$emit('focus-error', $event)"
  >
    <p v-if="conflict">当前页面保留了你的输入。继续编辑前，请先加载最新数据。</p>
    <button v-if="conflict" type="button" class="sc-btn sc-btn-secondary" @click="$emit('reload-latest')">加载最新数据</button>
  </ScErrorSummary>
</template>

<script setup lang="ts">
import ScErrorSummary from '../design-system/ScErrorSummary.vue';
defineProps<{ errors: string[]; conflict?: boolean }>();
defineEmits<{ 'focus-error': [message: string]; 'reload-latest': [] }>();
</script>
