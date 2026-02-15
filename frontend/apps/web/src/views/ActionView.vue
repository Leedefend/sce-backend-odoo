<template>
  <section class="page">
    <section v-if="appliedPresetLabel" class="route-preset">
      <p>已应用推荐筛选：{{ appliedPresetLabel }}<span v-if="routeContextSource">（来源：{{ routeContextSource }}）</span></p>
      <button class="clear-btn" @click="clearRoutePreset">清除推荐</button>
    </section>
    <KanbanPage
      v-if="viewMode === 'kanban'"
      :title="pageTitle"
      :status="status"
      :loading="status === 'loading' || batchBusy"
      :error-message="errorMessage"
      :trace-id="traceId"
      :error="error"
      :records="records"
      :fields="kanbanFields"
      :title-field="kanbanTitleField"
      :subtitle="subtitle"
      :status-label="statusLabel"
      :on-reload="reload"
      :on-card-click="handleRowClick"
    />
    <ListPage
      v-else
      :title="pageTitle"
      :model="model"
      :status="status"
      :loading="status === 'loading' || batchBusy"
      :error-message="errorMessage"
      :trace-id="traceId"
      :error="error"
      :columns="columns"
      :records="records"
      :sort-label="sortLabel"
      :sort-options="sortOptions"
      :sort-value="sortValue"
      :filter-value="filterValue"
      :search-term="searchTerm"
      :subtitle="subtitle"
      :status-label="statusLabel"
      :selected-ids="selectedIds"
      :batch-message="batchMessage"
      :batch-details="batchDetails"
      :failed-csv-available="Boolean(failedCsvContentB64)"
      :has-more-failures="batchHasMoreFailures"
      :show-assign="hasAssigneeField"
      :assignee-options="assigneeOptions"
      :selected-assignee-id="selectedAssigneeId"
      :list-profile="listProfile"
      :on-reload="reload"
      :on-search="handleSearch"
      :on-sort="handleSort"
      :on-filter="handleFilter"
      :on-toggle-selection="handleToggleSelection"
      :on-toggle-selection-all="handleToggleSelectionAll"
      :on-batch-action="handleBatchAction"
      :on-batch-assign="handleBatchAssign"
      :on-batch-export="handleBatchExport"
      :on-assignee-change="handleAssigneeChange"
      :on-download-failed-csv="handleDownloadFailedCsv"
      :on-load-more-failures="handleLoadMoreFailures"
      :on-batch-detail-action="handleBatchDetailAction"
      :on-clear-selection="clearSelection"
      :on-row-click="handleRowClick"
    />

    <DevContextPanel
      :visible="showHud"
      title="View Context"
      :entries="hudEntries"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { batchUpdateRecords, exportRecordsCsv, listRecords, listRecordsRaw } from '../api/data';
