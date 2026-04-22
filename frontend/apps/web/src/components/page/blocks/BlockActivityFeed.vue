<template>
  <article class="block block-activity-feed">
    <header class="block-header">
      <div>
        <p class="block-eyebrow">协作动态</p>
        <h4>{{ block.title || '动态' }}</h4>
      </div>
      <span class="block-count">{{ rows.length }} 条</span>
    </header>
    <ul v-if="rows.length" class="feed-list">
      <li v-for="item in rows" :key="item.key" class="feed-item">
        <p class="feed-title">{{ item.title }}</p>
        <p class="feed-desc">{{ item.description }}</p>
      </li>
    </ul>
    <p v-else class="feed-empty">暂无动态</p>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { PageOrchestrationBlock } from '../../../app/pageOrchestration';

const props = defineProps<{
  block: PageOrchestrationBlock;
  zoneKey: string;
  dataset: unknown;
}>();

const rows = computed(() => {
  if (!Array.isArray(props.dataset)) return [];
  return props.dataset.map((item, index) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    return {
      key: String(row.id || row.key || `feed-${index + 1}`),
      title: String(row.title || row.label || `动态 ${index + 1}`),
      description: String(row.description || row.message || ''),
    };
  });
});
</script>

<style scoped>
.block {
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-sm);
  background:
    linear-gradient(180deg, rgba(235, 248, 242, 0.36), rgba(255, 255, 255, 0) 78px),
    rgba(255, 255, 255, 0.96);
  padding: var(--ui-space-3);
  box-shadow: var(--ui-shadow-xs);
}

.block-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--ui-space-3);
  margin-bottom: var(--ui-space-3);
}

.block-eyebrow {
  margin: 0 0 2px;
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-bold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ui-color-ink-soft);
}

.block-header h4 {
  margin: 0;
  font-size: var(--ui-font-size-md);
  color: var(--ui-color-ink-strong);
}

.block-count {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: var(--ui-radius-pill);
  border: 1px solid rgba(31, 122, 91, 0.18);
  background: rgba(235, 248, 242, 0.86);
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-success-600);
}

.feed-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: var(--ui-space-2);
}

.feed-item {
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-sm);
  padding: var(--ui-space-3);
  background: rgba(248, 245, 239, 0.72);
}

.feed-title {
  margin: 0;
  font-size: var(--ui-font-size-md);
  font-weight: var(--ui-font-weight-semibold);
  color: var(--ui-color-ink-strong);
}

.feed-desc {
  margin: 4px 0 0;
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-muted);
  line-height: 1.5;
}

.feed-empty {
  margin: 0;
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-muted);
}
</style>
