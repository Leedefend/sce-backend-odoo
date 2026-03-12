<template>
  <section class="page-renderer">
    <header class="page-renderer-header">
      <div>
        <h2>{{ pageTitle }}</h2>
        <p v-if="pageSubtitle" class="page-renderer-subtitle">{{ pageSubtitle }}</p>
      </div>
      <div v-if="pageBadges.length" class="page-renderer-badges">
        <span
          v-for="badge in pageBadges"
          :key="`badge-${badge.label}-${badge.tone}`"
          class="page-renderer-badge"
          :class="`tone-${badge.tone || 'neutral'}`"
        >
          {{ badge.label }}
        </span>
      </div>
    </header>

    <div v-if="globalActions.length" class="page-renderer-actions">
      <button
        v-for="action in globalActions"
        :key="`global-${action.key}`"
        type="button"
        class="page-renderer-action"
        @click="emitAction(action, '', '', {})"
      >
        {{ action.label || action.key }}
      </button>
    </div>

    <ZoneRenderer
      v-for="zone in orderedZones"
      :key="zone.key"
      :zone="zone"
      :datasets="datasets"
      @action="onZoneAction"
    />
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import ZoneRenderer from './ZoneRenderer.vue';
import type {
  PageBlockActionEvent,
  PageOrchestrationAction,
  PageOrchestrationContract,
  PageOrchestrationZone,
} from '../../app/pageOrchestration';

const props = defineProps<{
  contract: PageOrchestrationContract;
  datasets: Record<string, unknown>;
}>();

const emit = defineEmits<{
  (event: 'action', payload: PageBlockActionEvent): void;
}>();

const pageTitle = computed(() => String(props.contract.page?.title || '页面'));
const pageSubtitle = computed(() => String(props.contract.page?.subtitle || ''));
const pageBadges = computed(() => Array.isArray(props.contract.page?.header?.badges)
  ? props.contract.page?.header?.badges || []
  : []);
const globalActions = computed<PageOrchestrationAction[]>(() => Array.isArray(props.contract.page?.global_actions)
  ? props.contract.page?.global_actions || []
  : []);

const orderedZones = computed<PageOrchestrationZone[]>(() => {
  const zones = Array.isArray(props.contract.zones) ? [...props.contract.zones] : [];
  return zones.sort((a, b) => Number(b.priority || 0) - Number(a.priority || 0));
});

function emitAction(
  action: PageOrchestrationAction,
  blockKey: string,
  zoneKey: string,
  item: Record<string, unknown>,
) {
  const actionKey = String(action.key || '').trim();
  if (!actionKey) return;
  emit('action', {
    actionKey,
    blockKey,
    zoneKey,
    item,
    intent: String(action.intent || ''),
    target: action.target && typeof action.target === 'object' ? action.target : {},
  });
}

function onZoneAction(payload: PageBlockActionEvent) {
  emit('action', payload);
}
</script>

<style scoped>
.page-renderer {
  display: grid;
  gap: 18px;
}
.page-renderer-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border: 1px solid #dbeafe;
  border-radius: 14px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 65%);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}
.page-renderer-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 650;
}
.page-renderer-subtitle {
  margin: 6px 0 0;
  color: #6b7280;
}
.page-renderer-badges {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.page-renderer-badge {
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  font-size: 12px;
}
.page-renderer-actions {
  display: flex;
  gap: 8px;
}
.page-renderer-action {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  padding: 6px 10px;
  cursor: pointer;
}
.tone-success { background: #ecfdf5; color: #047857; }
.tone-warning { background: #fffbeb; color: #b45309; }
.tone-danger { background: #fef2f2; color: #b91c1c; }
.tone-info { background: #eff6ff; color: #1d4ed8; }
.tone-neutral { background: #f9fafb; color: #374151; }
</style>
