<template>
  <PageRenderer
    v-if="useUnifiedWorkbenchRenderer"
    :contract="workbenchOrchestrationContract"
    :datasets="workbenchOrchestrationDatasets"
    @action="handleWorkbenchBlockAction"
  />

  <section v-else class="workbench">
    <header v-if="pageSectionEnabled('header', true) && pageSectionTagIs('header', 'header')" class="header" :style="pageSectionStyle('header')">
      <div>
        <p v-if="showHud" class="diagnostic">{{ pageText('diagnostic_hint', '诊断页仅用于排查，不作为正式产品界面。') }}</p>
        <h2>{{ pageText('header_title', '页面暂时无法打开') }}</h2>
        <p class="meta">{{ pageText('header_subtitle', '我们已为你保留可继续操作的入口。') }}</p>
        <p v-if="hasContext" class="context-line">
          {{ pageText('context_prefix', '推荐上下文：') }}{{ workspaceContextSummary }}
          <button class="ghost mini" @click="clearWorkspaceContext">{{ pageText('action_clear_context', '清除') }}</button>
        </p>
      </div>
      <div class="actions">
        <button
          v-for="action in headerActions"
          :key="action.key"
          class="ghost"
          :disabled="action.disabled"
          :title="action.disabledReason || ''"
          @click="executeWorkbenchAction(action.key)"
        >
          {{ action.label }}
        </button>
      </div>
    </header>

    <StatusPanel
      v-if="pageSectionEnabled('status_panel', true) && pageSectionTagIs('status_panel', 'section')"
      :title="pageText('panel_title', '页面暂时无法打开')"
      :message="message"
      :variant="panelVariant"
      :style="pageSectionStyle('status_panel')"
    />

    <section v-if="pageSectionEnabled('tiles', true) && pageSectionTagIs('tiles', 'section') && showTiles" class="tiles" :style="pageSectionStyle('tiles')">
      <button
        v-for="tile in tiles"
        :key="tile.key || tile.title"
        class="tile"
        :class="{ disabled: tile.policy.state !== 'enabled' }"
        :title="tile.tooltip"
        type="button"
        @click="handleTileClick(tile)"
      >
        <div class="tile-icon">{{ tile.icon || '•' }}</div>
        <div class="tile-body">
          <div class="tile-title">{{ tile.title || tile.key }}</div>
          <div class="tile-subtitle">{{ tile.subtitle || '' }}</div>
        </div>
      </button>
    </section>

    <div v-if="pageSectionEnabled('hud_details', true) && pageSectionTagIs('hud_details', 'div') && showHud" class="details" :style="pageSectionStyle('hud_details')">
      <div class="detail">
        <span class="label">{{ pageText('hud_label_reason', '原因') }}</span>
        <span class="value">{{ reasonLabel }}</span>
      </div>
      <div class="detail">
        <span class="label">{{ pageText('hud_label_menu', '菜单') }}</span>
        <span class="value">{{ menuId || pageText('hud_value_na', 'N/A') }}</span>
      </div>
      <div v-if="showHud" class="detail">
        <span class="label">{{ pageText('hud_label_action', '动作') }}</span>
        <span class="value">{{ actionId || pageText('hud_value_na', 'N/A') }}</span>
      </div>
      <div class="detail">
        <span class="label">{{ pageText('hud_label_route', '路由') }}</span>
        <span class="value">{{ route.fullPath }}</span>
      </div>
      <div v-if="diag" class="detail">
        <span class="label">{{ pageText('hud_label_diag', '诊断') }}</span>
        <span class="value">{{ diag }}</span>
      </div>
      <div v-if="showHud && diagActionType" class="detail">
        <span class="label">{{ pageText('hud_label_action_type', '动作类型') }}</span>
        <span class="value">{{ diagActionType }}</span>
      </div>
      <div v-if="showHud && diagContractType" class="detail">
        <span class="label">{{ pageText('hud_label_contract_type', '契约类型') }}</span>
        <span class="value">{{ diagContractType }}</span>
      </div>
      <div v-if="showHud && diagContractUrl" class="detail">
        <span class="label">{{ pageText('hud_label_contract_url', '契约链接') }}</span>
        <span class="value">{{ diagContractUrl }}</span>
      </div>
      <div v-if="showHud && diagMetaUrl" class="detail">
        <span class="label">{{ pageText('hud_label_meta_url', '元信息链接') }}</span>
        <span class="value">{{ diagMetaUrl }}</span>
      </div>
      <div v-if="showHud" class="detail">
        <span class="label">{{ pageText('hud_label_last_intent', '最近意图') }}</span>
        <span class="value">{{ lastIntent || pageText('hud_value_na', 'N/A') }}</span>
      </div>
      <div v-if="showHud" class="detail">
        <span class="label">{{ pageText('hud_label_trace_id', '追踪 ID') }}</span>
        <span class="value">
          {{ lastTraceId || pageText('hud_value_na', 'N/A') }}
          <button v-if="lastTraceId" class="ghost mini" @click="copyTrace">{{ pageText('action_copy', '复制') }}</button>
        </span>
      </div>
      <div v-if="showHud" class="detail">
        <span class="label">{{ pageText('hud_label_data_source', '数据源协议') }}</span>
        <span class="value">
          {{ hasStatusPanelDataSource ? pageText('hud_value_ready', '就绪') : pageText('hud_value_missing', '缺失') }}
          （type={{ statusPanelDataSourceType || pageText('hud_value_na', 'N/A') }}）
        </span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { ErrorCodes } from '../app/error_codes';
