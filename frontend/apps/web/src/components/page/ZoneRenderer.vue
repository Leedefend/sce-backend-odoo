<template>
  <section class="zone-renderer" :class="[`zone-${zone.zone_type || 'supporting'}`, `zone-key-${zone.key || 'unknown'}`]">
    <header v-if="zone.title || zone.description" class="zone-renderer-header">
      <h3 v-if="zone.title">{{ zone.title }}</h3>
      <p v-if="zone.description">{{ zone.description }}</p>
    </header>

    <div class="zone-renderer-body" :class="`display-${zone.display_mode || 'stack'}`">
      <BlockRenderer
        v-for="block in orderedBlocks"
        :key="block.key"
        :block="block"
        :zone-key="zone.key"
        :dataset="resolveDataset(block.data_source)"
        @action="onBlockAction"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import BlockRenderer from './BlockRenderer.vue';
import type { PageBlockActionEvent, PageOrchestrationBlock, PageOrchestrationZone } from '../../app/pageOrchestration';

const props = defineProps<{
  zone: PageOrchestrationZone;
  datasets: Record<string, unknown>;
}>();

const emit = defineEmits<{
  (event: 'action', payload: PageBlockActionEvent): void;
}>();

const orderedBlocks = computed<PageOrchestrationBlock[]>(() => {
  const blocks = Array.isArray(props.zone.blocks) ? [...props.zone.blocks] : [];
  return blocks.sort((a, b) => Number(b.priority || 0) - Number(a.priority || 0));
});

function resolveDataset(sourceKey: string | undefined): unknown {
  if (!sourceKey) return null;
  return props.datasets[sourceKey] ?? null;
}

function onBlockAction(payload: PageBlockActionEvent) {
  emit('action', payload);
}
</script>

<style scoped>
.zone-renderer {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #fff;
  padding: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}
.zone-renderer-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}
.zone-renderer-header p {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 13px;
}
.zone-renderer-body {
  margin-top: 14px;
  display: grid;
  gap: 14px;
}
.display-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.display-grid > * {
  height: 100%;
}
.display-stack {
  grid-template-columns: 1fr;
}

.zone-critical {
  border-color: #fecaca;
  background: #fff7f7;
}

.zone-primary {
  border-color: #bfdbfe;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 55%);
}

.zone-secondary {
  border-color: #dbeafe;
  background: #ffffff;
}

.zone-supporting {
  border-color: #e5e7eb;
  background: #ffffff;
}

.zone-key-today_focus {
  border-color: #93c5fd;
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 68%);
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.08);
}

.zone-key-today_focus .zone-renderer-header h3 {
  font-size: 22px;
}

.zone-key-analysis {
  border-color: #cbd5e1;
  background: #ffffff;
}

.zone-key-quick_entries {
  border-color: #bfdbfe;
  background: #ffffff;
}
</style>
