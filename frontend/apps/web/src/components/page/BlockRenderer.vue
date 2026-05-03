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
    <p class="block-fallback-meta">block_type={{ block.block_type || 'unknown' }}</p>
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
  border: 1px dashed #d1d5db;
  border-radius: 10px;
  background: #f9fafb;
  padding: 10px;
}
.block-fallback-title {
  margin: 0;
  font-size: 13px;
  color: #374151;
}
.block-fallback-meta {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 12px;
}
</style>
