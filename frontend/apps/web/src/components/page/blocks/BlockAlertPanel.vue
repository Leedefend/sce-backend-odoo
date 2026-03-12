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
        :class="[`tone-${item.tone || 'danger'}`, { 'risk-emphasis': isRiskZone }]"
      >
        <p class="alert-title">
          <span>{{ item.title }}</span>
          <span class="alert-source" :class="`source-${item.source}`">{{ item.sourceLabel }}</span>
        </p>
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
const isRiskZone = computed(() => String(props.zoneKey || '').includes('risk'));
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
      id: String(row.id || `alert-${index + 1}`),
      title: String(row.title || `提醒 ${index + 1}`),
      description: String(row.description || row.message || ''),
      source: String(row.source || ''),
      sourceLabel: String(row.source || '').toLowerCase() === 'business' ? '业务' : '兜底',
      tone: String(row.tone || row.alert_level || 'danger').toLowerCase(),
      buttonText: String(row.action_label || row.button_label || '查看'),
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
.alert-open-btn {
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: #fff;
  padding: 7px 12px;
  cursor: pointer;
  font-weight: 600;
}

.alert-open-btn {
  border-color: #dc2626;
  background: #dc2626;
  color: #ffffff;
  font-weight: 600;
}
.alert-list {
  display: grid;
  gap: 12px;
  margin-top: 12px;
  grid-template-columns: 1fr;
}

.alert-item {
  border: 1px solid #fecaca;
  border-left-width: 5px;
  border-radius: 12px;
  padding: 12px;
  min-height: 100px;
}
.alert-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}
.alert-desc {
  margin: 6px 0 10px;
  font-size: 13px;
  color: #6b7280;
}
.alert-source {
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
.tone-danger { background: #fff5f5; border-left-color: #ef4444; }
.tone-warning { background: #fffaf0; border-left-color: #f59e0b; }
.tone-info { background: #f4f8ff; border-left-color: #3b82f6; }
.tone-success { background: #f0fdf4; border-left-color: #16a34a; }
.tone-neutral { background: #f8fafc; border-left-color: #94a3b8; }
.risk-emphasis {
  border-left-width: 7px;
  box-shadow: 0 10px 20px rgba(220, 38, 38, 0.08);
}
.alert-empty {
  margin: 8px 0 0;
  color: #6b7280;
  font-size: 13px;
}
</style>
