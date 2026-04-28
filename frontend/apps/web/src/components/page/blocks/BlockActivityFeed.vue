<template>
  <article class="block block-activity-feed">
    <header class="block-header">
      <h4>{{ block.title || '动态' }}</h4>
    </header>
    <ul v-if="rows.length" class="feed-list">
      <li
        v-for="item in rows"
        :key="item.key"
        class="feed-item"
        :class="{ actionable: Boolean(item.actionKey) }"
        :tabindex="item.actionKey ? 0 : undefined"
        :role="item.actionKey ? 'button' : undefined"
        @click="emitAction(item.actionKey, item.raw)"
        @keydown.enter.prevent="emitAction(item.actionKey, item.raw)"
        @keydown.space.prevent="emitAction(item.actionKey, item.raw)"
      >
        <p class="feed-title">{{ item.title }}</p>
        <p class="feed-desc">{{ item.description }}</p>
      </li>
    </ul>
    <p v-else class="feed-empty">暂无动态</p>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { PageBlockActionEvent, PageOrchestrationBlock } from '../../../app/pageOrchestration';

const props = defineProps<{
  block: PageOrchestrationBlock;
  zoneKey: string;
  dataset: unknown;
}>();

const emit = defineEmits<{
  (event: 'action', payload: PageBlockActionEvent): void;
}>();

const rows = computed(() => {
  if (!Array.isArray(props.dataset)) return [];
  return props.dataset.map((item, index) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    return {
      key: String(row.id || row.key || `feed-${index + 1}`),
      title: String(row.title || row.label || `动态 ${index + 1}`),
      description: String(row.description || row.message || ''),
      actionKey: String(row.action_key || ''),
      raw: row,
    };
  });
});

function emitAction(actionKey: string, item: Record<string, unknown>) {
  const key = String(actionKey || '').trim();
  if (!key) return;
  emit('action', {
    actionKey: key,
    blockKey: props.block.key,
    zoneKey: props.zoneKey,
    item,
  });
}
</script>

<style scoped>
.block { border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; padding: 10px; }
.block-header h4 { margin: 0 0 8px; font-size: 14px; }
.feed-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.feed-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px; background: #f9fafb; }
.feed-item.actionable { cursor: pointer; }
.feed-item.actionable:hover { border-color: #93c5fd; background: #eff6ff; }
.feed-item.actionable:focus-visible { outline: 2px solid #2563eb; outline-offset: 2px; }
.feed-title { margin: 0; font-size: 13px; font-weight: 600; }
.feed-desc { margin: 4px 0 0; font-size: 12px; color: #6b7280; }
.feed-empty { margin: 0; font-size: 12px; color: #6b7280; }
</style>
