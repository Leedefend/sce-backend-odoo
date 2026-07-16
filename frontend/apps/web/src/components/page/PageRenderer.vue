<template>
  <section class="page-renderer">
    <header class="page-renderer-header">
      <div class="page-renderer-title">
        <component :is="primaryHeading ? 'h1' : 'h2'">{{ pageTitle }}</component>
        <p v-if="pageSubtitle" class="page-renderer-subtitle">{{ pageSubtitle }}</p>
      </div>
      <div v-if="headerBadges.length || globalActions.length" class="page-renderer-tools">
        <div v-if="headerBadges.length" class="page-renderer-badges">
          <span
            v-for="badge in headerBadges"
            :key="`badge-${badge.label}-${badge.tone}`"
            class="page-renderer-badge"
            :class="`tone-${badge.tone || 'neutral'}`"
          >
            {{ badge.label }}
          </span>
        </div>
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
      </div>
    </header>

    <div class="page-renderer-zones">
      <ZoneRenderer
        v-for="zone in orderedZones"
        :key="zone.key"
        :zone="zone"
        :datasets="datasets"
        @action="onZoneAction"
      />
    </div>
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
  primaryHeading?: boolean;
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

const headerBadges = computed(() => pageBadges.value);

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
  gap: 14px;
  width: 100%;
  max-width: min(1380px, 100%);
  margin: 0 auto;
  min-width: 0;
}
.page-renderer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  box-shadow: 0 1px 2px var(--sc-app-shadow);
}
.page-renderer-title {
  min-width: 0;
}
.page-renderer-header h1,
.page-renderer-header h2 {
  margin: 0;
  font-size: 22px;
  line-height: 1.18;
  font-weight: 700;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}
.page-renderer-subtitle {
  margin: 4px 0 0;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}
.page-renderer-tools {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
}
.page-renderer-badges {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}
.page-renderer-badge {
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid var(--sc-app-border);
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
}
.page-renderer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.page-renderer-action {
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 7px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
}
.page-renderer-action:hover {
  border-color: var(--sc-semantic-surface-interactive);
  color: var(--sc-app-info-text);
  background: var(--sc-app-info-bg);
}
.tone-success { background: var(--sc-app-success-bg); color: var(--sc-app-success-text); }
.tone-warning { background: var(--sc-app-warning-bg); color: var(--sc-app-warning-text); }
.tone-danger { background: var(--sc-app-danger-bg); color: var(--sc-app-danger-text); }
.tone-info { background: var(--sc-app-info-bg); color: var(--sc-app-info-text); }
.tone-neutral { background: var(--sc-app-subtle-bg); color: var(--sc-app-text-primary); }

@media (max-width: 1200px) {
  .page-renderer-header h1,
  .page-renderer-header h2 {
    font-size: 20px;
  }
}

@media (max-width: 720px) {
  .page-renderer {
    gap: 10px;
  }
  .page-renderer-header {
    padding: 10px;
  }
  .page-renderer-tools {
    justify-content: flex-start;
  }
}
</style>
