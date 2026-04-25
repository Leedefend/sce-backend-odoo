<template>
  <article class="block block-entry-grid">
    <header class="block-header">
      <h4>{{ block.title || '入口' }}</h4>
      <div class="block-header-actions">
        <button
          v-for="action in actions"
          :key="`entry-action-${action.key}`"
          type="button"
          class="block-action-btn"
          @click="emitAction(action.key, {})"
        >
          {{ action.label || action.key }}
        </button>
      </div>
    </header>

    <div v-if="items.length" class="entry-grid">
      <button
        v-for="item in items"
        :key="item.id"
        type="button"
        class="entry-item"
        @click="emitAction(item.actionKey || 'open_scene', item.raw)"
      >
        <p class="entry-title">{{ item.title }}</p>
        <p class="entry-hint">{{ item.hint }}</p>
        <div v-if="item.metaRows.length" class="entry-meta">
          <span v-for="meta in item.metaRows" :key="`${item.id}-${meta.label}`" class="entry-meta-chip">
            {{ meta.label }} {{ meta.value }}
          </span>
        </div>
      </button>
    </div>

    <p v-else class="entry-empty">当前无可用入口</p>
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

const actions = computed(() => (Array.isArray(props.block.actions) ? props.block.actions : []));
const maxItems = computed(() => {
  const payload = props.block.payload && typeof props.block.payload === 'object'
    ? props.block.payload as Record<string, unknown>
    : {};
  const value = Number(payload.max_items || 0);
  return Number.isFinite(value) && value > 0 ? Math.floor(value) : 0;
});
const items = computed(() => {
  if (!Array.isArray(props.dataset)) return [];
  const rows = maxItems.value > 0 ? props.dataset.slice(0, maxItems.value) : props.dataset;
  return rows.map((item, index) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    return {
      id: String(row.id || row.key || `entry-${index + 1}`),
      title: String(row.title || row.label || `入口 ${index + 1}`),
      hint: String(row.hint || row.subtitle || ''),
      actionKey: String(row.action_key || ''),
      metaRows: [
        {
          label: '可用',
          value: Number(row.allow_count || row.ready_count || 0),
        },
        {
          label: '功能',
          value: Number(row.capability_count || 0),
        },
      ].filter((meta) => Number.isFinite(meta.value) && meta.value > 0),
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
.block {
  border: 1px solid #dbe3ee;
  border-radius: 14px;
  background: #fff;
  padding: 14px;
  height: 100%;
}
.block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.block-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}
.block-header-actions {
  display: flex;
  gap: 6px;
}
.block-action-btn {
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: #fff;
  padding: 6px 10px;
  cursor: pointer;
  font-weight: 600;
}
.entry-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}
.entry-item {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: linear-gradient(180deg, #f8fbff 0%, #f9fafb 100%);
  padding: 14px;
  text-align: left;
  cursor: pointer;
  min-height: 104px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.entry-item:hover {
  border-color: #60a5fa;
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.14);
  transform: translateY(-2px);
}
.entry-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}
.entry-hint {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6b7280;
}
.entry-meta {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.entry-meta-chip {
  font-size: 11px;
  border-radius: 999px;
  padding: 2px 8px;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
  background: #eff6ff;
}
.entry-empty {
  margin: 8px 0 0;
  color: #6b7280;
  font-size: 13px;
}
</style>
