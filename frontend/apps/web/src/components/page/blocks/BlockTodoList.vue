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
      source: normalizeSource(row.source),
      sourceLabel: String(row.source_label || row.sourceLabel || '业务事项'),
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

function normalizeSource(value: unknown) {
  return String(value || 'business').toLowerCase().replace(/[^a-z0-9_-]/g, '_');
}

</script>

<style scoped>
.block {
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
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
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 8px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 7px 12px;
  cursor: pointer;
  font-weight: 600;
  white-space: nowrap;
}

.todo-open-btn {
  border-color: var(--sc-semantic-surface-interactive);
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
  font-weight: 600;
}
.todo-list {
  display: grid;
  gap: 12px;
  margin-top: 12px;
  grid-template-columns: 1fr;
}

.todo-item {
  border: 1px solid var(--sc-app-info-border);
  border-left-width: 5px;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 100px;
  min-width: 0;
}
.todo-item.actionable {
  cursor: pointer;
}
.todo-item.actionable:hover {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
}
.todo-item.actionable:focus-visible {
  outline: 2px solid var(--sc-semantic-surface-interactive);
  outline-offset: 2px;
}
.todo-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
}
.todo-desc {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--sc-app-text-secondary);
}
.todo-meta {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--sc-app-text-primary);
  font-weight: 600;
}
.todo-urgent {
  font-size: 11px;
  color: var(--sc-app-danger-text);
  border: 1px solid var(--sc-app-danger-border);
  background: var(--sc-app-danger-bg);
  border-radius: 999px;
  padding: 1px 6px;
}
.todo-source {
  font-size: 11px;
  border-radius: 999px;
  padding: 1px 6px;
  border: 1px solid var(--sc-app-border);
  color: var(--sc-app-text-secondary);
  background: var(--sc-app-muted-bg);
}
.source-business {
  border-color: var(--sc-app-success-border);
  color: var(--sc-app-success-text);
  background: var(--sc-app-success-bg);
}
.source-capability_fallback {
  border-color: var(--sc-app-warning-border);
  color: var(--sc-app-warning-text);
  background: var(--sc-app-warning-bg);
}
.tone-warning { background: var(--sc-app-warning-bg); border-left-color: var(--sc-app-warning-text); }
.tone-danger { background: var(--sc-app-danger-bg); border-left-color: var(--sc-app-danger-text); }
.tone-info { background: var(--sc-app-info-bg); border-left-color: var(--sc-app-info-text); }
.tone-success { background: var(--sc-app-success-bg); border-left-color: var(--sc-app-success-text); }
.tone-neutral { background: var(--sc-app-muted-bg); border-left-color: var(--sc-app-border-strong); }
.todo-empty {
  margin: 8px 0 0;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}
</style>
