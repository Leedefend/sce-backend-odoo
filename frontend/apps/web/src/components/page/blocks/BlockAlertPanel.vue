<template>
  <article class="block block-alert-panel">
    <header class="block-header">
      <h4>{{ block.title || '提醒' }}</h4>
      <div class="block-header-actions">
        <button
          v-for="action in actions"
          :key="`alert-action-${action.key}`"
          type="button"
          class="block-action-btn"
          @click="emitAction(action.key, {})"
        >
          {{ action.label || action.key }}
        </button>
      </div>
    </header>

    <div v-if="items.length" class="alert-list">
      <article
        v-for="item in items"
        :key="item.id"
        class="alert-item"
        :class="`tone-${item.tone || 'danger'}`"
      >
        <p class="alert-title">{{ item.title }}</p>
        <p class="alert-desc">{{ item.description }}</p>
        <button type="button" class="alert-open-btn" @click="emitAction(item.actionKey || 'open_scene', item.raw)">
          {{ item.buttonText }}
        </button>
      </article>
    </div>
    <p v-else class="alert-empty">当前无风险提醒</p>
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
const items = computed(() => {
  if (!Array.isArray(props.dataset)) return [];
  return props.dataset.map((item, index) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    return {
      id: String(row.id || `alert-${index + 1}`),
      title: String(row.title || `提醒 ${index + 1}`),
      description: String(row.description || row.message || ''),
      tone: String(row.tone || row.alert_level || 'danger').toLowerCase(),
      buttonText: String(row.action_label || row.button_label || '查看'),
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
.block {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
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
  font-size: 15px;
  font-weight: 600;
}
.block-header-actions {
  display: flex;
  gap: 6px;
}
.block-action-btn,
.alert-open-btn {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  padding: 6px 10px;
  cursor: pointer;
}

.alert-open-btn {
  border-color: #dc2626;
  background: #dc2626;
  color: #ffffff;
  font-weight: 600;
}
.alert-list {
  display: grid;
  gap: 10px;
  margin-top: 10px;
}

@media (min-width: 1200px) {
  .alert-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.alert-item {
  border: 1px solid #fecaca;
  border-left-width: 4px;
  border-radius: 10px;
  padding: 10px;
  min-height: 90px;
}
.alert-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
.alert-desc {
  margin: 6px 0 10px;
  font-size: 12px;
  color: #6b7280;
}
.tone-danger { background: #fff5f5; border-left-color: #ef4444; }
.tone-warning { background: #fffaf0; border-left-color: #f59e0b; }
.tone-info { background: #f4f8ff; border-left-color: #3b82f6; }
.tone-success { background: #f0fdf4; border-left-color: #16a34a; }
.tone-neutral { background: #f8fafc; border-left-color: #94a3b8; }
.alert-empty {
  margin: 8px 0 0;
  color: #6b7280;
  font-size: 13px;
}
</style>