import { useSessionStore } from '../stores/session';
import { isHudEnabled } from '../config/debug';
import { capabilityTooltip, evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { hasWorkspaceContext as hasWorkspaceContextValue, readWorkspaceContext, stripWorkspaceContext } from '../app/workspaceContext';
import { normalizeEmbeddedSceneQuery, parseSceneKeyFromQuery } from '../app/routeQuery';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import { resolvePageOrchestrationContractFromSceneV1 } from '../app/sceneContractV1';
import PageRenderer from '../components/page/PageRenderer.vue';
import type { PageBlockActionEvent, PageOrchestrationContract } from '../app/pageOrchestration';
import type { Scene } from '../app/resolvers/sceneRegistry';
import type { NavNode } from '@sc/schema';

type UnknownDict = Record<string, unknown>;

interface WorkbenchTile {
  key?: string;
  title?: string;
  subtitle?: string;
  icon?: string;
  scene_key?: string;
  sceneKey?: string;
  route?: string;
  payload?: {
    scene_key?: string;
    sceneKey?: string;
    action_id?: number;
    menu_id?: number;
    model?: string;
    record_id?: number;
  };
}

interface TilePolicy {
  state?: string;
  missing?: string[];
}

interface EnrichedWorkbenchTile extends WorkbenchTile {
  policy: TilePolicy;
  tooltip: string;
}

function asObject(value: unknown): UnknownDict | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null;
  }
  return value as UnknownDict;
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function resolveSceneCode(scene: Scene): string {
  return asText(asObject(scene)?.code);
}

function resolveTileScene(tile: WorkbenchTile): string {
  return (
    asText(tile.scene_key) ||
    asText(tile.sceneKey) ||
    asText(tile.payload?.scene_key) ||
    asText(tile.payload?.sceneKey)
  );
}

// Workbench is a diagnostic-only surface and must not be used as product UI.
const route = useRoute();
const router = useRouter();

const reason = computed(() => String(route.query.reason || ''));
const menuId = computed(() => Number(route.query.menu_id || 0) || undefined);
const actionId = computed(() => Number(route.query.action_id || 0) || undefined);
const sceneKey = computed(() => parseSceneKeyFromQuery(route.query as LocationQueryRaw));
const session = useSessionStore();
const pageContract = usePageContract('workbench');
const pageText = pageContract.text;
const pageActionText = pageContract.actionText;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageHasDataSource = pageContract.hasDataSource;
const pageDataSourceType = pageContract.dataSourceType;
const pageGlobalActions = pageContract.globalActions;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;

