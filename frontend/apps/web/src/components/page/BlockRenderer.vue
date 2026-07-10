<template>
  <div
    v-if="blockComponent"
    class="block-renderer"
    :class="blockClasses"
  >
    <component
      :is="blockComponent"
      :block="block"
      :zone-key="zoneKey"
      :dataset="dataset"
      @action="onAction"
    />
  </div>
  <article v-else class="block-fallback">
    <p class="block-fallback-title">未支持的区块类型</p>
    <p class="block-fallback-meta">请联系管理员完善页面配置。</p>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { resolveBlockComponent } from '../../app/pageBlockRegistry';
import type { PageBlockActionEvent, PageOrchestrationBlock } from '../../app/pageOrchestration';

const props = defineProps<{
  block: PageOrchestrationBlock;
  zoneKey: string;
  dataset: unknown;
}>();

const emit = defineEmits<{
  (event: 'action', payload: PageBlockActionEvent): void;
}>();

const blockComponent = computed(() => resolveBlockComponent(String(props.block.block_type || '')));
const blockClasses = computed(() => {
  const type = String(props.block.block_type || 'unknown').replace(/[^a-zA-Z0-9_-]/g, '-');
  const key = String(props.block.key || 'unknown').replace(/[^a-zA-Z0-9_-]/g, '-');
  return [`block-type-${type}`, `block-key-${key}`];
});

function onAction(payload: PageBlockActionEvent) {
  emit('action', payload);
}
</script>

<style scoped>
.block-renderer {
  min-width: 0;
  height: 100%;
}
.block-fallback {
  border: 1px dashed var(--sc-app-border-strong);
  border-radius: 10px;
  background: var(--sc-app-muted-bg);
  padding: 10px;
}
.block-fallback-title {
  margin: 0;
  font-size: 13px;
  color: var(--sc-app-text-secondary);
}
.block-fallback-meta {
  margin: 4px 0 0;
  color: var(--sc-semantic-text-muted);
  font-size: 12px;
}
</style>
