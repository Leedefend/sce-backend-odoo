<template>
  <section v-if="items.length" class="group-summary">
    <header class="group-summary-head">
      <p>分组摘要</p>
      <span>{{ groupByLabel }}</span>
    </header>
    <div class="group-summary-items">
      <button
        v-for="item in items"
        :key="`group-summary-${item.key}`"
        class="group-summary-item"
        @click="onPick?.(item)"
      >
        <span class="name">{{ item.label }}</span>
        <span class="count">{{ item.count }}</span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
type GroupSummaryItem = {
  key: string;
  label: string;
  count: number;
  domain: unknown[];
  value?: unknown;
};

withDefaults(
  defineProps<{
    items: GroupSummaryItem[];
    groupByLabel?: string;
    onPick?: (item: GroupSummaryItem) => void;
  }>(),
  {
    groupByLabel: '',
    onPick: undefined,
  },
);
</script>

<style scoped>
.group-summary {
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #dbeafe;
  border-radius: 10px;
  background: #f8fbff;
}

.group-summary-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.group-summary-head p {
  margin: 0;
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
}

.group-summary-head span {
  color: #475569;
  font-size: 12px;
}

.group-summary-items {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.group-summary-item {
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: #ffffff;
  color: #1e3a8a;
  padding: 4px 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.group-summary-item .name {
  font-size: 12px;
}

.group-summary-item .count {
  font-size: 12px;
  font-weight: 700;
}
</style>