import { trackUsageEvent } from '../api/usage';
import { resolveAction } from '../app/resolvers/actionResolver';
import { loadActionContract } from '../api/contract';
import { config } from '../config';
import { useSessionStore } from '../stores/session';
import ListPage from '../pages/ListPage.vue';
import KanbanPage from '../pages/KanbanPage.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import { deriveListStatus } from '../app/view_state';
import { isHudEnabled } from '../config/debug';
import { ErrorCodes } from '../app/error_codes';
import { evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { resolveSuggestedAction, useStatus } from '../composables/useStatus';
import { describeSuggestedAction, runSuggestedAction } from '../composables/useSuggestedAction';
import type { Scene, SceneListProfile } from '../app/resolvers/sceneRegistry';
import { readWorkspaceContext, stripWorkspaceContext } from '../app/workspaceContext';
import type { NavNode } from '@sc/schema';

type NavNodeWithScene = NavNode & {
  scene_key?: string;
  sceneKey?: string;
};

function resolveSceneCode(scene: Scene): string {
  const raw = scene as Scene & { code?: string };
  return typeof raw.code === 'string' ? raw.code : '';
}

function resolveNodeSceneKey(node: NavNode): string {
  const raw = node as NavNodeWithScene;
  return raw.scene_key || raw.sceneKey || node.meta?.scene_key || '';
}

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const status = ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>('idle');
const traceId = ref('');
const lastTraceId = ref('');
const records = ref<Array<Record<string, unknown>>>([]);
const searchTerm = ref('');
const sortValue = ref('');
const filterValue = ref<'all' | 'active' | 'archived'>('all');
const columns = ref<string[]>([]);
const kanbanFields = ref<string[]>([]);
const hasActiveField = ref(false);
const hasAssigneeField = ref(false);
const assigneeOptions = ref<Array<{ id: number; name: string }>>([]);
const selectedAssigneeId = ref<number | null>(null);
const selectedIds = ref<number[]>([]);
const batchMessage = ref('');
type BatchDetailLine = { text: string; actionRaw?: string; actionLabel?: string };
const batchDetails = ref<BatchDetailLine[]>([]);
const failedCsvFileName = ref('');
const failedCsvContentB64 = ref('');
const batchFailedOffset = ref(0);
const batchFailedLimit = ref(12);
const batchHasMoreFailures = ref(false);
const lastBatchRequest = ref<{
  model: string;
  ids: number[];
  action: 'archive' | 'activate' | 'assign';
  assigneeId?: number;
  ifMatchMap: Record<number, string>;
  idempotencyKey: string;
  context: Record<string, unknown>;
} | null>(null);
const batchBusy = ref(false);
const lastIntent = ref('');
const lastWriteMode = ref('');
const lastLatencyMs = ref<number | null>(null);
const appliedPresetLabel = ref('');
const routeContextSource = ref('');
const lastTrackedPreset = ref('');
const { error, clearError, setError } = useStatus();
type ContractColumnSchema = { name?: string };
type ContractViewBlock = {
  columns?: string[];
  columnsSchema?: ContractColumnSchema[];
  columns_schema?: ContractColumnSchema[];
  fields?: string[];
  model?: string;
  order?: string;
};
type ActionContractLoose = Awaited<ReturnType<typeof loadActionContract>> & {
  views?: {
    tree?: ContractViewBlock;
    list?: ContractViewBlock;
    kanban?: ContractViewBlock;
    form?: ContractViewBlock;
  };
  ui_contract?: {
    views?: {
      tree?: ContractViewBlock;
      list?: ContractViewBlock;
      kanban?: ContractViewBlock;
    };
    columns?: string[];
    columnsSchema?: ContractColumnSchema[];
  };
  fields?: Record<string, unknown>;
  model?: string;
  head?: { model?: string };
  data?: {
    type?: string;
    url?: string;
    target?: string;
  };
};
type ActionMetaLoose = {
  order?: string;
  url?: string;
};

const actionId = computed(() => Number(route.params.actionId));
const actionMeta = computed(() => session.currentAction);

const model = computed(() => actionMeta.value?.model ?? '');
const injectedTitle = inject('pageTitle', computed(() => ''));
const menuId = computed(() => Number(route.query.menu_id ?? 0));
const viewMode = computed(() => (actionMeta.value?.view_modes?.[0] ?? 'tree').toString());
const sortLabel = computed(() => sortValue.value || 'id asc');
const sortOptions = computed(() => [
  { label: 'Updated ↓ / Name ↑', value: 'write_date desc,name asc' },
  { label: 'Updated ↑ / Name ↑', value: 'write_date asc,name asc' },
  { label: 'Name ↑ / Updated ↓', value: 'name asc,write_date desc' },
  { label: 'Name ↓ / Updated ↓', value: 'name desc,write_date desc' },
]);
const subtitle = computed(() => `${records.value.length} records · sorted by ${sortLabel.value}`);
const kanbanTitleField = computed(() => {
  const candidates = ['display_name', 'name'];
  const found = candidates.find((field) => kanbanFields.value.includes(field));
  return found || kanbanFields.value[0] || 'id';
});
const statusLabel = computed(() => {
  if (status.value === 'loading') return 'Loading';
  if (status.value === 'error') return 'Error';
  if (status.value === 'empty') return 'Empty';
  return 'Ready';
});
const pageTitle = computed(() => injectedTitle?.value || actionMeta.value?.name || 'Workspace');
const showHud = computed(() => isHudEnabled(route));
const errorMessage = computed(() => (error.value?.code ? `code=${error.value.code} · ${error.value.message}` : error.value?.message || ''));
const sceneKey = computed(() => {
  const metaKey = route.meta?.sceneKey as string | undefined;
  if (metaKey) return metaKey;
  const queryKey = (route.query.scene_key || route.query.scene) as string | undefined;
  if (queryKey) return String(queryKey);
  const node = findMenuNode(session.menuTree, menuId.value);
  return node ? resolveNodeSceneKey(node) : '';
});
const scene = computed<Scene | null>(() => {
  if (!sceneKey.value) return null;
  return session.scenes.find((item: Scene) => item.key === sceneKey.value || resolveSceneCode(item) === sceneKey.value) || null;
});
const listProfile = computed<SceneListProfile | null>(() => (scene.value?.list_profile as SceneListProfile) || null);
const hudEntries = computed(() => [
  { label: 'action_id', value: actionId.value || '-' },
  { label: 'menu_id', value: menuId.value || '-' },
  { label: 'scene_key', value: sceneKey.value || '-' },
  { label: 'model', value: model.value || '-' },
  { label: 'view_mode', value: viewMode.value || '-' },
  { label: 'order', value: sortLabel.value || '-' },
  { label: 'last_intent', value: lastIntent.value || '-' },
  { label: 'write_mode', value: lastWriteMode.value || '-' },
  { label: 'trace_id', value: traceId.value || lastTraceId.value || '-' },
  { label: 'latency_ms', value: lastLatencyMs.value ?? '-' },
  { label: 'route', value: route.fullPath },
]);

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
}

