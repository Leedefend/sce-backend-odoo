<template>
  <ScDialog :open="open" title="确认配置影响" close-label="取消操作" @close="$emit('cancel')">
    <dl class="impact-summary">
      <div><dt>影响页面</dt><dd>{{ pageLabel || '当前业务页面' }}</dd></div>
      <div><dt>影响角色</dt><dd>{{ roleLabel || '当前适用角色' }}</dd></div>
      <div><dt>影响公司</dt><dd>{{ companyLabel || '当前公司' }}</dd></div>
      <div><dt>变更摘要</dt><dd>{{ summary }}</dd></div>
      <div><dt>生效方式</dt><dd>{{ immediate ? '确认后立即生效' : '仅保存当前草稿' }}</dd></div>
      <div><dt>回滚说明</dt><dd>{{ rollbackText }}</dd></div>
    </dl>
    <template #actions>
      <ScButton variant="ghost" @click="$emit('cancel')">取消</ScButton>
      <ScButton variant="danger" data-dialog-primary @click="$emit('confirm')">确认继续</ScButton>
    </template>
  </ScDialog>
</template>

<script setup lang="ts">
import ScButton from '../../components/design-system/ScButton.vue';
import ScDialog from '../../components/design-system/ScDialog.vue';

withDefaults(defineProps<{
  open: boolean;
  pageLabel: string;
  roleLabel: string;
  companyLabel: string;
  summary: string;
  immediate?: boolean;
  rollbackText?: string;
}>(), {
  immediate: true,
  rollbackText: '系统保留配置版本，可从版本记录恢复。',
});

defineEmits<{ confirm: []; cancel: [] }>();
</script>

<style scoped>
.impact-summary { display: grid; gap: var(--sc-product-space-2); margin: var(--sc-product-space-3) 0 0; }
.impact-summary div { display: grid; grid-template-columns: 96px minmax(0, 1fr); gap: var(--sc-product-space-2); }
.impact-summary dt { color: var(--sc-app-text-secondary); }
.impact-summary dd { margin: 0; color: var(--sc-app-text-primary); }
@media (max-width: 480px) { .impact-summary div { grid-template-columns: 1fr; gap: var(--sc-product-space-1); } }
</style>