const workbenchOrchestrationContract = computed<PageOrchestrationContract>(() => {
  return resolvePageOrchestrationContractFromSceneV1(
    pageContract.contract.value?.scene_contract_v1,
    pageContract.contract.value?.page_orchestration_v1,
    { pageType: 'workspace', layoutMode: 'workspace' },
  );
});
const useUnifiedWorkbenchRenderer = computed(() => {
  if (asText(route.query.legacy_workbench) === '1') return false;
  const contract = workbenchOrchestrationContract.value || {};
  const hasV1 = asText(contract.contract_version) === 'page_orchestration_v1';
  const zones = Array.isArray(contract.zones) ? contract.zones : [];
  return hasV1 && zones.length > 0;
});
const showHud = computed(() => isHudEnabled(route));
const lastTraceId = computed(() => session.lastTraceId || '');
const lastIntent = computed(() => session.lastIntent || '');
const diag = computed(() => String(route.query.diag || ''));
const diagActionType = computed(() => String(route.query.diag_action_type || ''));
const diagContractType = computed(() => String(route.query.diag_contract_type || ''));
const diagContractUrl = computed(() => String(route.query.diag_contract_url || ''));
const diagMetaUrl = computed(() => String(route.query.diag_meta_url || ''));
const workspaceContextQuery = computed(() => {
  return readWorkspaceContext(route.query as Record<string, unknown>);
});
const hasContext = computed(() => hasWorkspaceContextValue(workspaceContextQuery.value));
const workspaceContextSummary = computed(() => {
  const parts = [];
  if (workspaceContextQuery.value.preset) parts.push(`preset=${workspaceContextQuery.value.preset}`);
  if (workspaceContextQuery.value.search) parts.push(`search=${workspaceContextQuery.value.search}`);
  if (workspaceContextQuery.value.ctx_source) parts.push(`source=${workspaceContextQuery.value.ctx_source}`);
  if (workspaceContextQuery.value.project_id) parts.push(`project_id=${workspaceContextQuery.value.project_id}`);
  return parts.join(' · ');
});
const scene = computed<Scene | null>(() => {
  if (!sceneKey.value) return null;
  return (
    session.scenes.find((item) => item.key === sceneKey.value || resolveSceneCode(item) === sceneKey.value) || null
  );
});
const showTiles = computed(() => reason.value === ErrorCodes.CAPABILITY_MISSING && tiles.value.length > 0);
const statusPanelDataSourceType = computed(() => pageDataSourceType('ds_section_status_panel'));
const hasStatusPanelDataSource = computed(() => pageHasDataSource('ds_section_status_panel') && statusPanelDataSourceType.value === 'scene_context');
const workbenchOrchestrationDatasets = computed<Record<string, unknown>>(() => {
  const headerSummary = [
    { key: 'reason', label: pageText('hud_label_reason', '原因'), value: reasonLabel.value, tone: 'info' },
    { key: 'menu', label: pageText('hud_label_menu', '菜单'), value: menuId.value || pageText('hud_value_na', 'N/A'), tone: 'neutral' },
    { key: 'action', label: pageText('hud_label_action', '动作'), value: actionId.value || pageText('hud_value_na', 'N/A'), tone: 'neutral' },
  ];
  const panelSummary = [
    { key: 'panel', label: pageText('panel_title', '页面暂时无法打开'), value: message.value || '-', tone: panelVariant.value === 'error' ? 'danger' : 'warning' },
  ];
  const tileEntries = tiles.value.map((tile, idx) => ({
    id: String(tile.key || `tile-${idx + 1}`),
    key: String(tile.key || `tile-${idx + 1}`),
    title: String(tile.title || tile.key || `入口 ${idx + 1}`),
    hint: String(tile.subtitle || ''),
    scene_key: resolveTileScene(tile),
    route: String(tile.route || ''),
    action_key: 'open_scene',
    tile_key: String(tile.key || ''),
  }));
  const hudEntries = [
    { id: 'route', title: pageText('hud_label_route', '路由'), description: route.fullPath, tone: 'info' },
    { id: 'trace', title: pageText('hud_label_trace_id', '追踪 ID'), description: lastTraceId.value || pageText('hud_value_na', 'N/A'), tone: 'neutral' },
    { id: 'intent', title: pageText('hud_label_last_intent', '最近意图'), description: lastIntent.value || pageText('hud_value_na', 'N/A'), tone: 'neutral' },
  ];
  return {
    ds_section_header: headerSummary,
    ds_section_status_panel: panelSummary,
    ds_section_tiles: tileEntries,
    ds_section_hud_details: hudEntries,
  };
});
const headerActions = computed(() => {
  if (pageGlobalActions.value.length) {
    return pageGlobalActions.value;
  }
  return [
    { key: 'open_workbench', label: pageActionText('open_workbench', pageText('action_go_workbench', '返回工作台')), intent: 'ui.contract' },
    { key: 'open_menu', label: pageActionText('open_menu', pageText('action_open_menu', '打开菜单')), intent: 'ui.contract' },
    { key: 'refresh_page', label: pageActionText('refresh_page', pageText('action_refresh', '刷新')), intent: 'api.data' },
  ];
});
const tiles = computed<EnrichedWorkbenchTile[]>(() => {
  const rawTiles = Array.isArray(scene.value?.tiles) ? (scene.value?.tiles as WorkbenchTile[]) : [];
  if (!Array.isArray(rawTiles)) return [];
  return rawTiles.map((tile) => {
    const policy = evaluateCapabilityPolicy({ source: tile, available: session.capabilities });
    return {
      ...tile,
      policy,
      tooltip: capabilityTooltip(policy),
    };
  });
});

