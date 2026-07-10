import { defineStore } from 'pinia';
import type { AppInitResponse, LoginResponse, NavMeta, NavNode, ProjectContextContract, ProjectContextOption } from '@sc/schema';
import { intentRequest } from '../api/intents';
import { ApiError } from '../api/client';
import { config } from '../config';
import { getSceneByKey, setSceneRegistry, setSceneRegistryFromSceneReadyContract } from '../app/resolvers/sceneRegistry';
import type { Scene } from '../app/resolvers/sceneRegistry';
import { normalizeLegacyWorkbenchPath } from '../app/routeQuery';
import { applySceneValidationRecoveryStrategyRuntime, setSceneValidationRecoveryStrategy } from '../app/sceneValidationRecoveryStrategy';
import { isConfiguredDbPinned, resolveActiveDb, resolveConfiguredDb, resolveLoginRoutingDb, setActiveDb } from '../services/dbContext';

let appInitInFlight: Promise<void> | null = null;

function resolveAvailableSceneRoute(rawPath: string): string {
  const normalized = normalizeLegacyWorkbenchPath(String(rawPath || '').trim());
  if (!normalized) return '';
  const match = normalized.match(/^\/s\/([^/?#]+)/);
  if (!match) return normalized;
  const sceneKey = decodeURIComponent(match[1] || '').trim();
  return sceneKey && getSceneByKey(sceneKey) ? normalized : '';
}

function resolveAvailableSceneKeyRoute(sceneKey: string): string {
  const key = String(sceneKey || '').trim();
  if (!key) return '';
  const scene = getSceneByKey(key);
  if (!scene) return '';
  const rawPath = String(scene.target?.route || scene.route || `/s/${key}`).trim();
  return resolveAvailableSceneRoute(rawPath) || `/s/${key}`;
}

export interface RoleSurface {
  role_code: string;
  role_label: string;
  landing_scene_key: string;
  landing_menu_id?: number | null;
  landing_menu_xmlid?: string;
  landing_path?: string;
  scene_candidates: string[];
  menu_xmlids: string[];
}

export type RoleSurfaceMap = Record<string, {
  role_code?: string;
  role_label?: string;
  scene_candidates?: string[];
  menu_xmlids?: string[];
}>;

export interface CapabilityGroup {
  key: string;
  label: string;
  icon: string;
  sequence: number;
  capability_count: number;
  state_counts: Record<string, number>;
  capability_state_counts: Record<string, number>;
}

export interface CapabilityRuntimeMeta {
  key: string;
  label: string;
  state: string;
  capability_state: string;
  reason: string;
  reason_code: string;
  group_key: string;
  group_label: string;
}

export interface SceneActionHint {
  actionId: number;
  menuId?: number;
}

export interface ProductFacts {
  license: {
    level: string;
    tiers: string[];
    customer_visible?: boolean;
    upgrade_hint?: string;
    reason_codes?: string[];
  } | null;
  bundle: {
    name: string;
    profile?: Record<string, unknown>;
    scenes: Array<Record<string, unknown>>;
    capabilities: Array<Record<string, unknown>>;
    recommended_roles: string[];
    default_dashboard: string;
  } | null;
}

export interface WorkspaceHomeContract {
  schema_version?: string;
  semantic_protocol?: {
    block_types?: string[];
    state_tones?: string[];
    progress_states?: string[];
  };
  layout?: {
    sections?: Array<{ key?: string; enabled?: boolean; order?: number; tag?: string; open?: boolean }>;
    texts?: Record<string, unknown>;
    actions?: Record<string, unknown>;
  };
  page_orchestration?: {
    schema_version?: string;
    page?: {
      key?: string;
      intent?: string;
      role_code?: string;
      render_mode?: string;
    };
    zones?: Array<{ key?: string; label?: string; order?: number }>;
    blocks?: Array<{
      key?: string;
      type?: string;
      zone?: string;
      order?: number;
      source_path?: string;
      visible?: boolean;
      tone?: string;
      progress?: string;
      focus?: boolean;
    }>;
    role_layout?: {
      mode?: string;
      variant?: string;
      focus_blocks?: string[];
    };
  };
  page_orchestration_v1?: {
    contract_version?: string;
    scene_key?: string;
    page?: Record<string, unknown>;
    zones?: Array<Record<string, unknown>>;
    data_sources?: Record<string, unknown>;
    state_schema?: Record<string, unknown>;
    action_schema?: Record<string, unknown>;
    render_hints?: Record<string, unknown>;
    meta?: Record<string, unknown>;
  };
  scene_contract_v1?: {
    contract_version?: string;
    scene?: Record<string, unknown>;
    page?: Record<string, unknown>;
    nav_ref?: Record<string, unknown>;
    zones?: Array<Record<string, unknown>>;
    blocks?: Record<string, Record<string, unknown>>;
    actions?: Record<string, unknown>;
    permissions?: Record<string, unknown>;
    record?: Record<string, unknown>;
    extensions?: Record<string, unknown>;
    diagnostics?: Record<string, unknown>;
  };
  role_variant?: {
    role_code?: string;
    mode?: string;
    focus?: string[];
  };
  hero?: Record<string, unknown>;
  metrics?: unknown[];
  today_actions?: unknown[];
  risk?: Record<string, unknown>;
  ops?: Record<string, unknown>;
  scene_groups?: unknown[];
  group_overview?: unknown[];
  advice?: unknown[];
}

export interface WorkspaceHeroRow {
  key: string;
  label: string;
  value: string;
}

export interface WorkspaceAdviceRow {
  id: string;
  level: 'red' | 'amber' | 'green';
  title: string;
  description: string;
  actionLabel: string;
  actionEntryId: string;
  actionPath: string;
  actionQuery: Record<string, string>;
}

export interface WorkspaceMetricRow {
  key: string;
  label: string;
  value: string;
  delta: string;
  hint: string;
  tone: string;
  progress: string;
}

export interface WorkspaceTodayActionRow {
  id: string;
  title: string;
  description: string;
  count: number;
  status: string;
  tone: string;
  source: string;
  actionLabel: string;
  actionKey: string;
  entryId: string;
  sceneKey: string;
  route: string;
}

export interface WorkspaceRiskAlertRow {
  id: string;
  title: string;
  description: string;
  tone: string;
  source: string;
  actionLabel: string;
  actionKey: string;
  sceneKey: string;
  path: string;
  query: Record<string, string>;
  entryKey: string;
  entryId: string;
}

export interface WorkspaceOpsSummary {
  bars: Record<string, unknown>;
  kpi: Record<string, unknown>;
  summary: string;
}

export interface WorkspaceSceneEntryRow {
  id: string;
  key: string;
  title: string;
  actionLabel: string;
  subtitle: string;
  sceneKey: string;
  sceneLabel: string;
  sequence: number;
  status: string;
  state: string;
  capabilityState: string;
  groupKey: string;
  groupLabel: string;
  reason: string;
  reasonCode: string;
  route: string;
  targetActionId: number;
  targetMenuId: number;
  targetModel: string;
  targetRecordId: string;
  contextQuery: Record<string, string>;
  sceneTags: string[];
  tileTags: string[];
}

export interface WorkspaceCapabilityGroupRow {
  key: string;
  label: string;
  sequence: number;
  capabilityCount: number;
  allowCount: number;
  readonlyCount: number;
  denyCount: number;
  readyCount: number;
  score: number;
  examples: Array<{
    key: string;
    label: string;
    state: string;
    capabilityState: string;
  }>;
}

export interface ActivityProjectContextSnapshot {
  selected: ProjectContextOption | null;
  company_id: number | null;
  company_name: string;
  operation_strategy: string;
  operation_strategy_label: string;
}

export type ActivityRuntimeQuery = Record<string, string | string[]>;

export interface ActivityPage {
  key: string;
  title: string;
  route: string;
  kind: 'menu_action' | 'record_form' | 'scene' | 'workspace' | 'custom';
  model?: string;
  action_id?: number;
  menu_id?: number;
  record_id?: string;
  scene_key?: string;
  project_scope_policy?: string;
  project_context?: ActivityProjectContextSnapshot | null;
  runtime_query?: ActivityRuntimeQuery;
  dirty?: boolean;
  created_at: number;
  last_active_at: number;
}

export interface PageContract {
  schema_version?: string;
  texts?: Record<string, unknown>;
  sections?: Array<{ key?: string; enabled?: boolean; order?: number; tag?: string; open?: boolean }>;
  page_orchestration_v1?: {
    contract_version?: string;
    scene_key?: string;
    page?: Record<string, unknown>;
    zones?: Array<Record<string, unknown>>;
    data_sources?: Record<string, unknown>;
    state_schema?: Record<string, unknown>;
    action_schema?: Record<string, unknown>;
    render_hints?: Record<string, unknown>;
    meta?: Record<string, unknown>;
  };
  scene_contract_v1?: {
    contract_version?: string;
    scene?: Record<string, unknown>;
    page?: Record<string, unknown>;
    nav_ref?: Record<string, unknown>;
    zones?: Array<Record<string, unknown>>;
    blocks?: Record<string, Record<string, unknown>>;
    actions?: Record<string, unknown>;
    permissions?: Record<string, unknown>;
    record?: Record<string, unknown>;
    extensions?: Record<string, unknown>;
    diagnostics?: Record<string, unknown>;
  };
  actions?: Record<string, unknown>;
}

export interface SceneReadyContract {
  contract_version?: string;
  schema_version?: string;
  scene_version?: string;
  source_schema_version?: string;
  scene_channel?: string;
  active_scene_key?: string;
  scenes?: Array<Record<string, unknown>>;
  meta?: Record<string, unknown>;
}

export interface SceneGovernancePayload {
  contract_version?: string;
  scene_channel?: string;
  scene_contract_ref?: string;
  runtime_source?: string;
  governance?: Record<string, unknown>;
  auto_degrade?: Record<string, unknown>;
  delivery_policy?: Record<string, unknown>;
  nav_policy?: Record<string, unknown>;
  role_surface_provider?: Record<string, unknown>;
  scene_ready_consumption?: Record<string, unknown>;
  diagnostics?: Record<string, unknown>;
  gates?: Record<string, unknown>;
  reasons?: Record<string, unknown>;
}

export interface SessionState {
  token: string | null;
  sessionDb: string;
  user: AppInitResponse['user'] | null;
  menuTree: NavNode[];
  menuExpandedKeys: string[];
  currentAction: NavMeta | null;
  capabilities: string[];
  scenes: Scene[];
  sceneVersion: string | null;
  roleSurface: RoleSurface | null;
  roleSurfaceMap: RoleSurfaceMap;
  projectContext: ProjectContextContract | null;
  activityPages: ActivityPage[];
  activeActivityPageKey: string;
  activityPageCacheEpochs: Record<string, number>;
  capabilityCatalog: Record<string, CapabilityRuntimeMeta>;
  sceneActionHints: Record<string, SceneActionHint>;
  capabilityGroups: CapabilityGroup[];
  productFacts: ProductFacts;
  workspaceHome: WorkspaceHomeContract | null;
  workspaceHomeRef: {
    intent?: string;
    scene_key?: string;
    loaded?: boolean;
  } | null;
  pageContracts: Record<string, PageContract>;
  sceneReadyContractV1: SceneReadyContract | null;
  sceneGovernanceV1: SceneGovernancePayload | null;
  lastTraceId: string;
  lastIntent: string;
  lastLatencyMs: number | null;
  lastWriteMode: string;
  isReady: boolean;
  initStatus: 'idle' | 'loading' | 'ready' | 'error';
  initError: string | null;
  initTraceId: string | null;
  initMeta: AppInitResponse['meta'] | null;
  defaultRoute: {
    scene_key?: string;
    route?: string;
    reason?: string;
    menu_id?: number;
  } | null;
  bootstrapNextIntent: string;
}

const TOKEN_STORAGE_KEY_LEGACY = 'sc_auth_token';
const MAX_ACTIVITY_PAGES = 6;
const TRANSIENT_ACTIVITY_ROUTE_QUERY_KEYS = new Set([
  't',
  'search',
  'q',
  'order',
  'sort',
  'filter',
  'active_filter',
  'saved_filter',
  'group_by',
  'group_value',
  'group_sample_limit',
  'group_sort',
  'group_collapsed',
  'group_page',
  'group_offset',
  'group_fp',
  'group_window_id',
  'group_window_digest',
  'group_window_identity_key',
  'group_wid',
  'group_wdg',
  'group_wik',
  'offset',
  'limit',
]);

const ACTIVITY_RUNTIME_QUERY_KEYS = new Set([
  'search',
  'q',
  'active_filter',
  'saved_filter',
  'group_by',
  'group_value',
  'group_sample_limit',
  'group_sort',
  'group_collapsed',
  'group_page',
  'group_offset',
  'group_fp',
  'group_wid',
  'group_wdg',
  'group_wik',
]);

function currentDbScope(): string {
  return String(resolveActiveDb('') || resolveConfiguredDb(String(config.odooDb || '').trim()) || config.odooDb || 'default').trim() || 'default';
}

function sessionStorageKey(): string {
  return `sc_frontend_session_v0_6:${currentDbScope()}`;
}

function scopedTokenStorageKey(): string {
  return `sc_auth_token:${currentDbScope()}`;
}

function resolveUserCompanyId(user: unknown): number | null {
  if (!user || typeof user !== 'object') return null;
  const row = user as Record<string, unknown>;
  const direct = Number(row.company_id || 0);
  if (Number.isFinite(direct) && direct > 0) return direct;
  const company = row.company;
  if (company && typeof company === 'object') {
    const nested = Number((company as Record<string, unknown>).id || 0);
    if (Number.isFinite(nested) && nested > 0) return nested;
  }
  return null;
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : String(value ?? '').trim();
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function normalizeContextQuery(raw: unknown): Record<string, string> {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return {};
  return Object.entries(raw as Record<string, unknown>).reduce<Record<string, string>>((acc, [key, value]) => {
    const text = asText(value);
    if (text) acc[key] = text;
    return acc;
  }, {});
}

function asObjectList(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value)
    ? value.map((item) => asRecord(item)).filter((item) => Object.keys(item).length > 0)
    : [];
}

function normalizeProjectOption(raw: unknown): ProjectContextOption | null {
  const row = asRecord(raw);
  const id = Number(row.id || 0);
  if (!Number.isFinite(id) || id <= 0) return null;
  return {
    id,
    name: asText(row.name),
    display_name: asText(row.display_name) || asText(row.name),
    code: asText(row.code),
    company_id: Number(row.company_id || 0) || undefined,
    company_name: asText(row.company_name),
    stage: asText(row.stage),
    owner_id: Number(row.owner_id || 0) || undefined,
    owner_name: asText(row.owner_name),
    operation_strategy: asText(row.operation_strategy),
    operation_strategy_label: asText(row.operation_strategy_label),
    active: row.active === undefined ? undefined : Boolean(row.active),
  };
}

function normalizeCompanyOptions(raw: unknown) {
  return Array.isArray(raw)
    ? raw.map((item) => {
      const row = asRecord(item);
      const companyId = Number(row.company_id || 0);
      if (!Number.isFinite(companyId) || companyId <= 0) return null;
      return {
        company_id: companyId,
        company_name: asText(row.company_name),
        active: row.active === undefined ? undefined : Boolean(row.active),
      };
    }).filter(Boolean) as NonNullable<ProjectContextContract['company_options']>
    : [];
}

function normalizeOperationOptions(raw: unknown) {
  return Array.isArray(raw)
    ? raw.map((item) => {
      const row = asRecord(item);
      const strategy = asText(row.operation_strategy);
      return {
        operation_strategy: strategy,
        operation_strategy_label: asText(row.operation_strategy_label),
        active: row.active === undefined ? undefined : Boolean(row.active),
        disabled: row.disabled === undefined ? undefined : Boolean(row.disabled),
        disabled_reason: asText(row.disabled_reason),
      };
    }).filter(Boolean) as NonNullable<ProjectContextContract['operation_options']>
    : [];
}

function normalizeProjectContext(raw: unknown): ProjectContextContract | null {
  const row = asRecord(raw);
  if (!Object.keys(row).length) return null;
  const selector = asRecord(row.selector);
  const persistence = asRecord(row.persistence);
  const selected = normalizeProjectOption(row.selected);
  const options = Array.isArray(row.options)
    ? row.options.map((item) => normalizeProjectOption(item)).filter(Boolean) as ProjectContextOption[]
    : [];
  return {
    contract_version: asText(row.contract_version),
    enabled: Boolean(row.enabled),
    source: asText(row.source),
    model: asText(row.model),
    legacy_project_context: Boolean(row.legacy_project_context),
    company_id: Number(row.company_id || 0) || selected?.company_id || null,
    company_name: asText(row.company_name) || selected?.company_name || '',
    company_options: normalizeCompanyOptions(row.company_options),
    operation_strategy: asText(row.operation_strategy),
    operation_strategy_label: asText(row.operation_strategy_label),
    operation_options: normalizeOperationOptions(row.operation_options),
    selected,
    options,
    total: Number(row.total || 0),
    query: asText(row.query),
    reason_code: asText(row.reason_code),
    message: asText(row.message),
    selector: Object.keys(selector).length ? {
      intent: asText(selector.intent),
      search_param: asText(selector.search_param),
      selected_id_param: asText(selector.selected_id_param),
      limit: Number(selector.limit || 0) || undefined,
      label: asText(selector.label),
      placeholder: asText(selector.placeholder),
    } : undefined,
    persistence: Object.keys(persistence).length ? {
      scope: asText(persistence.scope),
      server_preference: Boolean(persistence.server_preference),
    } : undefined,
  };
}

function projectContextStorageSnapshot(raw: ProjectContextContract | null): ProjectContextContract | null {
  if (!raw) return null;
  return {
    ...raw,
    // Selector options are a live backend contract. Persisting them makes the
    // sidebar dropdown look stale after contract/schema upgrades.
    options: [],
    total: raw.selected ? 1 : 0,
    query: '',
  };
}

function normalizeActivityProjectContext(raw: unknown): ActivityProjectContextSnapshot | null {
  const row = asRecord(raw);
  if (!Object.keys(row).length) return null;
  return {
    selected: normalizeProjectOption(row.selected),
    company_id: Number(row.company_id || 0) || null,
    company_name: asText(row.company_name),
    operation_strategy: asText(row.operation_strategy),
    operation_strategy_label: asText(row.operation_strategy_label),
  };
}

function normalizeActivityRuntimeQuery(raw: unknown): ActivityRuntimeQuery | undefined {
  const source = asRecord(raw);
  const next: ActivityRuntimeQuery = {};
  Object.entries(source).forEach(([key, value]) => {
    if (!ACTIVITY_RUNTIME_QUERY_KEYS.has(key)) return;
    if (Array.isArray(value)) {
      const values = value.map((item) => asText(item)).filter(Boolean);
      if (values.length) next[key] = values;
      return;
    }
    const text = asText(value);
    if (text) next[key] = text;
  });
  return Object.keys(next).length ? next : undefined;
}

function stripTransientActivityRouteQuery(rawRoute: unknown): string {
  const source = asText(rawRoute);
  if (!source || !source.includes('?')) return source;
  const [pathWithMaybeHash, queryWithMaybeHash = ''] = source.split('?', 2);
  const [queryText, hashText = ''] = queryWithMaybeHash.split('#', 2);
  const params = new URLSearchParams(queryText);
  TRANSIENT_ACTIVITY_ROUTE_QUERY_KEYS.forEach((key) => params.delete(key));
  const nextQuery = params.toString();
  const hash = hashText ? `#${hashText}` : '';
  return `${pathWithMaybeHash}${nextQuery ? `?${nextQuery}` : ''}${hash}`;
}

function isDeprecatedMergedExpenseDepositActivity(row: ActivityPage): boolean {
  const title = asText(row.title);
  if (title === '费用/保证金申请') return true;
  const route = asText(row.route);
  if (!route.includes('integration_target')) return false;
  try {
    const queryText = route.split('?', 2)[1]?.split('#', 1)[0] || '';
    const target = asText(new URLSearchParams(queryText).get('integration_target'));
    return target === 'sc.expense.claim 费用/保证金申请';
  } catch {
    return route.includes('sc.expense.claim+%E8%B4%B9%E7%94%A8/%E4%BF%9D%E8%AF%81%E9%87%91%E7%94%B3%E8%AF%B7')
      || route.includes('sc.expense.claim%20%E8%B4%B9%E7%94%A8%2F%E4%BF%9D%E8%AF%81%E9%87%91%E7%94%B3%E8%AF%B7');
  }
}

function isDeprecatedMergedContractHandlingActivity(row: ActivityPage): boolean {
  const title = asText(row.title);
  const model = asText(row.model);
  const route = asText(row.route);
  if (title === '合同办理' && model === 'construction.contract') return true;
  if (route.includes('/a/1002') && (title === '合同办理' || model === 'construction.contract')) return true;
  if (!route.includes('integration_target')) return false;
  try {
    const queryText = route.split('?', 2)[1]?.split('#', 1)[0] || '';
    const target = asText(new URLSearchParams(queryText).get('integration_target'));
    return target === 'construction.contract 合同办理';
  } catch {
    return route.includes('construction.contract+%E5%90%88%E5%90%8C%E5%8A%9E%E7%90%86')
      || route.includes('construction.contract%20%E5%90%88%E5%90%8C%E5%8A%9E%E7%90%86');
  }
}

function isDeprecatedMergedContractSettlementActivity(row: ActivityPage): boolean {
  const title = asText(row.title);
  const model = asText(row.model);
  const route = asText(row.route);
  if (title === '结算办理' && model === 'sc.settlement.order') return true;
  if (!route.includes('integration_target')) return false;
  try {
    const queryText = route.split('?', 2)[1]?.split('#', 1)[0] || '';
    const target = asText(new URLSearchParams(queryText).get('integration_target'));
    return target === 'sc.settlement.order 结算办理';
  } catch {
    return route.includes('sc.settlement.order+%E7%BB%93%E7%AE%97%E5%8A%9E%E7%90%86')
      || route.includes('sc.settlement.order%20%E7%BB%93%E7%AE%97%E5%8A%9E%E7%90%86');
  }
}

function normalizeActivityPage(raw: unknown): ActivityPage | null {
  const row = asRecord(raw);
  const key = asText(row.key);
  const route = stripTransientActivityRouteQuery(row.route);
  if (!key || !route) return null;
  const kindText = asText(row.kind);
  const kind = ['menu_action', 'record_form', 'scene', 'workspace', 'custom'].includes(kindText)
    ? kindText as ActivityPage['kind']
    : 'custom';
  const createdAt = Number(row.created_at || row.createdAt || 0) || Date.now();
  const lastActiveAt = Number(row.last_active_at || row.lastActiveAt || 0) || createdAt;
  return {
    key,
    route,
    kind,
    title: asText(row.title) || '活动页面',
    model: asText(row.model) || undefined,
    action_id: Number(row.action_id || row.actionId || 0) || undefined,
    menu_id: Number(row.menu_id || row.menuId || 0) || undefined,
    record_id: asText(row.record_id || row.recordId) || undefined,
    scene_key: asText(row.scene_key || row.sceneKey) || undefined,
    project_scope_policy: asText(row.project_scope_policy || row.projectScopePolicy) || undefined,
    project_context: normalizeActivityProjectContext(row.project_context || row.projectContext),
    runtime_query: normalizeActivityRuntimeQuery(row.runtime_query || row.runtimeQuery),
    dirty: Boolean(row.dirty),
    created_at: createdAt,
    last_active_at: lastActiveAt,
  };
}

function trimActivityPages(pages: ActivityPage[], activeKey: string): ActivityPage[] {
  if (pages.length <= MAX_ACTIVITY_PAGES) return pages;
  const keep = [...pages];
  while (keep.length > MAX_ACTIVITY_PAGES) {
    const removable = keep
      .filter((page) => page.key !== activeKey && !page.dirty)
      .sort((a, b) => a.last_active_at - b.last_active_at)[0];
    if (!removable) break;
    const index = keep.findIndex((page) => page.key === removable.key);
    if (index >= 0) keep.splice(index, 1);
    else break;
  }
  return keep;
}

function isRetainedActivityPage(page: ActivityPage | null): page is ActivityPage {
  if (!page) return false;
  if (isDeprecatedMergedExpenseDepositActivity(page)) return false;
  if (isDeprecatedMergedContractHandlingActivity(page)) return false;
  if (isDeprecatedMergedContractSettlementActivity(page)) return false;
  const key = asText(page.key).toLowerCase();
  const route = asText(page.route).split(/[?#]/, 1)[0];
  const pageRecord = page as unknown as Record<string, unknown>;
  const sceneKey = asText(page.scene_key || pageRecord.sceneKey).toLowerCase();
  if (key === 'workspace:home') return false;
  if (sceneKey === 'workspace.home') return false;
  if (route === '/' || route === '/s/workspace.home') return false;
  return true;
}

function activityPageCacheRouteKey(key: string): string {
  const normalized = asText(key);
  if (!normalized) return '';
  const parts = normalized.split(':');
  if (parts[0] === 'action' && parts.length >= 4) return parts.slice(0, 4).join(':');
  if (parts[0] === 'scene' && parts.length >= 2) return parts.slice(0, 2).join(':');
  return normalized;
}

function invalidateRestoredActivityPageCaches(
  pages: ActivityPage[],
  currentEpochs: Record<string, number> | undefined,
): Record<string, number> {
  const next = { ...(currentEpochs || {}) };
  pages.forEach((page) => {
    const keys = [asText(page.key), activityPageCacheRouteKey(page.key)].filter(Boolean);
    keys.forEach((key) => {
      next[key] = Number(next[key] || 0) + 1;
    });
  });
  return next;
}

function isGenericActivityTitle(title: string): boolean {
  const text = asText(title);
  if (!text) return true;
  return /^(动作\s*\d+|业务动作|业务表单|新建业务表单|活动页面)$/.test(text);
}

export const useSessionStore = defineStore('session', {
  state: (): SessionState => ({
    token: null,
    sessionDb: '',
    user: null,
    menuTree: [],
    menuExpandedKeys: [],
    currentAction: null,
    capabilities: [],
    scenes: [],
    sceneVersion: null,
    roleSurface: null,
    roleSurfaceMap: {},
    projectContext: null,
    activityPages: [],
    activeActivityPageKey: '',
    activityPageCacheEpochs: {},
    capabilityCatalog: {},
    sceneActionHints: {},
    capabilityGroups: [],
    productFacts: {
      license: null,
      bundle: null,
    },
    workspaceHome: null,
    workspaceHomeRef: null,
    pageContracts: {},
    sceneReadyContractV1: null,
    sceneGovernanceV1: null,
    lastTraceId: '',
    lastIntent: '',
    lastLatencyMs: null,
    lastWriteMode: '',
    isReady: false,
    initStatus: 'idle',
    initError: null,
    initTraceId: null,
    initMeta: null,
    defaultRoute: null,
    bootstrapNextIntent: 'system.init',
  }),
  getters: {
    workspaceHeroRows(state): WorkspaceHeroRow[] {
      const hero = asRecord(state.workspaceHome?.hero);
      const source = Array.isArray(hero.summary_rows) ? hero.summary_rows : [];
      return source
        .map((item, index) => {
          const row = asRecord(item);
          return {
            key: asText(row.key) || `hero-${index + 1}`,
            label: asText(row.label),
            value: asText(row.value),
          };
        })
        .filter((row) => row.label && row.value);
    },
    workspaceAdviceRows(state): WorkspaceAdviceRow[] {
      const source = Array.isArray(state.workspaceHome?.advice) ? state.workspaceHome?.advice : [];
      return source.map((item, index) => {
        const row = asRecord(item);
        const levelRaw = asText(row.level).toLowerCase();
        const level: 'red' | 'amber' | 'green' = levelRaw === 'red' || levelRaw === 'amber' ? levelRaw : 'green';
        return {
          id: asText(row.id) || `advice-${index + 1}`,
          level,
          title: asText(row.title) || `建议 ${index + 1}`,
          description: asText(row.description),
          actionLabel: asText(row.action_label),
          actionEntryId: asText(row.entry_id),
          actionPath: asText(row.path),
          actionQuery: normalizeContextQuery(row.query),
        };
      });
    },
    workspaceMetricRows(state): WorkspaceMetricRow[] {
      const source = Array.isArray(state.workspaceHome?.metrics) ? state.workspaceHome?.metrics : [];
      return source.map((item, index) => {
        const row = asRecord(item);
        return {
          key: asText(row.key) || `metric-${index + 1}`,
          label: asText(row.label) || `指标 ${index + 1}`,
          value: asText(row.value) || '0',
          delta: asText(row.delta),
          hint: asText(row.hint),
          tone: asText(row.tone).toLowerCase() || 'neutral',
          progress: asText(row.progress).toLowerCase() || 'running',
        };
      });
    },
    workspaceTodayActionRows(state): WorkspaceTodayActionRow[] {
      const source = Array.isArray(state.workspaceHome?.today_actions) ? state.workspaceHome?.today_actions : [];
      return source.map((item, index) => {
        const row = asRecord(item);
        return {
          id: asText(row.id) || `todo-${index + 1}`,
          title: asText(row.title) || `待办 ${index + 1}`,
          description: asText(row.description),
          count: Number(row.count || row.pending_count || 0),
          status: asText(row.status).toLowerCase() || 'normal',
          tone: asText(row.tone).toLowerCase() || 'warning',
          source: asText(row.source) || 'business',
          actionLabel: asText(row.action_label),
          actionKey: asText(row.action_key) || 'open_scene',
          entryId: asText(row.entry_id),
          sceneKey: asText(row.scene_key),
          route: asText(row.route),
        };
      });
    },
    workspaceRiskAlertRows(state): WorkspaceRiskAlertRow[] {
      const risk = asRecord(state.workspaceHome?.risk);
      const source = asObjectList(risk.actions);
      return source.map((item, index) => ({
        id: asText(item.id) || `risk-${index + 1}`,
        title: asText(item.title) || `风险事项 ${index + 1}`,
        description: asText(item.description),
        tone: asText(item.tone).toLowerCase() || 'danger',
        source: asText(item.source) || 'business',
        actionLabel: asText(item.action_label),
        actionKey: asText(item.action_key) || 'open_scene',
        sceneKey: asText(item.scene_key),
        path: asText(item.path),
        query: normalizeContextQuery(item.query),
        entryKey: asText(item.entry_key),
        entryId: asText(item.entry_id),
      }));
    },
    workspaceOpsSummary(state): WorkspaceOpsSummary {
      const ops = asRecord(state.workspaceHome?.ops);
      return {
        bars: asRecord(ops.bars),
        kpi: asRecord(ops.kpi),
        summary: asText(ops.summary),
      };
    },
    workspaceSceneEntryRows(state): WorkspaceSceneEntryRow[] {
      const source = Array.isArray(state.workspaceHome?.scene_groups) ? state.workspaceHome?.scene_groups : [];
      if (source.length) {
        return source.map((item, index) => {
          const row = asRecord(item);
          return {
            id: asText(row.id) || `scene-group-${index + 1}`,
            key: asText(row.key),
            title: asText(row.title) || `功能 ${index + 1}`,
            actionLabel: asText(row.action_label),
            subtitle: asText(row.subtitle),
            sceneKey: asText(row.scene_key),
            sceneLabel: asText(row.scene_label) || asText(row.scene_key),
            sequence: Number(row.sequence ?? 9999),
            status: asText(row.status).toLowerCase() || 'ga',
            state: asText(row.state).toUpperCase(),
            capabilityState: asText(row.capability_state).toLowerCase(),
            groupKey: asText(row.group_key),
            groupLabel: asText(row.group_label),
            reason: asText(row.reason),
            reasonCode: asText(row.reason_code),
            route: asText(row.route),
            targetActionId: Number(row.action_id || 0),
            targetMenuId: Number(row.menu_id || 0),
            targetModel: asText(row.model),
            targetRecordId: asText(row.record_id),
            contextQuery: normalizeContextQuery(row.query),
            sceneTags: Array.isArray(row.scene_tags) ? (row.scene_tags as unknown[]).map((item) => asText(item).toLowerCase()).filter(Boolean) : [],
            tileTags: Array.isArray(row.tile_tags) ? (row.tile_tags as unknown[]).map((item) => asText(item).toLowerCase()).filter(Boolean) : [],
          };
        });
      }
      const list: WorkspaceSceneEntryRow[] = [];
      const capabilityCatalog = state.capabilityCatalog || {};
      state.scenes.forEach((scene, sceneIndex) => {
        const sceneKey = asText(scene.key);
        if (!sceneKey) return;
        const sceneLabel = asText(scene.label) || sceneKey;
        const sceneTags = Array.isArray((scene as unknown as Record<string, unknown>).tags)
          ? ((scene as unknown as Record<string, unknown>).tags as unknown[]).map((item) => asText(item).toLowerCase()).filter(Boolean)
          : [];
        const tiles = Array.isArray(scene.tiles) ? scene.tiles : [];
        tiles.forEach((tile, tileIndex) => {
          const tileRow = asRecord(tile);
          const key = asText(tileRow.key);
          if (!key) return;
          const capabilityMeta = capabilityCatalog[key];
          const payload = asRecord(tileRow.payload);
          const title = asText(tileRow.title) || asText(capabilityMeta?.label) || `功能 ${sceneIndex + 1}-${tileIndex + 1}`;
          list.push({
            id: `${sceneKey}-${key}-${sceneIndex}-${tileIndex}`,
            key,
            title,
            actionLabel: asText(tileRow.action_label) || asText(payload.action_label),
            subtitle: asText(tileRow.subtitle),
            sceneKey,
            sceneLabel,
            sequence: Number(tileRow.sequence ?? 9999),
            status: asText(tileRow.status).toLowerCase() || 'ga',
            state: asText(tileRow.state).toUpperCase(),
            capabilityState: asText(capabilityMeta?.capability_state).toLowerCase(),
            groupKey: asText(capabilityMeta?.group_key),
            groupLabel: asText(capabilityMeta?.group_label),
            reason: asText(tileRow.reason) || asText(capabilityMeta?.reason),
            reasonCode: asText(tileRow.reason_code) || asText(capabilityMeta?.reason_code),
            route: asText(tileRow.route),
            targetActionId: Number(payload.action_id || 0),
            targetMenuId: Number(payload.menu_id || 0),
            targetModel: asText(payload.model),
            targetRecordId: asText(payload.record_id),
            contextQuery: normalizeContextQuery(payload.context_query || payload.query || payload.context),
            sceneTags,
            tileTags: Array.isArray(tileRow.tags) ? (tileRow.tags as unknown[]).map((item) => asText(item).toLowerCase()).filter(Boolean) : [],
          });
        });
      });
      return list;
    },
    workspaceCapabilityGroupRows(state): WorkspaceCapabilityGroupRow[] {
      const source = Array.isArray(state.workspaceHome?.group_overview) ? state.workspaceHome?.group_overview : [];
      if (source.length) {
        return source.map((item) => {
          const row = asRecord(item);
          return {
            key: asText(row.key),
            label: asText(row.label) || asText(row.key),
            sequence: Number(row.sequence || 0),
            capabilityCount: Number(row.capability_count || 0),
            allowCount: Number(row.allow_count || 0),
            readonlyCount: Number(row.readonly_count || 0),
            denyCount: Number(row.deny_count || 0),
            readyCount: Number(row.ready_count || 0),
            score: Number(row.score || 0),
            examples: asObjectList(row.examples).map((example) => ({
              key: asText(example.key),
              label: asText(example.label) || asText(example.key),
              state: asText(example.state).toUpperCase(),
              capabilityState: asText(example.capability_state).toLowerCase(),
            })).filter((example) => example.label.length > 0),
          };
        });
      }
      return state.capabilityGroups.map((group) => {
        const readyCount = Number(group.state_counts?.READY || 0);
        const allowCount = Number(group.capability_state_counts?.allow || 0);
        return {
          key: group.key,
          label: group.label || group.key,
          sequence: Number(group.sequence || 0),
          capabilityCount: Number(group.capability_count || 0),
          allowCount,
          readonlyCount: Number(group.capability_state_counts?.readonly || 0),
          denyCount: Number(group.capability_state_counts?.deny || 0),
          readyCount,
          score: readyCount * 2 + allowCount,
          examples: [],
        };
      });
    },
  },
  actions: {
    setToken(token: string) {
      this.token = token;
      sessionStorage.setItem(scopedTokenStorageKey(), token);
      // Do not keep cross-db legacy token once db-scoped token is set.
      sessionStorage.removeItem(TOKEN_STORAGE_KEY_LEGACY);
    },
    restore() {
      this.isReady = false;
      this.initStatus = 'idle';
      this.initError = null;
      this.initTraceId = null;
      const cached = localStorage.getItem(sessionStorageKey());
      if (cached) {
        try {
          const parsed = JSON.parse(cached) as Partial<SessionState>;
          this.user = parsed.user ?? null;
          this.sessionDb = asText(parsed.sessionDb);
          // Navigation is a live backend contract. Do not hydrate it from
          // localStorage, otherwise menu/model changes can look stale until a
          // manual cache clear.
          this.menuTree = [];
          this.menuExpandedKeys = parsed.menuExpandedKeys ?? [];
          this.currentAction = parsed.currentAction ?? null;
          this.capabilities = parsed.capabilities ?? [];
          this.scenes = parsed.scenes ?? [];
          this.sceneVersion = parsed.sceneVersion ?? null;
          this.roleSurface = parsed.roleSurface ?? null;
          this.roleSurfaceMap = parsed.roleSurfaceMap ?? {};
          this.projectContext = projectContextStorageSnapshot(normalizeProjectContext(parsed.projectContext));
          this.activityPages = Array.isArray(parsed.activityPages)
            ? parsed.activityPages.map((item) => normalizeActivityPage(item)).filter(isRetainedActivityPage)
            : [];
          const restoredActiveKey = asText(parsed.activeActivityPageKey);
          this.activeActivityPageKey = this.activityPages.some((page) => page.key === restoredActiveKey)
            ? restoredActiveKey
            : '';
          this.activityPageCacheEpochs = invalidateRestoredActivityPageCaches(
            this.activityPages,
            parsed.activityPageCacheEpochs,
          );
          this.capabilityCatalog = parsed.capabilityCatalog ?? {};
          this.sceneActionHints = parsed.sceneActionHints ?? {};
          this.capabilityGroups = parsed.capabilityGroups ?? [];
          this.productFacts = parsed.productFacts ?? { license: null, bundle: null };
          this.workspaceHome = parsed.workspaceHome ?? null;
          this.workspaceHomeRef = parsed.workspaceHomeRef ?? null;
          this.pageContracts = {};
          this.sceneReadyContractV1 = parsed.sceneReadyContractV1 ?? null;
          this.sceneGovernanceV1 = parsed.sceneGovernanceV1 ?? null;
          if (this.sceneReadyContractV1?.scenes?.length) {
            setSceneRegistryFromSceneReadyContract(this.sceneReadyContractV1);
          } else if (this.scenes.length) {
            setSceneRegistry(this.scenes);
          }
          this.lastTraceId = parsed.lastTraceId ?? '';
          this.lastIntent = parsed.lastIntent ?? '';
          this.lastLatencyMs = parsed.lastLatencyMs ?? null;
          this.lastWriteMode = parsed.lastWriteMode ?? '';
          this.initMeta = parsed.initMeta ?? null;
          this.defaultRoute = parsed.defaultRoute ?? null;
          this.bootstrapNextIntent = String(parsed.bootstrapNextIntent || 'system.init').trim() || 'system.init';
        } catch {
          // ignore corrupted cache
        }
      }
      const token = sessionStorage.getItem(scopedTokenStorageKey());
      if (token) {
        this.token = token;
      }
      // Always purge legacy unscoped token to avoid cross-db pollution.
      sessionStorage.removeItem(TOKEN_STORAGE_KEY_LEGACY);
    },
    clearSession() {
      this.token = null;
      this.sessionDb = '';
      this.user = null;
      this.menuTree = [];
      this.menuExpandedKeys = [];
      this.currentAction = null;
      this.capabilities = [];
      this.scenes = [];
      this.sceneVersion = null;
      this.roleSurface = null;
      this.roleSurfaceMap = {};
      this.projectContext = null;
      this.activityPages = [];
      this.activeActivityPageKey = '';
      this.activityPageCacheEpochs = {};
      this.capabilityCatalog = {};
      this.sceneActionHints = {};
      this.capabilityGroups = [];
      this.productFacts = { license: null, bundle: null };
      this.workspaceHome = null;
      this.workspaceHomeRef = null;
      this.pageContracts = {};
      this.sceneReadyContractV1 = null;
      this.sceneGovernanceV1 = null;
      setSceneRegistry([]);
      this.lastTraceId = '';
      this.lastIntent = '';
      this.lastLatencyMs = null;
      this.lastWriteMode = '';
      this.defaultRoute = null;
      this.bootstrapNextIntent = 'system.init';
      this.isReady = false;
      localStorage.removeItem(sessionStorageKey());
      sessionStorage.removeItem(scopedTokenStorageKey());
      sessionStorage.removeItem(TOKEN_STORAGE_KEY_LEGACY);
    },
    setActionMeta(meta: NavMeta) {
      this.currentAction = meta;
      this.persist();
    },
    toggleMenuExpanded(key: string) {
      const set = new Set(this.menuExpandedKeys);
      if (set.has(key)) {
        set.delete(key);
      } else {
        set.add(key);
      }
      this.menuExpandedKeys = [...set];
      this.persist();
    },
    ensureMenuExpanded(keys: string[]) {
      const set = new Set(this.menuExpandedKeys);
      let changed = false;
      keys.forEach((key) => {
        if (!set.has(key)) {
          set.add(key);
          changed = true;
        }
      });
      if (changed) {
        this.menuExpandedKeys = [...set];
        this.persist();
      }
    },
    persist() {
      const snapshot: Partial<SessionState> = {
        sessionDb: this.sessionDb,
        user: this.user,
        menuTree: this.menuTree,
        menuExpandedKeys: this.menuExpandedKeys,
        currentAction: this.currentAction,
        capabilities: this.capabilities,
        scenes: this.scenes,
        sceneVersion: this.sceneVersion,
        roleSurface: this.roleSurface,
        roleSurfaceMap: this.roleSurfaceMap,
        projectContext: projectContextStorageSnapshot(this.projectContext),
        activityPages: this.activityPages,
        activeActivityPageKey: this.activeActivityPageKey,
        activityPageCacheEpochs: this.activityPageCacheEpochs,
        capabilityCatalog: this.capabilityCatalog,
        sceneActionHints: this.sceneActionHints,
        capabilityGroups: this.capabilityGroups,
        productFacts: this.productFacts,
        workspaceHome: this.workspaceHome,
        workspaceHomeRef: this.workspaceHomeRef,
        sceneReadyContractV1: this.sceneReadyContractV1,
        sceneGovernanceV1: this.sceneGovernanceV1,
        lastTraceId: this.lastTraceId,
        lastIntent: this.lastIntent,
        lastLatencyMs: this.lastLatencyMs,
        lastWriteMode: this.lastWriteMode,
        initMeta: this.initMeta,
        defaultRoute: this.defaultRoute,
        bootstrapNextIntent: this.bootstrapNextIntent,
      };
      try {
        localStorage.setItem(sessionStorageKey(), JSON.stringify(snapshot));
        return;
      } catch {
        // Persistence is only a reload optimization. A quota or serialization
        // failure must not block login or user initialization.
      }
      try {
        const minimalSnapshot: Partial<SessionState> = {
          sessionDb: this.sessionDb,
          user: this.user,
          menuExpandedKeys: this.menuExpandedKeys,
          currentAction: this.currentAction,
          roleSurface: this.roleSurface,
          projectContext: this.projectContext,
          activityPages: this.activityPages,
          activeActivityPageKey: this.activeActivityPageKey,
          activityPageCacheEpochs: this.activityPageCacheEpochs,
          workspaceHomeRef: this.workspaceHomeRef,
          lastTraceId: this.lastTraceId,
          lastIntent: this.lastIntent,
          lastLatencyMs: this.lastLatencyMs,
          lastWriteMode: this.lastWriteMode,
          initMeta: this.initMeta,
          defaultRoute: this.defaultRoute,
          bootstrapNextIntent: this.bootstrapNextIntent,
        };
        localStorage.setItem(sessionStorageKey(), JSON.stringify(minimalSnapshot));
      } catch {
        localStorage.removeItem(sessionStorageKey());
      }
    },
    currentActivityProjectContextSnapshot(): ActivityProjectContextSnapshot | null {
      const current = this.projectContext;
      if (!current) return null;
      return {
        selected: current.selected ?? null,
        company_id: Number(current.company_id || current.selected?.company_id || 0) || null,
        company_name: asText(current.company_name || current.selected?.company_name),
        operation_strategy: asText(current.operation_strategy || current.selected?.operation_strategy),
        operation_strategy_label: asText(current.operation_strategy_label || current.selected?.operation_strategy_label),
      };
    },
    registerActivityPage(rawPage: Omit<ActivityPage, 'created_at' | 'last_active_at'> & Partial<Pick<ActivityPage, 'created_at' | 'last_active_at'>>) {
      const now = Date.now();
      const key = asText(rawPage.key);
      const route = asText(rawPage.route);
      if (!key || !route) return;
      const existing = this.activityPages.find((page) => page.key === key);
      const incomingTitle = asText(rawPage.title) || '活动页面';
      const title = existing?.title && !isGenericActivityTitle(existing.title) && isGenericActivityTitle(incomingTitle)
        ? existing.title
        : incomingTitle;
      const nextPage: ActivityPage = {
        key,
        route,
        title,
        kind: rawPage.kind,
        model: asText(rawPage.model) || undefined,
        action_id: Number(rawPage.action_id || 0) || undefined,
        menu_id: Number(rawPage.menu_id || 0) || undefined,
        record_id: asText(rawPage.record_id) || undefined,
        scene_key: asText(rawPage.scene_key) || undefined,
        project_scope_policy: asText(rawPage.project_scope_policy) || undefined,
        project_context: rawPage.project_context ?? this.currentActivityProjectContextSnapshot(),
        runtime_query: existing?.runtime_query,
        dirty: Boolean(rawPage.dirty || existing?.dirty),
        created_at: existing?.created_at || Number(rawPage.created_at || 0) || now,
        last_active_at: now,
      };
      if (!isRetainedActivityPage(nextPage)) return;
      const others = this.activityPages.filter((page) => page.key !== key);
      this.activeActivityPageKey = key;
      this.activityPages = trimActivityPages([...others, nextPage], key)
        .sort((a, b) => a.created_at - b.created_at);
      this.persist();
    },
    closeActivityPage(key: string): ActivityPage | null {
      const normalizedKey = asText(key);
      if (!normalizedKey) return null;
      const closingActive = this.activeActivityPageKey === normalizedKey;
      this.activityPages = this.activityPages.filter((page) => page.key !== normalizedKey);
      const cacheRouteKey = activityPageCacheRouteKey(normalizedKey);
      this.activityPageCacheEpochs = {
        ...this.activityPageCacheEpochs,
        [normalizedKey]: Number(this.activityPageCacheEpochs[normalizedKey] || 0) + 1,
        ...(cacheRouteKey ? {
          [cacheRouteKey]: Number(this.activityPageCacheEpochs[cacheRouteKey] || 0) + 1,
        } : {}),
      };
      let nextPage: ActivityPage | null = null;
      if (closingActive) {
        nextPage = [...this.activityPages].sort((a, b) => b.last_active_at - a.last_active_at)[0] || null;
        this.activeActivityPageKey = nextPage?.key || '';
      }
      this.persist();
      return nextPage;
    },
    markActivityPageActive(key: string) {
      const normalizedKey = asText(key);
      if (!normalizedKey) return;
      const now = Date.now();
      this.activityPages = this.activityPages.map((page) => (
        page.key === normalizedKey ? { ...page, last_active_at: now } : page
      ));
      this.activeActivityPageKey = normalizedKey;
      this.persist();
    },
    updateActiveActivityRuntimeQuery(rawQuery: unknown) {
      const activeKey = asText(this.activeActivityPageKey);
      if (!activeKey) return;
      const runtimeQuery = normalizeActivityRuntimeQuery(rawQuery);
      let changed = false;
      this.activityPages = this.activityPages.map((page) => {
        if (page.key !== activeKey) return page;
        const current = JSON.stringify(page.runtime_query || {});
        const next = JSON.stringify(runtimeQuery || {});
        if (current === next) return page;
        changed = true;
        return {
          ...page,
          runtime_query: runtimeQuery,
        };
      });
      if (changed) this.persist();
    },
    updateActiveActivityTitle(rawTitle: unknown) {
      const activeKey = asText(this.activeActivityPageKey);
      const title = asText(rawTitle);
      if (!activeKey || !title) return;
      const activePage = this.activityPages.find((page) => page.key === activeKey);
      const titleBelongsToAnotherPage = this.activityPages.some((page) => page.key !== activeKey && page.title === title);
      if (
        activePage?.title
        && activePage.title !== title
        && !isGenericActivityTitle(activePage.title)
        && !isGenericActivityTitle(title)
        && titleBelongsToAnotherPage
      ) {
        return;
      }
      let changed = false;
      this.activityPages = this.activityPages.map((page) => {
        if (page.key !== activeKey || page.title === title) return page;
        changed = true;
        return { ...page, title };
      });
      if (changed) this.persist();
    },
    async applyActivityProjectContext(snapshot: ActivityProjectContextSnapshot | null | undefined) {
      if (!snapshot || !this.projectContext) return;
      const currentSelectedId = Number(this.projectContext.selected?.id || 0) || 0;
      const nextSelectedId = Number(snapshot.selected?.id || 0) || 0;
      const currentCompanyId = Number(this.projectContext.company_id || this.projectContext.selected?.company_id || 0) || 0;
      const nextCompanyId = Number(snapshot.company_id || snapshot.selected?.company_id || 0) || 0;
      const currentOperation = asText(this.projectContext.operation_strategy || this.projectContext.selected?.operation_strategy);
      const nextOperation = asText(snapshot.operation_strategy || snapshot.selected?.operation_strategy);
      if (
        currentSelectedId === nextSelectedId
        && currentCompanyId === nextCompanyId
        && currentOperation === nextOperation
      ) {
        return;
      }
      this.projectContext = {
        ...this.projectContext,
        selected: snapshot.selected ?? null,
        company_id: nextCompanyId || null,
        company_name: asText(snapshot.company_name || snapshot.selected?.company_name),
        operation_strategy: nextOperation,
        operation_strategy_label: asText(snapshot.operation_strategy_label || snapshot.selected?.operation_strategy_label),
      };
      this.persist();
      await this.loadAppInit();
    },
    recordIntentTrace(params: { traceId?: string; intent: string; latencyMs?: number | null; writeMode?: string }) {
      if (params.traceId) {
        this.lastTraceId = params.traceId;
      }
      this.lastIntent = params.intent;
      this.lastLatencyMs = params.latencyMs ?? null;
      this.lastWriteMode = params.writeMode ?? '';
      this.persist();
    },
    async login(username: string, password: string, dbOverride?: string) {
      const loginRoutingDb = resolveLoginRoutingDb();
      const configuredDb = resolveConfiguredDb(String(config.odooDb || '').trim());
      const db = String(loginRoutingDb ? '' : isConfiguredDbPinned() ? configuredDb : dbOverride || configuredDb).trim();
      if (db) {
        setActiveDb(db, true);
      }
      const result = await intentRequest<LoginResponse>({
        intent: 'login',
        params: { login: username, password, contract_mode: 'default', ...(db ? { db } : {}) },
      });
      const token = String(result.session?.token || result.token || '').trim();
      if (!token) {
        throw new Error('login response missing token');
      }
      const nextIntent = String(result.bootstrap?.next_intent || 'system.init').trim();
      const allowedBootstrapIntents = new Set(['system.init', 'session.bootstrap']);
      if (!allowedBootstrapIntents.has(nextIntent)) {
        throw new Error(`login bootstrap next_intent unsupported: ${nextIntent}`);
      }
      this.bootstrapNextIntent = nextIntent;
      const sessionDb = String(result.session?.db || (result as LoginResponse & { login_route?: { target_db?: string } }).login_route?.target_db || db || '').trim();
      this.sessionDb = sessionDb;
      if (sessionDb) {
        setActiveDb(sessionDb, true);
      }
      this.setToken(token);
    },
    async logout() {
      try {
        await intentRequest<{ message?: string }>({ intent: 'auth.logout' });
      } catch {
        // ignore logout failure
      }
      this.clearSession();
    },
    async loadAppInit(options: { force?: boolean } = {}) {
      if (appInitInFlight && !options.force) {
        return appInitInFlight;
      }
      if (appInitInFlight && options.force) {
        try {
          await appInitInFlight;
        } catch {
          // A forced refresh must fetch the latest runtime state even if the
          // previous bootstrap request failed.
        }
      }
      const run = (async () => {
      this.initStatus = 'loading';
      this.initError = null;
      this.initTraceId = null;
      const bootstrapIntent = String(this.bootstrapNextIntent || 'system.init').trim();
      if (bootstrapIntent === 'session.bootstrap') {
        await intentRequest({ intent: 'session.bootstrap', params: {} });
      }
      if (bootstrapIntent !== 'system.init' && bootstrapIntent !== 'session.bootstrap') {
        throw new Error(`unsupported bootstrap intent: ${bootstrapIntent}`);
      }
      const currentUrl = new URL(window.location.href);
      const currentSceneKey = String(
        currentUrl.searchParams.get('scene_key')
        || currentUrl.searchParams.get('sceneKey')
        || '',
      ).trim();
      const debugIntent = import.meta.env.DEV;

      // A1: 打印本次 system.init 的有效参数
      if (debugIntent) {
        console.group('[A1] system.init 请求诊断');
        console.log('1. API Base URL:', import.meta.env.VITE_API_BASE_URL);
        console.log('2. Authorization 存在:', !!this.token);
        console.log('3. X-Odoo-DB 环境变量:', import.meta.env.VITE_ODOO_DB);
      }

      const requestParams = {
        intent: 'system.init',
        params: {
          scene: 'web',
          with_preload: false,
          scene_ready_mode: 'registry',
          with: ['workspace_home'],
          ...(config.startupRootXmlid ? { root_xmlid: config.startupRootXmlid } : {}),
          ...(currentSceneKey ? { scene_key: currentSceneKey } : {}),
          ...(this.projectContext?.company_id ? { company_id: this.projectContext.company_id } : {}),
          ...(this.projectContext?.operation_strategy ? { operation_strategy: this.projectContext.operation_strategy } : {}),
          ...(this.projectContext?.selected?.id ? { current_project_id: this.projectContext.selected.id } : {}),
        },
      };
      if (debugIntent) {
        console.log('4. Request params:', JSON.stringify(requestParams, null, 2));
        console.groupEnd();
      }

      let result: AppInitResponse;
      try {
        result = await intentRequest<AppInitResponse>(requestParams);
      } catch (err) {
        if (err instanceof ApiError) {
          this.initError = err.message;
          this.initTraceId = err.traceId ?? null;
        } else {
          this.initError = err instanceof Error ? err.message : 'init failed';
        }
        this.initStatus = 'error';
        throw err;
      }
      // A1: 打印响应诊断信息
      if (debugIntent) {
        console.group('[A1] system.init 响应诊断');
        console.log('1. Response keys:', Object.keys(result));

        // 检查 meta 字段
        if (result.meta) {
          console.log('2. Meta 字段:', result.meta);
          console.log('   effective_db:', result.meta.effective_db);
          console.log('   effective_root_xmlid:', result.meta.effective_root_xmlid);
        } else {
          console.log('2. Meta 字段: 不存在');
        }

        // 检查 nav 字段
        if (result.nav) {
          console.log('3. Nav 字段存在，类型:', typeof result.nav, '是否为数组:', Array.isArray(result.nav));
          if (Array.isArray(result.nav) && result.nav.length > 0) {
            console.log('   菜单数量:', result.nav.length);
            console.log('   前3个菜单:');
            result.nav.slice(0, 3).forEach((item, index) => {
              console.log(`     [${index}] name: "${item.name}", xmlid: "${item.xmlid || 'N/A'}", id: ${item.id || 'N/A'}`);
            });
          }
        } else {
          console.log('3. Nav 字段: 不存在');
        }
        console.groupEnd();
      }

      if (debugIntent) {
        // eslint-disable-next-line no-console
        console.info('[debug] system.init result', result);
      }
      this.user = result.user;
      const rawCapabilities = (result as AppInitResponse & { capabilities?: Array<string | { key?: string }> }).capabilities ?? [];
      this.capabilities = rawCapabilities
        .map((cap) => (typeof cap === 'string' ? cap : cap?.key || ''))
        .filter((cap) => typeof cap === 'string' && cap.length > 0);
      this.capabilityCatalog = rawCapabilities.reduce<Record<string, CapabilityRuntimeMeta>>((acc, item) => {
        if (!item || typeof item === 'string') {
          if (typeof item === 'string' && item.trim()) {
            const key = item.trim();
            acc[key] = {
              key,
              label: key,
              state: 'READY',
              capability_state: 'allow',
              reason: '',
              reason_code: '',
              group_key: '',
              group_label: '',
            };
          }
          return acc;
        }
        const key = String(item.key || '').trim();
        if (!key) return acc;
        acc[key] = {
          key,
          label: String(item.label || key),
          state: String(item.state || '').toUpperCase() || '',
          capability_state: String(item.capability_state || '').toLowerCase() || '',
          reason: String(item.reason || ''),
          reason_code: String(item.reason_code || ''),
          group_key: String(item.group_key || ''),
          group_label: String(item.group_label || ''),
        };
        return acc;
      }, {});
      this.sceneActionHints = rawCapabilities.reduce<Record<string, SceneActionHint>>((acc, item) => {
        if (!item || typeof item === 'string') {
          return acc;
        }
        const capability = item as Record<string, unknown>;
        const rawPayload = capability.default_payload;
        const payload = (rawPayload && typeof rawPayload === 'object')
          ? (rawPayload as Record<string, unknown>)
          : {};
        const actionId = Number(payload.action_id || 0);
        const menuId = Number(payload.menu_id || 0) || undefined;
        if (actionId <= 0) {
          return acc;
        }
        const payloadSceneKey = String(payload.scene_key || '').trim();
        const payloadRoute = String(payload.route || '').trim();
        let sceneKey = payloadSceneKey;
        if (!sceneKey && payloadRoute) {
          try {
            const routeUrl = new URL(payloadRoute, 'http://localhost');
            sceneKey = String(routeUrl.searchParams.get('scene') || '').trim();
          } catch {
            sceneKey = '';
          }
        }
        if (!sceneKey) {
          return acc;
        }
        if (!acc[sceneKey]) {
          acc[sceneKey] = { actionId, menuId };
        }
        return acc;
      }, {});
      this.scenes = ((result as AppInitResponse & { scenes?: Scene[] }).scenes ?? []).filter(Boolean);
      this.sceneVersion = (result as AppInitResponse & { scene_version?: string; sceneVersion?: string }).scene_version ?? (result as AppInitResponse & { scene_version?: string; sceneVersion?: string }).sceneVersion ?? null;
      const roleSurfaceRaw = (result as AppInitResponse & { role_surface?: Partial<RoleSurface> }).role_surface ?? {};
      this.roleSurface = {
        role_code: String(roleSurfaceRaw.role_code || ''),
        role_label: String(roleSurfaceRaw.role_label || roleSurfaceRaw.role_code || ''),
        landing_scene_key: String(roleSurfaceRaw.landing_scene_key || ''),
        landing_menu_id: typeof roleSurfaceRaw.landing_menu_id === 'number' ? roleSurfaceRaw.landing_menu_id : null,
        landing_menu_xmlid: String(roleSurfaceRaw.landing_menu_xmlid || ''),
        landing_path: String(roleSurfaceRaw.landing_path || ''),
        scene_candidates: Array.isArray(roleSurfaceRaw.scene_candidates) ? roleSurfaceRaw.scene_candidates.map((item) => String(item || '')).filter(Boolean) : [],
        menu_xmlids: Array.isArray(roleSurfaceRaw.menu_xmlids) ? roleSurfaceRaw.menu_xmlids.map((item) => String(item || '')).filter(Boolean) : [],
      };
      setSceneValidationRecoveryStrategy();
      const validationStrategyRaw = (result as AppInitResponse & { scene_validation_recovery_strategy?: unknown }).scene_validation_recovery_strategy;
      const extFactsRaw = (result as AppInitResponse & { ext_facts?: Record<string, unknown> }).ext_facts ?? {};
      const extValidationStrategyRaw = extFactsRaw.scene_validation_recovery_strategy;
      const validationStrategy = (validationStrategyRaw && typeof validationStrategyRaw === 'object' && !Array.isArray(validationStrategyRaw))
        ? validationStrategyRaw
        : ((extValidationStrategyRaw && typeof extValidationStrategyRaw === 'object' && !Array.isArray(extValidationStrategyRaw))
          ? extValidationStrategyRaw
          : undefined);
      applySceneValidationRecoveryStrategyRuntime(
        validationStrategy as Record<string, unknown> | undefined,
        {
          roleCode: this.roleSurface.role_code,
          companyId: resolveUserCompanyId(this.user),
        },
      );
      this.roleSurfaceMap = ((result as AppInitResponse & { role_surface_map?: RoleSurfaceMap }).role_surface_map ?? {});
      this.projectContext = normalizeProjectContext((result as AppInitResponse & { project_context?: ProjectContextContract }).project_context);
      const rawCapabilityGroups = (result as AppInitResponse & { capability_groups?: unknown[] }).capability_groups ?? [];
      this.capabilityGroups = rawCapabilityGroups
        .map((raw) => {
          const item = (raw && typeof raw === 'object') ? (raw as Record<string, unknown>) : {};
          const stateCounts = (item.state_counts && typeof item.state_counts === 'object')
            ? (item.state_counts as Record<string, number>)
            : {};
          const capabilityStateCounts = (item.capability_state_counts && typeof item.capability_state_counts === 'object')
            ? (item.capability_state_counts as Record<string, number>)
            : {};
          return {
            key: String(item.key || ''),
            label: String(item.label || item.key || ''),
            icon: String(item.icon || ''),
            sequence: Number(item.sequence || 0),
            capability_count: Number(item.capability_count || 0),
            state_counts: stateCounts,
            capability_state_counts: capabilityStateCounts,
          };
        })
        .filter((item) => item.key.length > 0);
      const extFacts = (result as AppInitResponse & { ext_facts?: Record<string, unknown> }).ext_facts ?? {};
      const productFacts = (extFacts.product && typeof extFacts.product === 'object')
        ? (extFacts.product as Record<string, unknown>)
        : {};
      const rawLicense = (productFacts.license && typeof productFacts.license === 'object')
        ? (productFacts.license as Record<string, unknown>)
        : {};
      const rawBundle = (productFacts.bundle && typeof productFacts.bundle === 'object')
        ? (productFacts.bundle as Record<string, unknown>)
        : {};
      this.productFacts = {
        license: Object.keys(rawLicense).length
          ? {
              level: String(rawLicense.level || ''),
              tiers: Array.isArray(rawLicense.tiers) ? rawLicense.tiers.map((item) => String(item || '')).filter(Boolean) : [],
              customer_visible: rawLicense.customer_visible !== false,
              upgrade_hint: String(rawLicense.upgrade_hint || ''),
              reason_codes: Array.isArray(rawLicense.reason_codes)
                ? rawLicense.reason_codes.map((item) => String(item || '')).filter(Boolean)
                : [],
            }
          : null,
        bundle: Object.keys(rawBundle).length
          ? {
              name: String(rawBundle.name || ''),
              profile: rawBundle.profile && typeof rawBundle.profile === 'object'
                ? rawBundle.profile as Record<string, unknown>
                : {},
              scenes: Array.isArray(rawBundle.scenes)
                ? rawBundle.scenes.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object' && !Array.isArray(item)))
                : [],
              capabilities: Array.isArray(rawBundle.capabilities)
                ? rawBundle.capabilities.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object' && !Array.isArray(item)))
                : [],
              recommended_roles: Array.isArray(rawBundle.recommended_roles)
                ? rawBundle.recommended_roles.map((item) => String(item || '')).filter(Boolean)
                : [],
              default_dashboard: String(rawBundle.default_dashboard || ''),
            }
          : null,
      };
      this.workspaceHome = ((result as AppInitResponse & { workspace_home?: WorkspaceHomeContract }).workspace_home ?? null);
      this.workspaceHomeRef = ((result as AppInitResponse & {
        workspace_home_ref?: { intent?: string; scene_key?: string; loaded?: boolean }
      }).workspace_home_ref ?? null);
      this.pageContracts = ((result as AppInitResponse & { page_contracts?: { pages?: Record<string, PageContract> } }).page_contracts?.pages ?? {});
      this.sceneReadyContractV1 = ((result as AppInitResponse & { scene_ready_contract_v1?: SceneReadyContract }).scene_ready_contract_v1 ?? null);
      this.sceneGovernanceV1 = ((result as AppInitResponse & { scene_governance_v1?: SceneGovernancePayload }).scene_governance_v1 ?? null);
      if (this.sceneReadyContractV1?.scenes?.length) {
        setSceneRegistryFromSceneReadyContract(this.sceneReadyContractV1);
      } else {
        setSceneRegistry(this.scenes);
      }
      this.initMeta = {
        ...(result.meta ?? {}),
        nav_meta: (result as AppInitResponse & { nav_meta?: unknown }).nav_meta ?? null,
      } as AppInitResponse['meta'];
      const defaultRouteRaw = (result as AppInitResponse & { default_route?: unknown }).default_route;
      if (defaultRouteRaw && typeof defaultRouteRaw === 'object') {
        const row = defaultRouteRaw as Record<string, unknown>;
        this.defaultRoute = {
          scene_key: String(row.scene_key || ''),
          route: String(row.route || ''),
          reason: String(row.reason || ''),
          menu_id: Number(row.menu_id || 0) || undefined,
        };
      } else {
        this.defaultRoute = null;
      }
      const hasWorkspaceHome = Boolean(this.workspaceHome && Object.keys(this.workspaceHome).length > 0);
      if (!hasWorkspaceHome && !this.defaultRoute) {
        this.defaultRoute = {
          scene_key: '',
          route: '/',
          reason: 'minimum_workspace_fallback',
          menu_id: undefined,
        };
      }
      const releaseNavigation = (result as AppInitResponse & {
        release_navigation_v1?: { nav?: unknown };
        delivery_engine_v1?: { nav?: unknown };
      }).release_navigation_v1;
      const deliveryEngine = (result as AppInitResponse & {
        release_navigation_v1?: { nav?: unknown };
        delivery_engine_v1?: { nav?: unknown };
      }).delivery_engine_v1;
      const candidates = [releaseNavigation?.nav, deliveryEngine?.nav, result.nav];
      if (debugIntent) {
        console.info('[debug] system.init candidates:', candidates.map(c => ({
          type: typeof c,
          isArray: Array.isArray(c),
          length: Array.isArray(c) ? c.length : 'N/A'
        })));
      }
      const nav = (candidates.find((entry) => Array.isArray(entry)) ?? null) as NavNode[] | null;
      if (!nav) {
        this.initError = 'system.init missing required nav contract';
        this.initStatus = 'error';
        throw new Error('system.init missing required nav contract');
      }
      if (debugIntent) {
        // eslint-disable-next-line no-console
        console.info('[debug] system.init nav length', nav.length);
        // 调试：打印第一个导航项的结构
        if (nav.length > 0) {
          console.info('[debug] First nav item:', JSON.stringify(nav[0], null, 2));
        }
      }
      // 为导航项添加 key 属性
      const menuTreeWithKeys = nav.map((item, index) => addKeys(item, index));
      this.menuTree = menuTreeWithKeys;
      this.menuExpandedKeys = filterExpandedKeys(this.menuTree, this.menuExpandedKeys);
      this.isReady = true;
      this.initStatus = 'ready';
      this.persist();
      })();
      appInitInFlight = run;
      try {
        await run;
      } finally {
        if (appInitInFlight === run) {
          appInitInFlight = null;
        }
      }
    },
    async loadWorkspaceHomeOnDemand(force = false) {
      if (!force && this.workspaceHome && Object.keys(this.workspaceHome).length > 0) {
        return this.workspaceHome;
      }
      if (!this.token) {
        return null;
      }
      const result = await intentRequest<AppInitResponse>({
        intent: 'system.init',
        params: {
          scene: 'web',
          with_preload: false,
          scene_ready_mode: 'registry',
          with: ['workspace_home'],
          ...(config.startupRootXmlid ? { root_xmlid: config.startupRootXmlid } : {}),
          ...(this.projectContext?.company_id ? { company_id: this.projectContext.company_id } : {}),
          ...(this.projectContext?.operation_strategy ? { operation_strategy: this.projectContext.operation_strategy } : {}),
          ...(this.projectContext?.selected?.id ? { current_project_id: this.projectContext.selected.id } : {}),
        },
      });
      const row = result as AppInitResponse & {
        workspace_home?: WorkspaceHomeContract;
        workspace_home_ref?: { intent?: string; scene_key?: string; loaded?: boolean };
        page_contracts?: { pages?: Record<string, PageContract> };
      };
      this.workspaceHome = row.workspace_home ?? this.workspaceHome;
      this.workspaceHomeRef = row.workspace_home_ref ?? this.workspaceHomeRef;
      if (row.page_contracts?.pages) {
        this.pageContracts = row.page_contracts.pages;
      }
      this.persist();
      return this.workspaceHome;
    },
    async searchProjectContext(search = '') {
      const selector = this.projectContext?.selector || {};
      const intent = String(selector.intent || 'project.context.search').trim();
      const result = await intentRequest<ProjectContextContract>({
        intent,
        params: {
          search,
          company_id: this.projectContext?.company_id || undefined,
          operation_strategy: this.projectContext?.operation_strategy || undefined,
          selected_id: this.projectContext?.selected?.id || undefined,
          limit: selector.limit || 20,
        },
      });
      const normalized = normalizeProjectContext(result);
      if (normalized) {
        this.projectContext = {
          ...normalized,
          selected: normalized.selected ?? this.projectContext?.selected ?? null,
        };
        this.persist();
      }
      return this.projectContext;
    },
    async selectProjectContext(option: ProjectContextOption | null) {
      const current = this.projectContext || {};
      this.projectContext = {
        ...current,
        selected: option,
        company_id: option?.company_id || current.company_id || null,
        company_name: option?.company_name || current.company_name || '',
        operation_strategy: option?.operation_strategy || current.operation_strategy || '',
        operation_strategy_label: option?.operation_strategy_label || current.operation_strategy_label || '',
      };
      this.persist();
      await this.loadAppInit();
    },
    async selectBusinessScope(scope: { company_id?: number | null; operation_strategy?: string }) {
      const current = this.projectContext || {};
      const nextCompanyId = Number(scope.company_id ?? current.company_id ?? 0) || null;
      const nextOperation = asText(scope.operation_strategy ?? current.operation_strategy);
      const selected = current.selected;
      const keepSelected = selected
        && (!nextCompanyId || !selected.company_id || selected.company_id === nextCompanyId)
        && (!nextOperation || !selected.operation_strategy || selected.operation_strategy === nextOperation);
      this.projectContext = {
        ...current,
        company_id: nextCompanyId,
        operation_strategy: nextOperation,
        operation_strategy_label: current.operation_options?.find((option) => option.operation_strategy === nextOperation)?.operation_strategy_label || '',
        selected: keepSelected ? selected : null,
      };
      this.persist();
      await this.searchProjectContext('');
      await this.loadAppInit();
    },
    async ensureReady() {
      if (this.isReady) {
        return;
      }
      await this.loadAppInit();
    },
    resolveLandingPath(fallback = '/') {
      const candidate = String(this.roleSurface?.landing_path || '').trim();
      if (candidate.startsWith('/')) {
        const normalized = resolveAvailableSceneRoute(candidate);
        if (normalized) return normalized;
      }
      const sceneKey = String(this.roleSurface?.landing_scene_key || '').trim();
      if (sceneKey) {
        const normalized = resolveAvailableSceneKeyRoute(sceneKey);
        if (normalized) return normalized;
      }
      const defaultRoutePath = String(this.defaultRoute?.route || '').trim();
      const defaultRouteSceneKey = String(this.defaultRoute?.scene_key || '').trim();
      const startsWithNativeActionRoute = /^\/(a|f|r)\//.test(defaultRoutePath);
      if (defaultRoutePath.startsWith('/') && !startsWithNativeActionRoute) {
        const normalized = resolveAvailableSceneRoute(defaultRoutePath);
        if (normalized) return normalized;
      }
      if (defaultRouteSceneKey) {
        const normalized = resolveAvailableSceneKeyRoute(defaultRouteSceneKey);
        if (normalized) return normalized;
      }
      return fallback;
    },
  },
});

function resolveSceneDisplayLabel(node: NavNode): string {
  const meta = (node.meta && typeof node.meta === 'object')
    ? node.meta as Record<string, unknown>
    : {};
  const sceneSource = String(meta.scene_source || '').trim().toLowerCase();
  const actionType = String(meta.action_type || '').trim().toLowerCase();
  if (sceneSource !== 'scene_contract' && actionType !== 'scene.contract') {
    return '';
  }
  const sceneKey = String(
    (node as NavNode & { scene_key?: string; sceneKey?: string }).scene_key
      || (node as NavNode & { scene_key?: string; sceneKey?: string }).sceneKey
      || node.meta?.scene_key
      || '',
  ).trim();
  if (!sceneKey) {
    return '';
  }
  const scene = getSceneByKey(sceneKey);
  return String(scene?.label || '').trim();
}

function addKeys(node: NavNode, index = 0): NavNode {
  const key = (node as NavNode & { xmlid?: string }).xmlid || node.key || `menu_${node.menu_id || node.id || index}`;
  const children = node.children?.map((child, idx) => addKeys(child, idx)) ?? [];
  const sceneLabel = resolveSceneDisplayLabel(node);
  if (!sceneLabel) {
    return { ...node, key, children };
  }
  return {
    ...node,
    key,
    title: sceneLabel,
    label: sceneLabel,
    children,
  };
}

function filterExpandedKeys(tree: NavNode[], keys: string[]): string[] {
  if (!keys.length || !tree.length) {
    return [];
  }
  const available = new Set<string>();
  const walk = (nodes: NavNode[]) => {
    nodes.forEach((node) => {
      if (node.key) {
        available.add(node.key);
      }
      if (node.children?.length) {
        walk(node.children);
      }
    });
  };
  walk(tree);
  return keys.filter((key) => available.has(key));
}
