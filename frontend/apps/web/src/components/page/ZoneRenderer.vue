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
  min-width: 0;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  padding: 20px;
  box-shadow: 0 10px 24px var(--sc-app-shadow);
}
.zone-renderer-header h3 {
  margin: 0;
  font-size: 21px;
  font-weight: 700;
  overflow-wrap: anywhere;
}
.zone-renderer-header p {
  margin: 8px 0 0;
  color: var(--sc-app-text-secondary);
  font-size: 14px;
  overflow-wrap: anywhere;
}
.zone-renderer-body {
  margin-top: 16px;
  display: grid;
  gap: 16px;
  min-width: 0;
}
.display-grid {
  grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
}
.display-grid > * {
  height: 100%;
}
.display-stack {
  grid-template-columns: 1fr;
}

.zone-critical {
  border-color: var(--sc-app-danger-border);
  background: var(--sc-app-danger-bg);
}

.zone-primary {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
}

.zone-secondary {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-panel);
}

.zone-supporting {
  border-color: var(--sc-app-border);
  background: var(--sc-app-panel);
}

.zone-key-today_focus {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
  box-shadow: 0 18px 36px var(--sc-app-focus-ring);
  padding: 22px;
}

.zone-key-today_focus .zone-renderer-header h3 {
  font-size: 26px;
}

.zone-key-today_focus .display-grid {
  grid-template-columns: 1.3fr 1fr;
}

@media (max-width: 1200px) {
  .zone-key-today_focus .display-grid {
    grid-template-columns: 1fr;
  }
}

.zone-key-analysis {
  border-color: var(--sc-app-border-strong);
  background: var(--sc-app-panel);
}

.zone-key-quick_entries {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-panel);
}

.zone-key-hero {
  background: var(--sc-app-muted-bg);
  border-color: var(--sc-app-info-border);
  box-shadow: none;
}

.zone-key-hero .zone-renderer-header h3 {
  font-size: 17px;
}

.zone-key-hero .zone-renderer-header p {
  font-size: 13px;
}
</style>