const reasonLabel = computed(() => {
  switch (reason.value) {
    case ErrorCodes.NAV_MENU_NO_ACTION:
      return pageText('reason_nav_menu_no_action', '菜单分组（无可执行动作）');
    case ErrorCodes.ACT_NO_MODEL:
      return pageText('reason_act_no_model', '动作未绑定模型');
    case ErrorCodes.ACT_UNSUPPORTED_TYPE:
      return pageText('reason_act_unsupported_type', '动作类型暂不支持');
    case ErrorCodes.CONTRACT_CONTEXT_MISSING:
      return pageText('reason_contract_context_missing', '契约上下文缺失');
    case ErrorCodes.CAPABILITY_MISSING:
      return pageText('reason_capability_missing', '缺少能力权限');
    default:
      return reason.value || pageText('reason_unknown', '未知原因');
  }
});

const message = computed(() => {
  switch (reason.value) {
    case ErrorCodes.NAV_MENU_NO_ACTION:
      return pageText('message_nav_menu_no_action', '当前菜单是目录，暂时没有可进入的子菜单。');
    case ErrorCodes.ACT_NO_MODEL:
      return pageText('message_act_no_model', '当前动作对应的是自定义工作区，未绑定数据模型。');
    case ErrorCodes.ACT_UNSUPPORTED_TYPE:
      return pageText('message_act_unsupported_type', '');
    case ErrorCodes.CONTRACT_CONTEXT_MISSING:
      return pageText('message_contract_context_missing', '页面缺少契约必需上下文（例如 action_id）。');
    case ErrorCodes.CAPABILITY_MISSING:
      return pageText('message_capability_missing', '');
    default:
      return pageText('message_default', '你可以返回工作台或打开菜单继续操作。');
  }
});

const panelVariant = computed(() => {
  if (reason.value === ErrorCodes.CAPABILITY_MISSING) {
    return 'forbidden_capability';
  }
  return 'error';
});

const firstReachableMenuId = computed(() => findFirstReachableMenuId(session.menuTree));

onMounted(() => {
  const normalized = normalizeEmbeddedSceneQuery(route.query as LocationQueryRaw);
  if (normalized.changed) {
    router.replace({ path: route.path, query: normalized.query }).catch(() => {});
    return;
  }
  if (!reason.value) {
    if (sceneKey.value) {
      router.replace({ path: `/s/${sceneKey.value}`, query: workspaceContextQuery.value }).catch(() => {});
      return;
    }
    router.replace({ path: '/', query: workspaceContextQuery.value }).catch(() => {});
  }
});

function refresh() {
  window.location.reload();
}

async function goToProjects() {
  await router.push({ path: session.resolveLandingPath('/'), query: workspaceContextQuery.value });
}

async function openFirstReachableMenu() {
  if (firstReachableMenuId.value) {
    await router.push({ path: `/m/${firstReachableMenuId.value}`, query: workspaceContextQuery.value });
    return;
  }
  await router.push({ path: session.resolveLandingPath('/'), query: workspaceContextQuery.value });
}

async function executeWorkbenchAction(actionKey: string) {
  const matched = headerActions.value.find((item) => item.key === actionKey);
  if (matched?.disabled) {
    return;
  }
  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: workspaceContextQuery.value,
    onRefresh: refresh,
    onOpenMenuFirstReachable: async () => {
      if (!firstReachableMenuId.value) return false;
      await router.push({ path: `/m/${firstReachableMenuId.value}`, query: workspaceContextQuery.value });
      return true;
    },
    onFallback: async (key) => {
      if (key === 'open_workbench') {
        await goToProjects();
        return true;
      }
      if (key === 'open_menu') {
        await openFirstReachableMenu();
        return true;
      }
      if (key === 'refresh_page') {
        refresh();
        return true;
      }
      return false;
    },
  });
  if (!handled && actionKey === 'refresh_page') {
    refresh();
  }
}