function applyRoutePreset() {
  const preset = String(route.query.preset || '').trim();
  const routeSearch = String(route.query.search || '').trim();
  const ctxSource = String(route.query.ctx_source || '').trim();
  routeContextSource.value = ctxSource;
  let changed = false;
  const setIfDiff = <T>(target: { value: T }, next: T) => {
    if (target.value === next) return;
    target.value = next;
    changed = true;
  };

  if (preset === 'pending_approval') {
    appliedPresetLabel.value = '待审批合同';
    setIfDiff(searchTerm, routeSearch || '审批');
    setIfDiff(filterValue, 'active');
  } else if (preset === 'project_intake') {
    appliedPresetLabel.value = '项目立项';
    setIfDiff(searchTerm, routeSearch || '立项');
    setIfDiff(filterValue, 'active');
  } else if (preset === 'cost_watchlist') {
    appliedPresetLabel.value = '成本台账关注';
    setIfDiff(searchTerm, routeSearch || '成本');
  } else {
    appliedPresetLabel.value = '';
    if (routeSearch) {
      setIfDiff(searchTerm, routeSearch);
    }
  }
  if (preset && preset !== lastTrackedPreset.value) {
    lastTrackedPreset.value = preset;
    void trackUsageEvent('workspace.preset.apply', { preset, view: 'action' }).catch(() => {});
  }
  if (!preset) {
    lastTrackedPreset.value = '';
  }
  return changed;
}

function clearRoutePreset() {
  appliedPresetLabel.value = '';
  routeContextSource.value = '';
  const nextQuery = stripWorkspaceContext(route.query as Record<string, unknown>);
  void trackUsageEvent('workspace.preset.clear', { view: 'action' }).catch(() => {});
  router.replace({ name: 'action', params: route.params, query: nextQuery }).catch(() => {});
}

function mergeContext(base: Record<string, unknown> | string | undefined) {
  if (!base || typeof base === 'string') {
    return menuId.value ? { menu_id: menuId.value } : {};
  }
  if (!menuId.value) {
    return base;
  }
  return { ...base, menu_id: menuId.value };
}

function normalizeDomain(domain: unknown) {
  if (Array.isArray(domain)) {
    return domain;
  }
  return [];
}

function mergeSceneDomain(base: unknown, sceneFilters: unknown) {
  const baseDomain = normalizeDomain(base);
  const sceneDomain = normalizeDomain(sceneFilters);
  if (!sceneDomain.length) {
    return baseDomain;
  }
  if (!baseDomain.length) {
    return sceneDomain;
  }
  return [...sceneDomain, ...baseDomain];
}

function mergeActiveFilter(base: unknown) {
  const domain = normalizeDomain(base);
  if (!hasActiveField.value || filterValue.value === 'all') {
    return domain;
  }
  const activeClause = ['active', '=', filterValue.value === 'active'];
  if (!domain.length) {
    return [activeClause];
  }
  return [...domain, activeClause];
}

function uniqueFields(fields: string[]) {
  const seen = new Set<string>();
  return fields.filter((field) => {
    if (!field) return false;
    if (seen.has(field)) return false;
    seen.add(field);
    return true;
  });
}

function resolveRequestedFields(contractFields: string[], profile: SceneListProfile | null) {
  const profileColumns = profile?.columns ?? [];
  const secondary = profile?.row_secondary ? [profile.row_secondary] : [];
  return uniqueFields([...profileColumns, ...secondary, ...contractFields]);
}

function findMenuNode(nodes: NavNode[], menuId?: number): NavNode | null {
  if (!menuId) {
    return null;
  }
  const walk = (items: NavNode[]): NavNode | null => {
    for (const node of items) {
      if (node.menu_id === menuId || node.id === menuId) {
        return node;
      }
      if (node.children?.length) {
        const found = walk(node.children);
        if (found) return found;
      }
    }
    return null;
  };
  return walk(nodes) || null;
}

function pickColumns(rows: Array<Record<string, unknown>>) {
  if (!rows.length) {
    return ['id', 'name'];
  }
  const first = rows[0];
  const keys = Object.keys(first);
  return keys.slice(0, 6);
}

