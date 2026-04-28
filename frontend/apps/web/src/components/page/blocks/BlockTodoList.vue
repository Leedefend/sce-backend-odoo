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
      <article
        v-for="item in items"
        :key="item.id"
        class="todo-item"
        :class="[`tone-${item.tone || 'info'}`, { actionable: Boolean(item.actionKey) }]"
        :tabindex="item.actionKey ? 0 : undefined"
        :role="item.actionKey ? 'button' : undefined"
        @click="emitAction(item.actionKey || 'open_scene', item.raw)"
        @keydown.enter.prevent="emitAction(item.actionKey || 'open_scene', item.raw)"
        @keydown.space.prevent="emitAction(item.actionKey || 'open_scene', item.raw)"
      >
        <div>
          <p class="todo-title">
            <span>{{ item.title }}</span>
            <span v-if="item.status === 'urgent'" class="todo-urgent">紧急</span>
            <span class="todo-source" :class="`source-${item.source}`">{{ item.sourceLabel }}</span>
          </p>
          <p class="todo-desc">{{ item.description }}</p>
          <p v-if="item.pendingCount > 0" class="todo-meta">待处理 {{ item.pendingCount }}</p>
        </div>
        <button type="button" class="todo-open-btn" @click.stop="emitAction(item.actionKey || 'open_scene', item.raw)">
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
const maxItems = computed(() => {
  const payload = (props.block.payload && typeof props.block.payload === 'object')
    ? props.block.payload as Record<string, unknown>
    : {};
  const value = Number(payload.max_items || 0);
  return Number.isFinite(value) && value > 0 ? Math.trunc(value) : 0;
});
const items = computed(() => {
  if (!Array.isArray(props.dataset)) return [];
  const normalized = props.dataset.map((item, index) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    return {
      id: String(row.id || `todo-${index + 1}`),
      title: String(row.title || `待办 ${index + 1}`),
      description: String(row.description || ''),
      pendingCount: Number(row.count || row.pending_count || 0),
      status: String(row.status || '').toLowerCase(),
      source: String(row.source || ''),
      sourceLabel: String(row.source || '').toLowerCase() === 'business' ? '业务' : '兜底',
      tone: String(row.tone || 'warning').toLowerCase(),
      buttonText: String(row.action_label || row.button_label || '进入处理'),
      actionKey: String(row.action_key || ''),
      raw: row,
    };
  });
  if (maxItems.value > 0) return normalized.slice(0, maxItems.value);
  return normalized;
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
.block-action-btn,
.todo-open-btn {
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: #fff;
  padding: 7px 12px;
  cursor: pointer;
  font-weight: 600;
}

.todo-open-btn {
  border-color: #2563eb;
  background: #2563eb;
  color: #ffffff;
  font-weight: 600;
}
.todo-list {
  display: grid;
  gap: 12px;
  margin-top: 12px;
  grid-template-columns: 1fr;
}

.todo-item {
  border: 1px solid #dbeafe;
  border-left-width: 5px;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 100px;
}
.todo-item.actionable {
  cursor: pointer;
}
.todo-item.actionable:hover {
  border-color: #93c5fd;
  background: #eff6ff;
}
.todo-item.actionable:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}
.todo-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}
.todo-desc {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6b7280;
}
.todo-meta {
  margin: 6px 0 0;
  font-size: 13px;
  color: #334155;
  font-weight: 600;
}
.todo-urgent {
  font-size: 11px;
  color: #b91c1c;
  border: 1px solid #fecaca;
  background: #fff1f2;
  border-radius: 999px;
  padding: 1px 6px;
}
.todo-source {
  font-size: 11px;
  border-radius: 999px;
  padding: 1px 6px;
  border: 1px solid #cbd5e1;
  color: #475569;
  background: #f8fafc;
}
.source-business {
  border-color: #86efac;
  color: #166534;
  background: #f0fdf4;
}
.source-capability_fallback {
  border-color: #fde68a;
  color: #92400e;
  background: #fffbeb;
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
