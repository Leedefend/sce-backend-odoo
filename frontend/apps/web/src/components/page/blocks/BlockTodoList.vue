<template>
  <article class="block block-todo-list">
    <header class="block-header">
      <h4>{{ block.title || '待办' }}</h4>
      <div class="block-header-actions">
        <button
          v-for="action in actions"
          :key="`block-action-${action.key}`"
          type="button"
          class="block-action-btn"
          @click="emitAction(action.key, {})"
        >
          {{ action.label || action.key }}
        </button>
      </div>
    </header>

    <div v-if="items.length" class="todo-list">
      <article v-for="item in items" :key="item.id" class="todo-item" :class="`tone-${item.tone || 'info'}`">
        <div>
          <p class="todo-title">{{ item.title }}</p>
          <p class="todo-desc">{{ item.description }}</p>
        </div>
        <button type="button" class="todo-open-btn" @click="emitAction(item.actionKey || 'open_scene', item.raw)">
          {{ item.buttonText }}
        </button>
      </article>
    </div>

    <p v-else class="todo-empty">当前暂无待办</p>
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
      id: String(row.id || `todo-${index + 1}`),
      title: String(row.title || `待办 ${index + 1}`),
      description: String(row.description || ''),
      tone: String(row.tone || 'warning').toLowerCase(),
      buttonText: String(row.action_label || row.button_label || '进入处理'),
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
.todo-open-btn {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  padding: 6px 10px;
  cursor: pointer;
}

.todo-open-btn {
  border-color: #2563eb;
  background: #2563eb;
  color: #ffffff;
  font-weight: 600;
}
.todo-list {
  display: grid;
  gap: 10px;
  margin-top: 10px;
}

@media (min-width: 1200px) {
  .todo-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.todo-item {
  border: 1px solid #dbeafe;
  border-left-width: 4px;
  border-radius: 10px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 90px;
}
.todo-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
.todo-desc {
  margin: 6px 0 0;
  font-size: 12px;
  color: #6b7280;
}
.tone-warning { background: #fffaf0; border-left-color: #f59e0b; }
.tone-danger { background: #fff5f5; border-left-color: #ef4444; }
.tone-info { background: #f4f8ff; border-left-color: #3b82f6; }
.tone-success { background: #f0fdf4; border-left-color: #16a34a; }
.tone-neutral { background: #f8fafc; border-left-color: #94a3b8; }
.todo-empty {
  margin: 8px 0 0;
  color: #6b7280;
  font-size: 13px;
}
</style>