function downloadCsvBase64(filename: string, mimeType: string, contentB64: string) {
  if (!contentB64) return;
  const binary = atob(contentB64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  const blob = new Blob([bytes], { type: mimeType || 'text/csv' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename || 'export.csv';
  link.click();
  URL.revokeObjectURL(url);
}

function applyBatchFailureArtifacts(result: {
  failed_preview?: Array<{ id: number; reason_code: string; message: string; retryable?: boolean; suggested_action?: string }>;
  failed_page_offset?: number;
  failed_page_limit?: number;
  failed_has_more?: boolean;
  failed_truncated?: number;
  failed_csv_file_name?: string;
  failed_csv_content_b64?: string;
}, options?: { append?: boolean }) {
  const preview = Array.isArray(result.failed_preview) ? result.failed_preview : [];
  const lines: BatchDetailLine[] = preview.map((item) => {
    const hint = resolveSuggestedAction(item.suggested_action, item.reason_code, item.retryable);
    const retryTag = item.retryable === true ? 'retryable' : item.retryable === false ? 'non-retryable' : '';
    const text = [`#${item.id} ${item.reason_code}: ${item.message}`, retryTag, hint].filter(Boolean).join(' | ');
    const action = describeSuggestedAction(item.suggested_action, {
      hasRetryHandler: true,
      hasActionHandler: false,
    });
    return {
      text,
      actionRaw: action.canRun ? action.parsed.raw : '',
      actionLabel: action.label,
    };
  });
  if (options?.append) {
    batchDetails.value = [...batchDetails.value, ...lines];
  } else {
    batchDetails.value = lines;
  }
  batchFailedOffset.value = Number(result.failed_page_offset || 0) + preview.length;
  batchFailedLimit.value = Number(result.failed_page_limit || 12) || 12;
  batchHasMoreFailures.value = Boolean(result.failed_has_more);
  if ('failed_csv_file_name' in result && result.failed_csv_file_name) {
    failedCsvFileName.value = String(result.failed_csv_file_name || '');
  }
  if ('failed_csv_content_b64' in result && result.failed_csv_content_b64) {
    failedCsvContentB64.value = String(result.failed_csv_content_b64 || '');
  }
}

function handleBatchDetailAction(actionRaw: string) {
  runSuggestedAction(actionRaw, { onRetry: reload });
}

function extractColumnsFromContract(contract: Awaited<ReturnType<typeof loadActionContract>>) {
  const typed = contract as ActionContractLoose;
  const directViews = typed.views || typed.ui_contract?.views;
  if (directViews) {
    const treeBlock = directViews.tree || directViews.list;
    const treeColumns = treeBlock?.columns;
    if (Array.isArray(treeColumns) && treeColumns.length) {
      return treeColumns;
    }
    const treeSchema = treeBlock?.columnsSchema || treeBlock?.columns_schema;
    if (Array.isArray(treeSchema) && treeSchema.length) {
      return treeSchema.map((col) => col.name).filter(Boolean) as string[];
    }
  }

  const columns = typed.ui_contract?.columns;
  if (Array.isArray(columns) && columns.length) {
    return columns;
  }
  const schema = typed.ui_contract?.columnsSchema;
  if (Array.isArray(schema) && schema.length) {
    return schema.map((col) => col.name).filter(Boolean) as string[];
  }
  const rawFields = contract?.ui_contract_raw?.fields;
  if (rawFields && typeof rawFields === 'object') {
    return Object.keys(rawFields);
  }
  return [];
}

function extractKanbanFields(contract: Awaited<ReturnType<typeof loadActionContract>>) {
  const typed = contract as ActionContractLoose;
  const directViews = typed.views || typed.ui_contract?.views;
  if (directViews) {
    const kanbanBlock = directViews.kanban;
    if (Array.isArray(kanbanBlock?.fields) && kanbanBlock.fields.length) {
      return kanbanBlock.fields;
    }
  }
  const fieldsMap = typed.fields || typed.ui_contract_raw?.fields;
  if (fieldsMap && typeof fieldsMap === 'object') {
    const preferred = ['display_name', 'name', 'stage_id', 'user_id', 'partner_id', 'write_date', 'create_date'];
    const available = Object.keys(fieldsMap);
    const picked = preferred.filter((field) => available.includes(field));
    if (picked.length) {
      return picked;
    }
    return available.slice(0, 6);
  }
  return ['name', 'id'];
}

function resolveModelFromContract(contract: Awaited<ReturnType<typeof loadActionContract>>) {
  const typed = contract as ActionContractLoose;
  const direct = typed.model;
  if (typeof direct === 'string' && direct.trim()) {
    return direct.trim();
  }
  const headModel = typed.head?.model;
  if (typeof headModel === 'string' && headModel.trim()) {
    return headModel.trim();
  }
  const viewModel = typed.views?.tree?.model || typed.views?.form?.model || typed.views?.kanban?.model;
  if (typeof viewModel === 'string' && viewModel.trim()) {
    return viewModel.trim();
  }
  return '';
}

function getActionType(meta: unknown) {
  const raw = (meta as { type?: string; action_type?: string }) || {};
  return String(raw.type || raw.action_type || '').toLowerCase();
}

function isClientAction(meta: unknown) {
  const raw = meta as { tag?: string; type?: string; action_type?: string };
  const tag = String(raw?.tag || '').toLowerCase();
  const actionType = getActionType(meta);
  return actionType.includes('client') || tag.length > 0;
}

function isUrlAction(meta: unknown, contract: unknown) {
  const actionType = getActionType(meta);
  if (actionType.includes('act_url') || actionType.includes('url')) {
    return true;
  }
  const typed = contract as ActionContractLoose;
  const contractType = String(typed.data?.type || '').toLowerCase();
  return contractType === 'url_redirect';
}

function normalizeUrlTarget(target: unknown) {
  const raw = String(target || '').toLowerCase();
  if (raw === 'self' || raw === 'current' || raw === 'main') {
    return 'self';
  }
  return 'new';
}

function isShellRoute(url: string) {
  return (
    url === '/' ||
    url.startsWith('/s/') ||
    url.startsWith('/m/') ||
    url.startsWith('/a/') ||
    url.startsWith('/r/') ||
    url.startsWith('/login') ||
    url.startsWith('/admin/')
  );
}

function resolveNavigationUrl(url: string) {
  const raw = String(url || '').trim();
  if (!raw) {
    return '';
  }
  if (/^https?:\/\//i.test(raw)) {
    return raw;
  }
  if (!raw.startsWith('/')) {
    return raw;
  }
  try {
    return new URL(raw, config.apiBaseUrl).toString();
  } catch {
    return raw;
  }
}

function isPortalPath(url: string) {
  return url.startsWith('/portal/');
}

function resolvePortalBridgeBase() {
  try {
    const base = new URL(config.apiBaseUrl);
    if (base.hostname === 'localhost') {
      base.hostname = '127.0.0.1';
    }
    return base.toString();
  } catch {
    return config.apiBaseUrl;
  }
}

function buildPortalBridgeUrl(url: string) {
  const nextPath = url.startsWith('/') ? url : `/${url}`;
  const bridge = new URL('/portal/bridge', resolvePortalBridgeBase());
  bridge.searchParams.set('next', nextPath);
  if (session.token) {
    bridge.searchParams.set('token', session.token);
  }
  if (config.odooDb) {
    bridge.searchParams.set('db', config.odooDb);
  }
  return bridge.toString();
}

function resolveActionUrl(meta: unknown, contract: unknown) {
  const metaTyped = (meta as { url?: string }) || {};
  const metaUrl = String(metaTyped.url || '').trim();
  if (metaUrl) {
    return metaUrl;
  }
  const typed = contract as ActionContractLoose;
  const contractUrl = String(typed.data?.url || '').trim();
  if (contractUrl) {
    return contractUrl;
  }
  return '';
}

async function redirectUrlAction(meta: unknown, contract: unknown) {
  const url = resolveActionUrl(meta, contract);
  if (!url) {
    const actionType = getActionType(meta);
    const typed = contract as ActionContractLoose;
    const contractType = String(typed.data?.type || '').toLowerCase();
    await router.replace({
      name: 'workbench',
      query: {
        menu_id: menuId.value || undefined,
        action_id: actionId.value || undefined,
        reason: ErrorCodes.ACT_UNSUPPORTED_TYPE,
        diag: 'act_url_empty',
        diag_action_type: actionType || undefined,
        diag_contract_type: contractType || undefined,
      },
    });
    return true;
  }
  const metaTyped = (meta as { target?: string }) || {};
  const typed = contract as ActionContractLoose;
  const target = normalizeUrlTarget(metaTyped.target || typed.data?.target);
  if (target === 'self' && url.startsWith('/')) {
    if (isShellRoute(url)) {
      await router.replace(url);
    } else {
      if (isPortalPath(url)) {
        window.location.assign(buildPortalBridgeUrl(url));
      } else {
        window.location.assign(resolveNavigationUrl(url));
      }
    }
    return true;
  }
  const navUrl = resolveNavigationUrl(url);
  window.open(navUrl, target === 'self' ? '_self' : '_blank', 'noopener,noreferrer');
  return true;
}

function isWindowAction(meta: unknown) {
  const actionType = getActionType(meta);
  return actionType.includes('act_window') || actionType.includes('window') || actionType === '';
}

async function loadAssigneeOptions() {
  if (!hasAssigneeField.value) {
    assigneeOptions.value = [];
    selectedAssigneeId.value = null;
    return;
  }
  try {
    const result = await listRecords({
      model: 'res.users',
      fields: ['id', 'name'],
      domain: [['active', '=', true]],
      order: 'name asc',
      limit: 80,
    });
    const rows = Array.isArray(result.records) ? result.records : [];
    assigneeOptions.value = rows
      .map((row) => {
        const id = typeof row.id === 'number' ? row.id : Number(row.id);
        const name = String(row.name || '');
        if (!id || Number.isNaN(id) || !name) return null;
        return { id, name };
      })
      .filter((row): row is { id: number; name: string } => !!row);
    if (selectedAssigneeId.value && !assigneeOptions.value.find((opt) => opt.id === selectedAssigneeId.value)) {
      selectedAssigneeId.value = null;
    }
  } catch {
    assigneeOptions.value = [];
    selectedAssigneeId.value = null;
  }
}

async function load() {
  status.value = 'loading';
  clearError();
  traceId.value = '';
  lastIntent.value = 'api.data.list';
  lastWriteMode.value = 'read';
  lastLatencyMs.value = null;
  records.value = [];
  columns.value = [];
  kanbanFields.value = [];
  const startedAt = Date.now();

  if (!actionId.value) {
    setError(new Error('Action id missing'), 'Action id missing');
    status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
    return;
  }

  try {
    const { contract, meta } = await resolveAction(session.menuTree, actionId.value, actionMeta.value);
    if (meta) {
      session.setActionMeta(meta);
    }
    if (isUrlAction(meta, contract)) {
      await redirectUrlAction(meta, contract);
      return;
    }
    if (!sortValue.value) {
      const typedContract = contract as ActionContractLoose;
      const viewOrder = typedContract.views?.tree?.order || typedContract.ui_contract?.views?.tree?.order;
      const metaOrder = (meta as ActionMetaLoose | undefined)?.order;
      const order = scene.value?.default_sort || viewOrder || metaOrder;
      if (typeof order === 'string' && order.trim()) {
        sortValue.value = order;
      } else {
        sortValue.value = 'id asc';
      }
    }
    const policy = evaluateCapabilityPolicy({ source: meta, available: session.capabilities });
    if (policy.state !== 'enabled') {
      await router.replace({
        name: 'workbench',
        query: {
          menu_id: menuId.value || undefined,
          action_id: actionId.value || undefined,
          reason: ErrorCodes.CAPABILITY_MISSING,
          missing: policy.missing.join(','),
        },
      });
      return;
    }
    const contractModel = resolveModelFromContract(contract);
    const resolvedModel = meta?.model ?? model.value ?? contractModel;
    if (meta && !meta.model && resolvedModel) {
      session.setActionMeta({ ...meta, model: resolvedModel });
    }
    if (!resolvedModel) {
      if (isClientAction(meta)) {
        await router.replace({
          name: 'workbench',
          query: {
            menu_id: menuId.value || undefined,
            action_id: actionId.value || undefined,
            reason: ErrorCodes.ACT_NO_MODEL,
          },
        });
        return;
      }
      if (!isWindowAction(meta)) {
        const actionType = getActionType(meta);
        const typedContract = contract as ActionContractLoose;
        const contractType = String(typedContract.data?.type || '').toLowerCase();
        const contractUrl = String(typedContract.data?.url || '');
        const metaUrl = String((meta as ActionMetaLoose | undefined)?.url || '');
        await router.replace({
          name: 'workbench',
          query: {
            menu_id: menuId.value || undefined,
            action_id: actionId.value || undefined,
            reason: ErrorCodes.ACT_UNSUPPORTED_TYPE,
            diag: 'non_window_action',
            diag_action_type: actionType || undefined,
            diag_contract_type: contractType || undefined,
            diag_contract_url: contractUrl || undefined,
            diag_meta_url: metaUrl || undefined,
          },
        });
        return;
      }
      setError(new Error('Action has no model'), 'Action has no model');
      status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
      return;
    }
    const contractColumns = extractColumnsFromContract(contract);
    const kanbanContractFields = extractKanbanFields(contract);
    kanbanFields.value = kanbanContractFields;
    hasActiveField.value = Boolean(contract.ui_contract_raw?.fields?.active);
    hasAssigneeField.value = Boolean(contract.ui_contract_raw?.fields?.user_id);
    await loadAssigneeOptions();
    const requestedFields =
      viewMode.value === 'kanban'
        ? kanbanContractFields
        : resolveRequestedFields(contractColumns, listProfile.value);
    const result = await listRecordsRaw({
      model: resolvedModel,
      fields: requestedFields.length ? requestedFields : ['id', 'name'],
      domain: mergeActiveFilter(mergeSceneDomain(meta?.domain, scene.value?.filters)),
      context: mergeContext(meta?.context),
      limit: 40,
      offset: 0,
      search_term: searchTerm.value.trim() || undefined,
      order: sortLabel.value,
    });
    records.value = result.data?.records ?? [];
    const currentIds = new Set(
      records.value
        .map((row) => {
          const id = row.id;
          if (typeof id === 'number') return id;
          if (typeof id === 'string' && id.trim()) {
            const parsed = Number(id);
            return Number.isNaN(parsed) ? null : parsed;
          }
          return null;
        })
        .filter((id): id is number => typeof id === 'number'),
    );
    selectedIds.value = selectedIds.value.filter((id) => currentIds.has(id));
    columns.value = contractColumns.length ? contractColumns : pickColumns(records.value);
    status.value = deriveListStatus({ error: '', recordsLength: records.value.length });
    if (result.meta?.trace_id) {
      traceId.value = String(result.meta.trace_id);
      lastTraceId.value = String(result.meta.trace_id);
    } else if (result.traceId) {
      traceId.value = String(result.traceId);
      lastTraceId.value = String(result.traceId);
    }
    lastLatencyMs.value = Date.now() - startedAt;
  } catch (err) {
    setError(err, 'failed to load list');
    traceId.value = error.value?.traceId || '';
    lastTraceId.value = error.value?.traceId || '';
    status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
    lastLatencyMs.value = Date.now() - startedAt;
  }
}

function handleRowClick(row: Record<string, unknown>) {
  const id = row.id;
  if (!model.value) {
    return;
  }
  if (typeof id === 'number') {
    router.push({
      path: `/r/${model.value}/${id}`,
      query: { menu_id: menuId.value || undefined, action_id: actionId.value || undefined, ...resolveWorkspaceContextQuery() },
    });
  } else if (typeof id === 'string' && id) {
    router.push({
      path: `/r/${model.value}/${id}`,
      query: { menu_id: menuId.value || undefined, action_id: actionId.value || undefined, ...resolveWorkspaceContextQuery() },
    });
  }
}

function reload() {
  load();
}

function handleSearch(value: string) {
  searchTerm.value = value;
  load();
}

function handleSort(value: string) {
  sortValue.value = value;
  load();
}

function handleFilter(value: 'all' | 'active' | 'archived') {
  filterValue.value = value;
  clearSelection();
  load();
}

function clearSelection() {
  selectedIds.value = [];
}

function handleAssigneeChange(assigneeId: number | null) {
  selectedAssigneeId.value = assigneeId;
}

function handleToggleSelection(id: number, selected: boolean) {
  const set = new Set(selectedIds.value);
  if (selected) {
    set.add(id);
  } else {
    set.delete(id);
  }
  selectedIds.value = Array.from(set);
}

function handleToggleSelectionAll(ids: number[], selected: boolean) {
  if (!ids.length) return;
  const set = new Set(selectedIds.value);
  ids.forEach((id) => {
    if (selected) {
      set.add(id);
    } else {
      set.delete(id);
    }
  });
  selectedIds.value = Array.from(set);
}

function buildIfMatchMap(ids: number[]) {
  const wanted = new Set(ids);
  const map: Record<number, string> = {};
  records.value.forEach((row) => {
    const rawId = row.id;
    const id =
      typeof rawId === 'number'
        ? rawId
        : typeof rawId === 'string' && rawId.trim()
          ? Number(rawId)
          : NaN;
    if (!Number.isFinite(id) || !wanted.has(id)) return;
    const writeDate = String((row.write_date as string | undefined) || '').trim();
    if (writeDate) {
      map[id] = writeDate;
    }
  });
  return map;
}

function buildIdempotencyKey(action: string, ids: number[], extra: Record<string, unknown> = {}) {
  const payload = {
    model: model.value || '',
    action,
    ids: [...ids].sort((a, b) => a - b),
    extra,
  };
  return `batch:${JSON.stringify(payload)}`;
}

async function handleBatchAction(action: 'archive' | 'activate') {
  batchMessage.value = '';
  batchDetails.value = [];
  failedCsvFileName.value = '';
  failedCsvContentB64.value = '';
  batchFailedOffset.value = 0;
  batchHasMoreFailures.value = false;
  lastBatchRequest.value = null;
  if (!model.value || !selectedIds.value.length) return;
  if (!hasActiveField.value) {
    batchMessage.value = '当前模型不支持 active 字段，无法批量归档/激活';
    return;
  }
  batchBusy.value = true;
  try {
    const ifMatchMap = buildIfMatchMap(selectedIds.value);
    const idempotencyKey = buildIdempotencyKey(action, selectedIds.value, { active: action === 'activate' });
    const requestContext = mergeContext(actionMeta.value?.context);
    const result = await batchUpdateRecords({
      model: model.value,
      ids: selectedIds.value,
      action,
      ifMatchMap,
      idempotencyKey,
      failedPreviewLimit: 12,
      failedOffset: 0,
      failedLimit: 12,
      exportFailedCsv: true,
      context: requestContext,
    });
    lastBatchRequest.value = {
      model: model.value,
      ids: [...selectedIds.value],
      action,
      ifMatchMap,
      idempotencyKey,
      context: requestContext,
    };
    if (result.idempotent_replay) {
      batchMessage.value = '批量操作已幂等处理（重复请求被忽略）';
    } else {
    batchMessage.value =
      action === 'activate'
        ? `批量激活完成：成功 ${result.succeeded}，失败 ${result.failed}`
        : `批量归档完成：成功 ${result.succeeded}，失败 ${result.failed}`;
    }
    applyBatchFailureArtifacts(result);
    clearSelection();
    await load();
  } catch (err) {
    setError(err, 'batch operation failed');
    batchMessage.value = action === 'activate' ? '批量激活失败' : '批量归档失败';
    batchDetails.value = [];
    failedCsvFileName.value = '';
    failedCsvContentB64.value = '';
    batchFailedOffset.value = 0;
    batchHasMoreFailures.value = false;
    lastBatchRequest.value = null;
  } finally {
    batchBusy.value = false;
  }
}

async function handleBatchAssign(assigneeId: number) {
  batchMessage.value = '';
  batchDetails.value = [];
  failedCsvFileName.value = '';
  failedCsvContentB64.value = '';
  batchFailedOffset.value = 0;
  batchHasMoreFailures.value = false;
  lastBatchRequest.value = null;
  if (!model.value || !selectedIds.value.length) return;
  if (!hasAssigneeField.value) {
    batchMessage.value = '当前模型不支持负责人字段，无法批量指派';
    return;
  }
  if (!assigneeId) {
    batchMessage.value = '请先选择负责人';
    return;
  }
  batchBusy.value = true;
  try {
    const ifMatchMap = buildIfMatchMap(selectedIds.value);
    const idempotencyKey = buildIdempotencyKey('assign', selectedIds.value, { assignee_id: assigneeId });
    const requestContext = mergeContext(actionMeta.value?.context);
    const result = await batchUpdateRecords({
      model: model.value,
      ids: selectedIds.value,
      action: 'assign',
      assigneeId,
      ifMatchMap,
      idempotencyKey,
      failedPreviewLimit: 12,
      failedOffset: 0,
      failedLimit: 12,
      exportFailedCsv: true,
      context: requestContext,
    });
    lastBatchRequest.value = {
      model: model.value,
      ids: [...selectedIds.value],
      action: 'assign',
      assigneeId,
      ifMatchMap,
      idempotencyKey,
      context: requestContext,
    };
    const assignee = assigneeOptions.value.find((opt) => opt.id === assigneeId)?.name || `#${assigneeId}`;
    if (result.idempotent_replay) {
      batchMessage.value = `批量指派给 ${assignee} 已幂等处理（重复请求被忽略）`;
    } else {
      batchMessage.value = `批量指派给 ${assignee}：成功 ${result.succeeded}，失败 ${result.failed}`;
    }
    applyBatchFailureArtifacts(result);
    clearSelection();
    await load();
  } catch (err) {
    setError(err, 'batch assign failed');
    batchMessage.value = '批量指派失败';
    batchDetails.value = [];
    failedCsvFileName.value = '';
    failedCsvContentB64.value = '';
    batchFailedOffset.value = 0;
    batchHasMoreFailures.value = false;
    lastBatchRequest.value = null;
  } finally {
    batchBusy.value = false;
  }
}

function handleBatchExport(scope: 'selected' | 'all') {
  void exportByBackend(scope);
}

async function exportByBackend(scope: 'selected' | 'all') {
  batchMessage.value = '';
  batchDetails.value = [];
  failedCsvFileName.value = '';
  failedCsvContentB64.value = '';
  if (!model.value) return;
  if (scope === 'selected' && !selectedIds.value.length) {
    batchMessage.value = '没有可导出的选中记录';
    return;
  }
  batchBusy.value = true;
  try {
    const ids = scope === 'selected' ? selectedIds.value : [];
    const domain = scope === 'all' ? mergeActiveFilter(mergeSceneDomain(actionMeta.value?.domain, scene.value?.filters)) : [];
    const fields = columns.value.length ? ['id', ...columns.value.filter((col) => col !== 'id')] : ['id', 'name'];
    const result = await exportRecordsCsv({
      model: model.value,
      fields,
      ids,
      domain,
      order: sortLabel.value,
      limit: scope === 'all' ? 10000 : 5000,
      context: mergeContext(actionMeta.value?.context),
    });
    if (!result.content_b64) {
      batchMessage.value = '没有可导出的记录';
      return;
    }
    downloadCsvBase64(result.file_name, result.mime_type, result.content_b64);
    batchMessage.value = `已导出 ${result.count} 条记录`;
  } catch (err) {
    setError(err, 'batch export failed');
    batchMessage.value = '批量导出失败';
  } finally {
    batchBusy.value = false;
  }
}

function handleDownloadFailedCsv() {
  if (!failedCsvContentB64.value) return;
  downloadCsvBase64(failedCsvFileName.value || 'batch_failed.csv', 'text/csv', failedCsvContentB64.value);
}

async function handleLoadMoreFailures() {
  if (!lastBatchRequest.value || !batchHasMoreFailures.value) return;
  batchBusy.value = true;
  try {
    const req = lastBatchRequest.value;
    const result = await batchUpdateRecords({
      model: req.model,
      ids: req.ids,
      action: req.action,
      assigneeId: req.assigneeId,
      ifMatchMap: req.ifMatchMap,
      idempotencyKey: req.idempotencyKey,
      failedPreviewLimit: batchFailedLimit.value,
      failedOffset: batchFailedOffset.value,
      failedLimit: batchFailedLimit.value,
      exportFailedCsv: false,
      context: req.context,
    });
    applyBatchFailureArtifacts(result, { append: true });
  } catch (err) {
    setError(err, 'load more failures failed');
  } finally {
    batchBusy.value = false;
  }
}

onMounted(async () => {
  applyRoutePreset();
  await load();
});

watch(
  () => route.fullPath,
  () => {
    if (applyRoutePreset()) {
      void load();
    }
  },
);
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}

.route-preset {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  background: #eff6ff;
}

.route-preset p {
  margin: 0;
  color: #1e3a8a;
  font-size: 13px;
}

.clear-btn {
  border: 1px solid #93c5fd;
  border-radius: 8px;
  background: #fff;
  color: #1d4ed8;
  padding: 4px 8px;
  cursor: pointer;
}
</style>