async function handleTileClick(tile: EnrichedWorkbenchTile) {
  const explicitScene = resolveTileScene(tile);
  if (explicitScene) {
    await router.push({ path: `/s/${explicitScene}`, query: workspaceContextQuery.value });
    return;
  }
  if (tile.policy?.state === 'disabled_capability') {
    await router.replace({
      name: 'workbench',
      query: {
        reason: ErrorCodes.CAPABILITY_MISSING,
        scene: sceneKey.value || undefined,
        missing: (tile.policy.missing || []).join(',') || undefined,
      },
    });
    return;
  }
  if (tile.route) {
    await router.push({ path: String(tile.route), query: workspaceContextQuery.value });
    return;
  }
  const payload = tile.payload || {};
  if (payload.action_id) {
    await router.push({
      path: `/a/${payload.action_id}`,
      query: { menu_id: payload.menu_id || undefined, ...workspaceContextQuery.value },
    });
    return;
  }
  if (payload.model && payload.record_id) {
    await router.push({
      path: `/r/${payload.model}/${payload.record_id}`,
      query: {
        menu_id: payload.menu_id || undefined,
        action_id: payload.action_id || undefined,
        ...workspaceContextQuery.value,
      },
    });
  }
}

function normalizeItemQuery(item: Record<string, unknown>): LocationQueryRaw {
  const raw = item.query;
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return workspaceContextQuery.value;
  return { ...workspaceContextQuery.value, ...(raw as Record<string, unknown>) };
}

async function handleWorkbenchBlockAction(event: PageBlockActionEvent) {
  const item = event.item && typeof event.item === 'object' ? event.item as Record<string, unknown> : {};
  const tileKey = asText(item.tile_key || item.key);
  if (tileKey) {
    const matchedTile = tiles.value.find((tile) => asText(tile.key) === tileKey);
    if (matchedTile) {
      await handleTileClick(matchedTile);
      return;
    }
  }
  const scene = asText(item.scene_key || item.sceneKey);
  if (scene) {
    await router.push({ path: `/s/${scene}`, query: normalizeItemQuery(item) });
    return;
  }
  const path = asText(item.path || item.route);
  if (path) {
    await router.push({ path, query: normalizeItemQuery(item) });
    return;
  }
  await executeWorkbenchAction(event.actionKey);
}

async function copyTrace() {
  if (!lastTraceId.value) return;
  try {
    await navigator.clipboard.writeText(lastTraceId.value);
  } catch {
    // noop
  }
}

function clearWorkspaceContext() {
  const nextQuery = stripWorkspaceContext(route.query as Record<string, unknown>);
  router.replace({ path: route.path, query: nextQuery }).catch(() => {});
}

function resolveNodeSceneKey(node: NavNode): string {
  return asText((node as NavNode & { scene_key?: string; sceneKey?: string }).scene_key)
    || asText((node as NavNode & { scene_key?: string; sceneKey?: string }).sceneKey)
    || asText(node.meta?.scene_key);
}

function findFirstReachableMenuId(nodes: NavNode[]): number | null {
  if (!Array.isArray(nodes)) {
    return null;
  }
  for (const node of nodes) {
    if (!node) {
      continue;
    }
    const menuId = Number(node.menu_id || node.id || 0) || 0;
    if (menuId) {
      if (node.meta?.action_id) {
        return menuId;
      }
      if (resolveNodeSceneKey(node)) {
        return menuId;
      }
    }
    const nested = findFirstReachableMenuId(node.children || []);
    if (nested) {
      return nested;
    }
  }
  return null;
}
</script>

<style scoped>
.workbench {
  display: grid;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions {
  display: flex;
  gap: 8px;
}

.meta {
  color: #64748b;
  font-size: 14px;
}

.diagnostic {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #b45309;
}

.context-line {
  margin: 8px 0 0;
  color: #334155;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.tiles {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.tile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
  background: white;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 12px 20px rgba(15, 23, 42, 0.08);
  text-align: left;
  cursor: pointer;
}

.tile.disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.tile-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.08);
  display: grid;
  place-items: center;
  font-weight: 700;
  color: #334155;
}

.tile-title {
  font-weight: 600;
  color: #0f172a;
}

.tile-subtitle {
  font-size: 12px;
  color: #64748b;
}

.detail {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 4px;
}

.ghost.mini {
  margin-left: 8px;
  padding: 4px 8px;
  font-size: 12px;
}

.label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94a3b8;
}

.value {
  font-weight: 600;
}

.ghost {
  background: transparent;
  color: #111827;
  border: 1px solid rgba(15, 23, 42, 0.12);
  padding: 10px 14px;
  border-radius: 10px;
  cursor: pointer;
}
</style>
