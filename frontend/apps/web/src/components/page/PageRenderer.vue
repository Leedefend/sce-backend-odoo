<template>
  <section class="page-renderer" :class="rendererClasses">
    <header class="page-renderer-header">
      <div class="page-renderer-title">
        <h2>{{ pageTitle }}</h2>
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

    <div v-if="isMyWorkPage" class="my-work-scene-layout">
      <ZoneRenderer
        v-for="zone in orderedZones"
        :key="zone.key"
        :zone="zone"
        :datasets="datasets"
        @action="onZoneAction"
      />
    </div>

    <div v-else-if="isRoleHomePage" class="role-home-layout">
      <ZoneRenderer
        v-for="zone in orderedZones"
        :key="zone.key"
        :zone="zone"
        :datasets="datasets"
        @action="onZoneAction"
      />
    </div>

    <div v-else-if="isCompanyDashboardPage" class="company-dashboard-layout">
      <ZoneRenderer
        v-for="zone in orderedZones"
        :key="zone.key"
        :zone="zone"
        :datasets="datasets"
        @action="onZoneAction"
      />
    </div>

    <div v-else-if="isProjectCockpitPage" class="cockpit-zone-layout">
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

const sceneKey = computed(() => String(props.contract.scene_key || ''));
const pageKey = computed(() => String(props.contract.page?.key || ''));
const pageTitle = computed(() => String(props.contract.page?.title || '页面'));
const pageSubtitle = computed(() => String(props.contract.page?.subtitle || ''));
const pageBadges = computed(() => Array.isArray(props.contract.page?.header?.badges)
  ? props.contract.page?.header?.badges || []
  : []);
const globalActions = computed<PageOrchestrationAction[]>(() => Array.isArray(props.contract.page?.global_actions)
  ? props.contract.page?.global_actions || []
  : []);

const isMyWorkPage = computed(() => sceneKey.value === 'my_work.workspace' || pageKey.value === 'my_work');
const isRoleHomePage = computed(() => sceneKey.value === 'workspace.home' || pageKey.value === 'workspace.home');
const isCompanyDashboardPage = computed(() => sceneKey.value === 'dashboard.company' || pageKey.value === 'dashboard.company');
const isProjectCockpitPage = computed(() => pageKey.value === 'project.management.dashboard');
const rendererClasses = computed(() => ({
  'page-renderer--role-home': isRoleHomePage.value,
  'page-renderer--my-work': isMyWorkPage.value,
  'page-renderer--company-dashboard': isCompanyDashboardPage.value,
  'page-renderer--project-cockpit': isProjectCockpitPage.value,
}));
const headerBadges = computed(() => {
  if (pageBadges.value.length) return pageBadges.value;
  if (isMyWorkPage.value) {
    return [
      { label: '个人事项', tone: 'info' },
      { label: '可执行待办', tone: 'success' },
    ];
  }
  if (isRoleHomePage.value) {
    return [
      { label: '角色定位', tone: 'info' },
      { label: '能力入口', tone: 'success' },
    ];
  }
  if (isCompanyDashboardPage.value) {
    return [
      { label: '经营总览', tone: 'info' },
      { label: '契约驱动', tone: 'neutral' },
    ];
  }
  return [];
});

const orderedZones = computed<PageOrchestrationZone[]>(() => {
  const zones = Array.isArray(props.contract.zones) ? [...props.contract.zones] : [];
  return zones.sort((a, b) => Number(b.priority || 0) - Number(a.priority || 0));
});

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
  gap: 14px;
  width: 100%;
  max-width: min(1380px, 100%);
  margin: 0 auto;
  min-width: 0;
}
.my-work-scene-layout,
.role-home-layout,
.company-dashboard-layout,
.workbench-zone-layout {
  display: grid;
  gap: 12px;
}
.cockpit-zone-layout {
  display: grid;
  gap: 16px;
}
.cockpit-focus-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 16px;
  min-width: 0;
}
.cockpit-support-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
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

