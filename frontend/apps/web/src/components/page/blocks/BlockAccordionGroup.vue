<template>
  <article class="block block-accordion-group">
    <details open>
      <summary>{{ block.title || '详情' }}</summary>
      <div class="accordion-content">
        <p v-if="rows.length === 0" class="accordion-empty">暂无数据</p>
        <article v-for="item in rows" :key="item.key" class="accordion-item">
          <p class="accordion-title">{{ item.title }}</p>
          <p class="accordion-desc">{{ item.description }}</p>
        </article>
      </div>
    </details>
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
  if (Array.isArray(props.dataset)) {
    return props.dataset.map((item, index) => {
      const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
      return {
        key: String(row.id || row.key || `acc-${index + 1}`),
        title: String(row.title || row.label || `项 ${index + 1}`),
        description: String(row.description || row.message || ''),
      };
    });
  }
  if (!props.dataset || typeof props.dataset !== 'object') return [];
  return Object.entries(props.dataset as Record<string, unknown>).slice(0, 8).map(([key, value]) => ({
    key,
    title: key,
    description: typeof value === 'object' ? JSON.stringify(value) : String(value ?? '--'),
  }));
});
</script>

<style scoped>
.block { border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; padding: 10px; height: 100%; }
summary { cursor: pointer; font-weight: 600; }
.accordion-content { margin-top: 8px; display: grid; gap: 8px; }
.accordion-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px; background: #f9fafb; }
.accordion-title { margin: 0; font-size: 13px; font-weight: 600; }
.accordion-desc { margin: 4px 0 0; font-size: 12px; color: #6b7280; }
.accordion-empty { margin: 0; font-size: 12px; color: #6b7280; }
</style>
