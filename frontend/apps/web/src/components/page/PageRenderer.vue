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

    <div v-if="isProjectCockpitPage" class="cockpit-zone-layout">
      <ZoneRenderer
        v-if="cockpitMetricsZone"
        :key="cockpitMetricsZone.key"
        :zone="cockpitMetricsZone"
        :datasets="datasets"
        @action="onZoneAction"
      />

      <div class="cockpit-focus-grid">
        <ZoneRenderer
          v-if="cockpitRiskZone"
          :key="cockpitRiskZone.key"
          :zone="cockpitRiskZone"
          :datasets="datasets"
          @action="onZoneAction"
        />
        <ZoneRenderer
          v-if="cockpitProgressZone"
          :key="cockpitProgressZone.key"
          :zone="cockpitProgressZone"
          :datasets="datasets"
          @action="onZoneAction"
        />
      </div>

      <div class="cockpit-support-grid">
        <ZoneRenderer
          v-for="zone in cockpitSupportZones"
          :key="zone.key"
          :zone="zone"
          :datasets="datasets"
          @action="onZoneAction"
        />
      </div>

      <ZoneRenderer
        v-for="zone in cockpitTrailingZones"
        :key="zone.key"
        :zone="zone"
        :datasets="datasets"
        @action="onZoneAction"
      />
    </div>

    <template v-else>
      <ZoneRenderer
        v-for="zone in orderedZones"
        :key="zone.key"
        :zone="zone"
        :datasets="datasets"
        @action="onZoneAction"
      />
    </template>
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

const pageKey = computed(() => String(props.contract.page?.key || ''));
const isProjectCockpitPage = computed(() => pageKey.value === 'project.management.dashboard');

function zoneMatches(zone: PageOrchestrationZone, name: string) {
  const key = String(zone.key || '');
  return key === name || key.endsWith(`.${name}`);
}

const cockpitMetricsZone = computed<PageOrchestrationZone | null>(() => (
  orderedZones.value.find((zone) => zoneMatches(zone, 'metrics')) || null
));

const cockpitRiskZone = computed<PageOrchestrationZone | null>(() => (
  orderedZones.value.find((zone) => zoneMatches(zone, 'risk')) || null
));

const cockpitProgressZone = computed<PageOrchestrationZone | null>(() => (
  orderedZones.value.find((zone) => zoneMatches(zone, 'progress')) || null
));

const cockpitSupportZones = computed<PageOrchestrationZone[]>(() => {
  if (!isProjectCockpitPage.value) return [];
  const wantedOrder = ['contract', 'cost', 'finance'];
  return wantedOrder
    .map((name) => orderedZones.value.find((zone) => zoneMatches(zone, name)))
    .filter((zone): zone is PageOrchestrationZone => Boolean(zone));
});

const cockpitTrailingZones = computed<PageOrchestrationZone[]>(() => {
  if (!isProjectCockpitPage.value) return [];
  return orderedZones.value.filter((zone) => (
    !zoneMatches(zone, 'metrics')
    && !zoneMatches(zone, 'risk')
    && !zoneMatches(zone, 'progress')
    && !zoneMatches(zone, 'contract')
    && !zoneMatches(zone, 'cost')
    && !zoneMatches(zone, 'finance')
  ));
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
  gap: 20px;
  max-width: 1380px;
  margin: 0 auto;
}
.workbench-zone-layout {
  display: grid;
  gap: 16px;
}
.cockpit-zone-layout {
  display: grid;
  gap: 16px;
}
.cockpit-focus-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 16px;
}
.cockpit-support-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}
.page-renderer-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px;
  border: 1px solid #cfe2ff;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 65%);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.06);
}
.page-renderer-header h2 {
  margin: 0;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.2px;
}
.page-renderer-subtitle {
  margin: 8px 0 0;
  color: #475569;
  font-size: 15px;
}
.page-renderer-badges {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.page-renderer-badge {
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  font-size: 12px;
  font-weight: 600;
}
.page-renderer-actions {
  display: flex;
  gap: 10px;
}
.page-renderer-action {
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: #fff;
  padding: 8px 14px;
  font-weight: 600;
  cursor: pointer;
}
.tone-success { background: #ecfdf5; color: #047857; }
.tone-warning { background: #fffbeb; color: #b45309; }
.tone-danger { background: #fef2f2; color: #b91c1c; }
.tone-info { background: #eff6ff; color: #1d4ed8; }
.tone-neutral { background: #f9fafb; color: #374151; }

@media (max-width: 1200px) {
  .workbench-secondary-grid {
    grid-template-columns: 1fr;
  }

  .cockpit-focus-grid,
  .cockpit-support-grid {
    grid-template-columns: 1fr;
  }

  .page-renderer-header h2 {
    font-size: 24px;
  }
}
</style>