.page-renderer--my-work {
  max-width: min(1440px, 100%);
}
.page-renderer--my-work .page-renderer-header {
  border-left: 4px solid var(--sc-semantic-surface-interactive);
  background: var(--sc-app-panel);
}
.page-renderer--my-work :deep(.zone-renderer) {
  border-radius: 8px;
  padding: 12px;
  box-shadow: none;
}
.page-renderer--my-work :deep(.zone-key-hero) {
  padding: 10px 12px;
}
.page-renderer--my-work :deep(.zone-key-hero .zone-renderer-body) {
  margin-top: 8px;
}
.page-renderer--my-work :deep(.zone-key-primary .zone-renderer-body) {
  grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
  align-items: start;
}
.page-renderer--my-work :deep(.zone-key-supporting) {
  padding: 8px 12px;
}
.page-renderer--my-work :deep(.zone-renderer-header h3) {
  font-size: 17px;
}
.page-renderer--my-work :deep(.zone-renderer-header p) {
  margin-top: 3px;
  font-size: 12px;
}
.page-renderer--my-work :deep(.zone-renderer-body) {
  gap: 10px;
  margin-top: 10px;
}
.page-renderer--my-work :deep(.block) {
  border-radius: 8px;
  padding: 10px;
  box-shadow: none;
}
.page-renderer--my-work :deep(.block-header h4) {
  font-size: 15px;
}
.page-renderer--my-work :deep(.metric-grid) {
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 8px;
}
.page-renderer--my-work :deep(.metric-item) {
  min-height: 76px;
  padding: 10px;
  border-radius: 8px;
  background: var(--sc-app-panel);
}
.page-renderer--my-work :deep(.metric-value) {
  margin-top: 4px;
  font-size: 24px;
}
.page-renderer--my-work :deep(.todo-list),
.page-renderer--my-work :deep(.alert-list) {
  gap: 8px;
  margin-top: 8px;
}
.page-renderer--my-work :deep(.todo-list) {
  max-height: 560px;
  overflow: auto;
  padding-right: 2px;
}
.page-renderer--my-work :deep(.todo-item),
.page-renderer--my-work :deep(.alert-item) {
  min-height: 68px;
  border-radius: 8px;
  padding: 9px 10px;
}
.page-renderer--my-work :deep(.todo-title),
.page-renderer--my-work :deep(.alert-title) {
  font-size: 14px;
}
.page-renderer--my-work :deep(.todo-desc),
.page-renderer--my-work :deep(.alert-desc) {
  margin-top: 4px;
  font-size: 12px;
}
.page-renderer--my-work :deep(.todo-open-btn),
.page-renderer--my-work :deep(.alert-open-btn),
.page-renderer--my-work :deep(.block-action-btn) {
  border-radius: 7px;
  padding: 5px 9px;
  font-size: 12px;
}
.page-renderer--my-work :deep(.entry-grid) {
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px;
}
.page-renderer--my-work :deep(.entry-item) {
  min-height: 72px;
  border-radius: 8px;
  padding: 10px;
  background: var(--sc-app-panel);
  transform: none;
}
.page-renderer--my-work :deep(.entry-title) {
  font-size: 14px;
}
.page-renderer--my-work :deep(.entry-hint) {
  margin-top: 4px;
  font-size: 12px;
}
.page-renderer--my-work :deep(.feed-list),
.page-renderer--my-work :deep(.accordion-content) {
  gap: 7px;
}
.page-renderer--my-work :deep(.feed-list) {
  max-height: 560px;
  overflow: auto;
  padding-right: 2px;
}
.page-renderer--my-work :deep(.feed-item),
.page-renderer--my-work :deep(.accordion-item) {
  border-radius: 8px;
  padding: 8px 10px;
  background: var(--sc-app-panel);
}
.page-renderer--my-work :deep(.feed-title),
.page-renderer--my-work :deep(.accordion-title) {
  font-size: 13px;
  line-height: 1.35;
}
.page-renderer--my-work :deep(.feed-desc),
.page-renderer--my-work :deep(.accordion-desc) {
  margin-top: 3px;
  font-size: 12px;
}
.page-renderer--my-work :deep(summary) {
  font-size: 14px;
}

