<template>
  <section v-if="items.length" class="group-summary">
    <header class="group-summary-head">
      <p>分组摘要</p>
      <div class="group-summary-head-actions">
        <span v-if="windowInfo">{{ windowInfo }}</span>
        <button
          v-if="onPrevWindow"
          class="page-btn"
          :disabled="!canPrevWindow"
          @click="onPrevWindow?.()"
        >
          上一组
        </button>
        <button
          v-if="onNextWindow"
          class="page-btn"
          :disabled="!canNextWindow"
          @click="onNextWindow?.()"
        >
          下一组
        </button>
        <span>{{ groupByLabel }}</span>
        <button v-if="activeKey" class="clear-btn" @click="onClear?.()">清除下钻</button>
      </div>
    </header>
    <div class="group-summary-items">
      <button
        v-for="item in items"
        :key="`group-summary-${item.key}`"
        class="group-summary-item"
        :class="{ active: activeKey === item.key }"
        @click="onPick?.(item)"
      >
        <span class="name">{{ item.label }}</span>
        <span class="count">{{ item.count }}</span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type GroupSummaryItem = {
  key: string;
  label: string;
  count: number;
  domain: unknown[];
  value?: unknown;
};

const props = withDefaults(
  defineProps<{
    items: Array<GroupSummaryItem | Record<string, unknown>>;
    groupByLabel?: string;
    activeKey?: string;
    windowOffset?: number;
    windowCount?: number;
    windowTotal?: number;
    windowStart?: number;
    windowEnd?: number;
    canPrevWindow?: boolean;
    canNextWindow?: boolean;
    onPick?: (item: GroupSummaryItem | Record<string, unknown>) => void;
    onClear?: () => void;
    onPrevWindow?: () => void;
    onNextWindow?: () => void;
  }>(),
  {
    groupByLabel: '',
    activeKey: '',
    windowOffset: 0,
    windowCount: 0,
    windowTotal: undefined,
    windowStart: undefined,
    windowEnd: undefined,
    canPrevWindow: false,
    canNextWindow: false,
    onPick: undefined,
    onClear: undefined,
    onPrevWindow: undefined,
    onNextWindow: undefined,
  },
);

const windowInfo = computed(() => {
  const offset = Math.max(0, Math.trunc(Number(props.windowOffset || 0)));
  const count = Math.max(0, Math.trunc(Number(props.windowCount || 0)));
  if (count <= 0) return '';
  const backendStart = Number(props.windowStart);
  const backendEnd = Number(props.windowEnd);
  const start = Number.isFinite(backendStart) && backendStart > 0 ? Math.trunc(backendStart) : offset + 1;
  const end = Number.isFinite(backendEnd) && backendEnd >= start ? Math.trunc(backendEnd) : (offset + count);
  if (Number.isFinite(Number(props.windowTotal)) && Number(props.windowTotal) >= 0) {
    return `第 ${start}-${end} 组 / 共 ${Math.trunc(Number(props.windowTotal))} 组`;
  }
  return `第 ${start}-${end} 组`;
});
</script>

<style scoped>
.group-summary {
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--sc-app-info-border);
  border-radius: 10px;
  background: var(--sc-app-info-bg);
}

.group-summary-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.group-summary-head-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.group-summary-head p {
  margin: 0;
  color: var(--sc-app-text-primary);
  font-size: 13px;
  font-weight: 700;
}

.group-summary-head span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.group-summary-items {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.group-summary-item {
  border: 1px solid var(--sc-app-info-border);
  border-radius: 999px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-info-text);
  padding: 4px 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.group-summary-item.active {
  border-color: var(--sc-semantic-surface-interactive);
  background: var(--sc-app-info-bg);
}

.clear-btn {
  border: 1px solid var(--sc-app-info-border);
  border-radius: 999px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-info-text);
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.page-btn {
  border: 1px solid var(--sc-app-info-border);
  border-radius: 999px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-info-text);
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.page-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.group-summary-item .name {
  font-size: 12px;
}

.group-summary-item .count {
  font-size: 12px;
  font-weight: 700;
}
</style>
