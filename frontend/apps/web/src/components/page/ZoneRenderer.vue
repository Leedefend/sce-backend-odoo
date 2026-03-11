<template>
  <section class="zone-renderer" :class="`zone-${zone.zone_type || 'supporting'}`">
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
  border-radius: 12px;
  background: #fff;
  padding: 12px;
}
.zone-renderer-header h3 {
  margin: 0;
  font-size: 16px;
}
.zone-renderer-header p {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 13px;
}
.zone-renderer-body {
  margin-top: 10px;
  display: grid;
  gap: 10px;
}
.display-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.display-stack {
  grid-template-columns: 1fr;
}

.zone-critical {
  border-color: #fecaca;
  background: #fff7f7;
}
</style>