.page-renderer--role-home {
  max-width: min(1440px, 100%);
  gap: 12px;
}
.page-renderer--role-home .page-renderer-header {
  border-left: 4px solid var(--sc-app-success-text);
  background: var(--sc-app-panel);
  padding: 10px 12px;
}
.page-renderer--role-home .page-renderer-header h2 {
  font-size: 20px;
}
.page-renderer--role-home :deep(.zone-renderer) {
  border-radius: 8px;
  padding: 12px;
  box-shadow: none;
}
.page-renderer--role-home :deep(.zone-renderer-header h3) {
  font-size: 16px;
}
.page-renderer--role-home :deep(.zone-renderer-header p) {
  margin-top: 3px;
  font-size: 12px;
}
.page-renderer--role-home :deep(.zone-renderer-body) {
  gap: 10px;
  margin-top: 10px;
}
.page-renderer--role-home :deep(.zone-key-hero) {
  border-color: var(--sc-app-success-border);
  background: var(--sc-app-success-bg);
}
.page-renderer--role-home :deep(.zone-key-hero .zone-renderer-body) {
  margin-top: 8px;
}
.page-renderer--role-home :deep(.zone-key-hero .block) {
  border-color: var(--sc-app-success-border);
  background: var(--sc-app-panel);
}
.page-renderer--role-home :deep(.summary-grid) {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.page-renderer--role-home :deep(.summary-item) {
  border-radius: 8px;
  min-height: 66px;
  background: var(--sc-app-muted-bg);
}
.page-renderer--role-home :deep(.summary-value) {
  font-size: 15px;
}
.page-renderer--role-home :deep(.zone-key-today_focus) {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-panel);
  padding: 12px;
}
.page-renderer--role-home :deep(.zone-key-today_focus .zone-renderer-header h3) {
  font-size: 18px;
}
.page-renderer--role-home :deep(.zone-key-today_focus .display-grid) {
  grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
}
.page-renderer--role-home :deep(.zone-key-today_focus .display-grid > :only-child) {
  grid-column: 1 / -1;
}
.page-renderer--role-home :deep(.zone-key-today_focus .block-todo-list .todo-list) {
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
}
.page-renderer--role-home :deep(.zone-key-analysis .zone-renderer-body.display-grid) {
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1fr) minmax(0, 1fr);
}
.page-renderer--role-home :deep(.block) {
  border-radius: 8px;
  padding: 10px;
  box-shadow: none;
}
.page-renderer--role-home :deep(.block-header h4) {
  font-size: 14px;
}
.page-renderer--role-home :deep(.metric-grid) {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.page-renderer--role-home :deep(.metric-item) {
  min-height: 82px;
  border-radius: 8px;
  padding: 10px;
}
.page-renderer--role-home :deep(.metric-value) {
  margin-top: 4px;
  font-size: 24px;
}
.page-renderer--role-home :deep(.metric-meta) {
  margin-top: 4px;
  font-size: 11px;
}
.page-renderer--role-home :deep(.todo-list),
.page-renderer--role-home :deep(.alert-list),
.page-renderer--role-home :deep(.feed-list) {
  gap: 8px;
  margin-top: 8px;
  max-height: 360px;
  overflow: auto;
  padding-right: 2px;
}
.page-renderer--role-home :deep(.todo-item),
.page-renderer--role-home :deep(.alert-item),
.page-renderer--role-home :deep(.feed-item) {
  min-height: 68px;
  border-radius: 8px;
  padding: 9px 10px;
}
.page-renderer--role-home :deep(.todo-title),
.page-renderer--role-home :deep(.alert-title),
.page-renderer--role-home :deep(.feed-title),
.page-renderer--role-home :deep(.entry-title) {
  font-size: 14px;
}
.page-renderer--role-home :deep(.todo-desc),
.page-renderer--role-home :deep(.alert-desc),
.page-renderer--role-home :deep(.feed-desc),
.page-renderer--role-home :deep(.entry-hint) {
  margin-top: 4px;
  font-size: 12px;
}
.page-renderer--role-home :deep(.entry-grid) {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.page-renderer--role-home :deep(.entry-item) {
  min-height: 82px;
  border-radius: 8px;
  padding: 10px;
  background: var(--sc-app-panel);
  transform: none;
}
.page-renderer--role-home :deep(.entry-meta) {
  margin-top: 8px;
}
.page-renderer--role-home :deep(.todo-open-btn),
.page-renderer--role-home :deep(.alert-open-btn),
.page-renderer--role-home :deep(.block-action-btn),
.page-renderer--role-home :deep(.summary-action-btn) {
  border-radius: 7px;
  padding: 5px 9px;
  font-size: 12px;
}

.page-renderer--company-dashboard {
  max-width: min(1500px, 100%);
}
.page-renderer--company-dashboard .page-renderer-header {
  border-left: 4px solid var(--sc-app-success-text);
  background: var(--sc-app-panel);
}
.page-renderer--company-dashboard :deep(.zone-renderer) {
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
  box-shadow: none;
}
.page-renderer--company-dashboard :deep(.zone-renderer-body.display-grid) {
  grid-template-columns: repeat(4, minmax(160px, 1fr));
  gap: 10px;
}
.page-renderer--company-dashboard :deep(.block) {
  border-radius: 8px;
  padding: 12px;
  box-shadow: none;
}
.page-renderer--company-dashboard :deep(.block-type-metric .block) {
  min-height: 112px;
  border-color: var(--sc-app-border);
  background: var(--sc-app-panel);
  padding: 14px;
}
.page-renderer--company-dashboard :deep(.block-type-alert_panel) {
  grid-column: span 2;
}
.page-renderer--company-dashboard :deep(.block-type-entry_grid) {
  grid-column: span 2;
}
.page-renderer--company-dashboard :deep(.block-type-record_summary) {
  grid-column: span 4;
}
.page-renderer--company-dashboard :deep(.metric-grid) {
  grid-template-columns: 1fr;
}
.page-renderer--company-dashboard :deep(.metric-item) {
  min-height: 72px;
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
}
.page-renderer--company-dashboard :deep(.metric-label) {
  font-size: 12px;
}
.page-renderer--company-dashboard :deep(.metric-value) {
  margin-top: 5px;
  font-size: 30px;
  line-height: 1.05;
}
.page-renderer--company-dashboard :deep(.metric-meta) {
  margin-top: 6px;
}
.page-renderer--company-dashboard :deep(.entry-grid) {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.page-renderer--company-dashboard :deep(.entry-item) {
  min-height: 62px;
  border-radius: 8px;
  padding: 10px;
  background: var(--sc-app-panel);
  transform: none;
}
.page-renderer--company-dashboard :deep(.alert-list) {
  gap: 8px;
  margin-top: 8px;
}
.page-renderer--company-dashboard :deep(.alert-item) {
  min-height: 92px;
  border-radius: 8px;
  padding: 10px;
}
.page-renderer--company-dashboard :deep(.alert-title),
.page-renderer--company-dashboard :deep(.entry-title) {
  font-size: 14px;
}
.page-renderer--company-dashboard :deep(.alert-desc),
.page-renderer--company-dashboard :deep(.entry-hint) {
  font-size: 12px;
}
.page-renderer--company-dashboard :deep(.summary-grid) {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.page-renderer--company-dashboard :deep(.summary-item) {
  border-radius: 8px;
  background: var(--sc-app-panel);
}

@media (max-width: 1200px) {
  .cockpit-focus-grid,
  .cockpit-support-grid {
    grid-template-columns: 1fr;
  }

  .page-renderer-header h2 {
    font-size: 20px;
  }

  .page-renderer--company-dashboard :deep(.zone-renderer-body.display-grid) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .page-renderer--company-dashboard :deep(.block-type-alert_panel),
  .page-renderer--company-dashboard :deep(.block-type-entry_grid),
  .page-renderer--company-dashboard :deep(.block-type-record_summary) {
    grid-column: span 2;
  }

  .page-renderer--my-work :deep(.zone-key-primary .zone-renderer-body) {
    grid-template-columns: 1fr;
  }

  .page-renderer--role-home :deep(.summary-grid),
  .page-renderer--role-home :deep(.metric-grid),
  .page-renderer--role-home :deep(.entry-grid),
  .page-renderer--role-home :deep(.zone-key-today_focus .display-grid),
  .page-renderer--role-home :deep(.zone-key-analysis .zone-renderer-body.display-grid) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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
  .page-renderer--company-dashboard :deep(.zone-renderer-body.display-grid),
  .page-renderer--company-dashboard :deep(.entry-grid),
  .page-renderer--company-dashboard :deep(.summary-grid) {
    grid-template-columns: 1fr;
  }
  .page-renderer--company-dashboard :deep(.block-type-alert_panel),
  .page-renderer--company-dashboard :deep(.block-type-entry_grid),
  .page-renderer--company-dashboard :deep(.block-type-record_summary) {
    grid-column: span 1;
  }
  .page-renderer--my-work :deep(.todo-list),
  .page-renderer--my-work :deep(.feed-list),
  .page-renderer--role-home :deep(.todo-list),
  .page-renderer--role-home :deep(.alert-list),
  .page-renderer--role-home :deep(.feed-list) {
    max-height: 460px;
  }
  .page-renderer--role-home :deep(.summary-grid),
  .page-renderer--role-home :deep(.metric-grid),
  .page-renderer--role-home :deep(.entry-grid),
  .page-renderer--role-home :deep(.zone-key-today_focus .display-grid),
  .page-renderer--role-home :deep(.zone-key-analysis .zone-renderer-body.display-grid) {
    grid-template-columns: 1fr;
  }
}
</style>
