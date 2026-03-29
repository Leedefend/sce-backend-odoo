import { defineStore } from 'pinia';
import type { AppInitResponse, LoginResponse, NavMeta, NavNode } from '@sc/schema';
import { intentRequest } from '../api/intents';
import { ApiError } from '../api/client';
import { config } from '../config';
import { getSceneByKey, setSceneRegistry, setSceneRegistryFromSceneReadyContract } from '../app/resolvers/sceneRegistry';
import type { Scene } from '../app/resolvers/sceneRegistry';
import { buildSceneRegistryFallbackPath, normalizeEditionKey, normalizeLegacyWorkbenchPath } from '../app/routeQuery';
import { applySceneValidationRecoveryStrategyRuntime, setSceneValidationRecoveryStrategy } from '../app/sceneValidationRecoveryStrategy';
import { resolveActiveDb, setActiveDb } from '../services/dbContext';
import { MY_WORK_PATH, normalizeProjectEntryContext, PROJECT_MANAGEMENT_PATH } from '../app/projectEntryContext';

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
  } | null;
  bundle: {
    name: string;
    scenes: string[];
    capabilities: string[];
    recommended_roles: string[];
    default_dashboard: string;
  } | null;
}

export interface EnterpriseEnablementStepTarget {
  action_id: number;
  menu_id: number;
  action_xmlid: string;
  menu_xmlid: string;
  route: string;
}

export interface EnterpriseEnablementStep {
  key: string;
  label: string;
  status: string;
  entry_xmlid: string;
  action_xmlid: string;
  next_hint: string;
  target: EnterpriseEnablementStepTarget | null;
}

export interface EnterpriseEnablementFacts {
  version: string;
  phase: string;
  theme: string;
  entry_root_xmlid: string;
  current_company_id: number;
  current_company_name: string;
  primary_action: EnterpriseEnablementStepTarget | null;
  steps: EnterpriseEnablementStep[];
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
    diagnostics?: SceneContractDiagnostics;
  };
  scene_contract_standard_v1?: Record<string, unknown>;
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
  advice?: unknown[];
}

export interface SceneConsumerRuntimeAlignment {
  runtime_state_present?: boolean;
  page_status_aligned?: boolean;
  record_state_summary_aligned?: boolean;
  current_state_projected?: boolean;
  consumer_runtime_present?: boolean;
  current_state_aligned?: boolean;
}

export interface SceneConsumerRuntime {
  page_status?: string;
  runtime_page_status?: string;
  current_state?: string;
  missing_required_count?: number;
  active_transition_count?: number;
  alignment?: SceneConsumerRuntimeAlignment;
  bridge_alignment?: SceneConsumerRuntimeAlignment;
}

export interface SceneContractDiagnostics {
  consumer_runtime?: SceneConsumerRuntime;
  consumer_runtime_assertions?: Record<string, unknown>;
  semantic_runtime_state?: Record<string, unknown>;
  semantic_runtime_assertions?: Record<string, unknown>;
  [key: string]: unknown;
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
    diagnostics?: SceneContractDiagnostics;
  };
  scene_contract_standard_v1?: Record<string, unknown>;
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
  user: AppInitResponse['user'] | null;
  menuTree: NavNode[];
  releaseNavigationTree: NavNode[];
  deliveryEngineV1: AppInitResponse['delivery_engine_v1'] | null;
  editionRuntimeV1: AppInitResponse['edition_runtime_v1'] | null;
  requestedEditionKey: string;
  effectiveEditionKey: string;
  menuExpandedKeys: string[];
  currentAction: NavMeta | null;
  capabilities: string[];
  scenes: Scene[];
  sceneVersion: string | null;
  roleSurface: RoleSurface | null;
  roleSurfaceMap: RoleSurfaceMap;
  capabilityCatalog: Record<string, CapabilityRuntimeMeta>;
  sceneActionHints: Record<string, SceneActionHint>;
  capabilityGroups: CapabilityGroup[];
  productFacts: ProductFacts;
  enterpriseEnablement: EnterpriseEnablementFacts | null;
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
  initRequestSeq: number;
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
  activeProjectContext: Record<string, unknown> | null;
}

const DB_SCOPE = String(config.odooDb || 'default').trim() || 'default';
const STORAGE_KEY = `sc_frontend_session_v0_4:${DB_SCOPE}`;
const TOKEN_STORAGE_KEY_LEGACY = 'sc_auth_token';
const TOKEN_STORAGE_KEY_SCOPED = `sc_auth_token:${DB_SCOPE}`;

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

function normalizeEnterpriseEnablementTarget(raw: unknown): EnterpriseEnablementStepTarget | null {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  const row = raw as Record<string, unknown>;
  return {
    action_id: Number(row.action_id || 0),
    menu_id: Number(row.menu_id || 0),
    action_xmlid: String(row.action_xmlid || ''),
    menu_xmlid: String(row.menu_xmlid || ''),
    route: String(row.route || ''),
  };
}

export const useSessionStore = defineStore('session', {
  state: (): SessionState => ({
    token: null,
    user: null,
    menuTree: [],
    releaseNavigationTree: [],
    deliveryEngineV1: null,
    editionRuntimeV1: null,
    requestedEditionKey: 'standard',
    effectiveEditionKey: 'standard',
    menuExpandedKeys: [],
    currentAction: null,
    capabilities: [],
    scenes: [],
    sceneVersion: null,
    roleSurface: null,
    roleSurfaceMap: {},
    capabilityCatalog: {},
    sceneActionHints: {},
    capabilityGroups: [],
    productFacts: {
      license: null,
      bundle: null,
    },
    enterpriseEnablement: null,
    workspaceHome: null,
    workspaceHomeRef: null,
    pageContracts: {},
    sceneReadyContractV1: null,
    sceneGovernanceV1: null,
    lastTraceId: '',
    lastIntent: '',
    lastLatencyMs: null,
    lastWriteMode: '',
    initRequestSeq: 0,
    isReady: false,
    initStatus: 'idle',
    initError: null,
    initTraceId: null,
    initMeta: null,
    defaultRoute: null,
  bootstrapNextIntent: 'system.init',
  activeProjectContext: null,
  }),
  actions: {
    setToken(token: string) {
      this.token = token;
      sessionStorage.setItem(TOKEN_STORAGE_KEY_SCOPED, token);
      // Do not keep cross-db legacy token once db-scoped token is set.
      sessionStorage.removeItem(TOKEN_STORAGE_KEY_LEGACY);
    },
    restore() {
      const cached = localStorage.getItem(STORAGE_KEY);
      if (cached) {
        try {
          const parsed = JSON.parse(cached) as Partial<SessionState>;
          this.user = parsed.user ?? null;
          this.menuTree = parsed.menuTree ?? [];
          this.releaseNavigationTree = parsed.releaseNavigationTree ?? [];
          this.deliveryEngineV1 = parsed.deliveryEngineV1 ?? null;
          this.editionRuntimeV1 = parsed.editionRuntimeV1 ?? null;
          this.requestedEditionKey = normalizeEditionKey(parsed.requestedEditionKey) || 'standard';
          this.effectiveEditionKey = normalizeEditionKey(parsed.effectiveEditionKey) || 'standard';
          this.menuExpandedKeys = parsed.menuExpandedKeys ?? [];
          this.currentAction = parsed.currentAction ?? null;
          this.capabilities = parsed.capabilities ?? [];
          this.scenes = parsed.scenes ?? [];
          this.sceneVersion = parsed.sceneVersion ?? null;
          this.roleSurface = parsed.roleSurface ?? null;
          this.roleSurfaceMap = parsed.roleSurfaceMap ?? {};
          this.capabilityCatalog = parsed.capabilityCatalog ?? {};
          this.sceneActionHints = parsed.sceneActionHints ?? {};
          this.capabilityGroups = parsed.capabilityGroups ?? [];
          this.productFacts = parsed.productFacts ?? { license: null, bundle: null };
          this.enterpriseEnablement = parsed.enterpriseEnablement ?? null;
          this.workspaceHome = parsed.workspaceHome ?? null;
          this.workspaceHomeRef = parsed.workspaceHomeRef ?? null;
          this.pageContracts = parsed.pageContracts ?? {};
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
      const token = sessionStorage.getItem(TOKEN_STORAGE_KEY_SCOPED);
      if (token) {
        this.token = token;
      }
      // Always purge legacy unscoped token to avoid cross-db pollution.
      sessionStorage.removeItem(TOKEN_STORAGE_KEY_LEGACY);
      if (this.token && this.menuTree.length) {
        this.isReady = true;
        this.initStatus = 'ready';
      } else {
        this.isReady = false;
        this.initStatus = 'idle';
      }
    },
    clearSession() {
      this.token = null;
      this.user = null;
      this.menuTree = [];
      this.releaseNavigationTree = [];
      this.deliveryEngineV1 = null;
      this.editionRuntimeV1 = null;
      this.requestedEditionKey = 'standard';
      this.effectiveEditionKey = 'standard';
      this.menuExpandedKeys = [];
      this.currentAction = null;
      this.capabilities = [];
      this.scenes = [];
      this.sceneVersion = null;
      this.roleSurface = null;
      this.roleSurfaceMap = {};
      this.capabilityCatalog = {};
      this.sceneActionHints = {};
      this.capabilityGroups = [];
      this.productFacts = { license: null, bundle: null };
      this.enterpriseEnablement = null;
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
      this.initRequestSeq = 0;
      this.defaultRoute = null;
      this.bootstrapNextIntent = 'system.init';
      this.activeProjectContext = null;
      this.isReady = false;
      this.initStatus = 'idle';
      this.initError = null;
      this.initTraceId = null;
      this.initMeta = null;
      localStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem(TOKEN_STORAGE_KEY_SCOPED);
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
        user: this.user,
        menuTree: this.menuTree,
        releaseNavigationTree: this.releaseNavigationTree,
        deliveryEngineV1: this.deliveryEngineV1,
        editionRuntimeV1: this.editionRuntimeV1,
        requestedEditionKey: this.requestedEditionKey,
        effectiveEditionKey: this.effectiveEditionKey,
        menuExpandedKeys: this.menuExpandedKeys,
        currentAction: this.currentAction,
        capabilities: this.capabilities,
        scenes: this.scenes,
        sceneVersion: this.sceneVersion,
        roleSurface: this.roleSurface,
        roleSurfaceMap: this.roleSurfaceMap,
        capabilityCatalog: this.capabilityCatalog,
        sceneActionHints: this.sceneActionHints,
        capabilityGroups: this.capabilityGroups,
        productFacts: this.productFacts,
        enterpriseEnablement: this.enterpriseEnablement,
        workspaceHome: this.workspaceHome,
        workspaceHomeRef: this.workspaceHomeRef,
        pageContracts: this.pageContracts,
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
      localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
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
      const configuredDb = config.odooDbPinned
        ? String(config.odooDb || '').trim()
        : resolveActiveDb(String(config.odooDb || '').trim());
      const db = String(dbOverride || configuredDb).trim();
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
      this.user = result.user ?? null;
      this.menuTree = [];
      this.releaseNavigationTree = [];
      this.deliveryEngineV1 = null;
      this.editionRuntimeV1 = null;
      this.requestedEditionKey = 'standard';
      this.effectiveEditionKey = 'standard';
      this.menuExpandedKeys = [];
      this.currentAction = null;
      this.capabilities = [];
      this.scenes = [];
      this.sceneVersion = null;
      this.roleSurface = null;
      this.roleSurfaceMap = {};
      this.capabilityCatalog = {};
      this.sceneActionHints = {};
      this.capabilityGroups = [];
      this.productFacts = { license: null, bundle: null };
      this.enterpriseEnablement = null;
      this.workspaceHome = null;
      this.workspaceHomeRef = null;
      this.sceneReadyContractV1 = null;
      this.sceneGovernanceV1 = null;
      this.initMeta = null;
      this.initRequestSeq = 0;
      this.defaultRoute = null;
      this.activeProjectContext = null;
      this.isReady = false;
      this.initStatus = 'idle';
      this.initError = null;
      this.initTraceId = null;
      setSceneRegistry([]);
      this.bootstrapNextIntent = nextIntent;
      this.setToken(token);
    },
    syncRequestedEditionKey(rawEditionKey?: string | null) {
      const normalized = normalizeEditionKey(rawEditionKey) || this.requestedEditionKey || 'standard';
      if (normalized === this.requestedEditionKey) {
        return false;
      }
      this.requestedEditionKey = normalized;
      this.persist();
      return true;
    },
    async logout() {
      try {
        await intentRequest<{ message?: string }>({ intent: 'auth.logout' });
      } catch {
        // ignore logout failure
      }
      this.clearSession();
    },
    async loadAppInit() {
      const requestSeq = this.initRequestSeq + 1;
      this.initRequestSeq = requestSeq;
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
      const debugIntent =
        import.meta.env.DEV ||
        localStorage.getItem('DEBUG_INTENT') === '1' ||
        new URLSearchParams(window.location.search).get('debug') === '1';

      // A1: 打印本次 system.init 的有效参数
      if (debugIntent) {
        console.group('[A1] system.init 请求诊断');
        console.log('1. API Base URL:', import.meta.env.VITE_API_BASE_URL);
        console.log('2. Authorization 存在:', !!this.token);
        if (this.token) {
          console.log('   Token 前10位:', this.token.substring(0, 10) + '...');
        }
        console.log('3. X-Odoo-DB 环境变量:', import.meta.env.VITE_ODOO_DB);
      }

      const requestParams = {
        intent: 'system.init',
        params: {
          scene: 'web',
          with_preload: false,
          root_xmlid: 'smart_construction_core.menu_sc_root',
          edition_key: this.requestedEditionKey || 'standard',
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
        if (requestSeq !== this.initRequestSeq) {
          throw err;
        }
        if (err instanceof ApiError) {
          this.initError = err.message;
          this.initTraceId = err.traceId ?? null;
        } else {
          this.initError = err instanceof Error ? err.message : 'init failed';
        }
        this.initStatus = 'error';
        throw err;
      }
      if (requestSeq !== this.initRequestSeq) {
        return result;
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
            }
          : null,
        bundle: Object.keys(rawBundle).length
          ? {
              name: String(rawBundle.name || ''),
              scenes: Array.isArray(rawBundle.scenes) ? rawBundle.scenes.map((item) => String(item || '')).filter(Boolean) : [],
              capabilities: Array.isArray(rawBundle.capabilities) ? rawBundle.capabilities.map((item) => String(item || '')).filter(Boolean) : [],
              recommended_roles: Array.isArray(rawBundle.recommended_roles)
                ? rawBundle.recommended_roles.map((item) => String(item || '')).filter(Boolean)
                : [],
              default_dashboard: String(rawBundle.default_dashboard || ''),
            }
          : null,
      };
      const enterpriseEnablementRaw = (extFacts.enterprise_enablement && typeof extFacts.enterprise_enablement === 'object')
        ? (extFacts.enterprise_enablement as Record<string, unknown>)
        : {};
      const enterpriseMainlineRaw = (enterpriseEnablementRaw.mainline && typeof enterpriseEnablementRaw.mainline === 'object')
        ? (enterpriseEnablementRaw.mainline as Record<string, unknown>)
        : {};
      this.enterpriseEnablement = Object.keys(enterpriseMainlineRaw).length
        ? {
            version: String(enterpriseMainlineRaw.version || ''),
            phase: String(enterpriseMainlineRaw.phase || ''),
            theme: String(enterpriseMainlineRaw.theme || ''),
            entry_root_xmlid: String(enterpriseMainlineRaw.entry_root_xmlid || ''),
            current_company_id: Number(enterpriseMainlineRaw.current_company_id || 0),
            current_company_name: String(enterpriseMainlineRaw.current_company_name || ''),
            primary_action: normalizeEnterpriseEnablementTarget(enterpriseMainlineRaw.primary_action),
            steps: Array.isArray(enterpriseMainlineRaw.steps)
              ? enterpriseMainlineRaw.steps
                .map((item) => {
                  const row = (item && typeof item === 'object') ? (item as Record<string, unknown>) : {};
                  return {
                    key: String(row.key || ''),
                    label: String(row.label || row.key || ''),
                    status: String(row.status || ''),
                    entry_xmlid: String(row.entry_xmlid || ''),
                    action_xmlid: String(row.action_xmlid || ''),
                    next_hint: String(row.next_hint || ''),
                    target: normalizeEnterpriseEnablementTarget(row.target),
                  };
                })
                .filter((item) => item.key.length > 0)
              : [],
          }
        : null;
      this.workspaceHome = ((result as AppInitResponse & { workspace_home?: WorkspaceHomeContract }).workspace_home ?? null);
      const initMeta = (result as AppInitResponse).init_meta ?? {};
      const preloadHint = (initMeta.workspace_home_preload_hint && typeof initMeta.workspace_home_preload_hint === 'object')
        ? initMeta.workspace_home_preload_hint
        : null;
      const workspaceHomeRefRaw = ((result as AppInitResponse & {
        workspace_home_ref?: { intent?: string; scene_key?: string; loaded?: boolean }
      }).workspace_home_ref ?? null);
      this.workspaceHomeRef = workspaceHomeRefRaw ?? (preloadHint
        ? {
            intent: String(preloadHint.intent || 'ui.contract'),
            scene_key: String(preloadHint.scene_key || ''),
            loaded: false,
          }
        : null);
      this.sceneReadyContractV1 = ((result as AppInitResponse & { scene_ready_contract_v1?: SceneReadyContract }).scene_ready_contract_v1 ?? null);
      this.sceneGovernanceV1 = ((result as AppInitResponse & { scene_governance_v1?: SceneGovernancePayload }).scene_governance_v1 ?? null);
      if (this.sceneReadyContractV1?.scenes?.length) {
        setSceneRegistryFromSceneReadyContract(this.sceneReadyContractV1);
      } else {
        setSceneRegistry(this.scenes);
      }
      this.initMeta = {
        ...(result.meta ?? {}),
        nav_meta: (result as AppInitResponse).nav_meta ?? null,
        init_meta: initMeta,
        version: (result as AppInitResponse).version ?? null,
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
      const candidates = [result.nav];
      this.deliveryEngineV1 = (result as AppInitResponse).delivery_engine_v1 ?? null;
      this.editionRuntimeV1 = (result as AppInitResponse).edition_runtime_v1 ?? null;
      const requestedEditionKey = normalizeEditionKey(this.editionRuntimeV1?.requested?.edition_key)
        || normalizeEditionKey(this.requestedEditionKey)
        || 'standard';
      const effectiveEditionKey = normalizeEditionKey(this.editionRuntimeV1?.effective?.edition_key)
        || normalizeEditionKey(this.deliveryEngineV1?.edition_key)
        || requestedEditionKey
        || 'standard';
      this.requestedEditionKey = requestedEditionKey;
      this.effectiveEditionKey = effectiveEditionKey;
      const releaseNav = Array.isArray(result.release_navigation_v1?.nav)
        ? result.release_navigation_v1?.nav
        : [];
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
      const releaseNavigationTreeWithKeys = releaseNav.map((item, index) => addKeys(item, index + 1000));
      this.menuTree = menuTreeWithKeys;
      this.releaseNavigationTree = releaseNavigationTreeWithKeys;
      const activeTree = this.releaseNavigationTree.length ? this.releaseNavigationTree : this.menuTree;
      const filteredExpandedKeys = filterExpandedKeys(activeTree, this.menuExpandedKeys);
      this.menuExpandedKeys = filteredExpandedKeys.length ? filteredExpandedKeys : defaultExpandedKeys(activeTree);
      this.isReady = true;
      this.initStatus = 'ready';
      this.persist();
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
          with_preload: true,
          root_xmlid: 'smart_construction_core.menu_sc_root',
          edition_key: this.requestedEditionKey || 'standard',
        },
      });
      const row = result as AppInitResponse & {
        workspace_home?: WorkspaceHomeContract;
        workspace_home_ref?: { intent?: string; scene_key?: string; loaded?: boolean };
        scene_ready_contract_v1?: SceneReadyContract;
      };
      this.workspaceHome = row.workspace_home ?? this.workspaceHome;
      this.workspaceHomeRef = row.workspace_home
        ? {
            ...(this.workspaceHomeRef ?? {}),
            intent: String(this.workspaceHomeRef?.intent || 'ui.contract'),
            scene_key: String(this.workspaceHomeRef?.scene_key || 'portal.dashboard'),
            loaded: true,
          }
        : (row.workspace_home_ref ?? this.workspaceHomeRef);
      this.sceneReadyContractV1 = row.scene_ready_contract_v1 ?? this.sceneReadyContractV1;
      if (this.sceneReadyContractV1?.scenes?.length) {
        setSceneRegistryFromSceneReadyContract(this.sceneReadyContractV1);
      }
      this.persist();
      return this.workspaceHome;
    },
    async ensurePageContract(pageKey: string, force = false) {
      const normalizedPageKey = String(pageKey || '').trim().toLowerCase();
      if (!normalizedPageKey) {
        return {} as PageContract;
      }
      const cached = this.pageContracts?.[normalizedPageKey];
      if (!force && cached && Object.keys(cached).length > 0) {
        return cached;
      }
      const result = await intentRequest<{
        page_key?: string;
        page_contract?: PageContract;
      }>({
        intent: 'page.contract',
        params: {
          page_key: normalizedPageKey,
          scene: 'web',
          root_xmlid: 'smart_construction_core.menu_sc_root',
        },
      });
      const runtimePayload = (result && typeof result === 'object') ? result : {};
      const runtimePageKey = String(runtimePayload.page_key || normalizedPageKey).trim().toLowerCase() || normalizedPageKey;
      const runtimeContract = (runtimePayload.page_contract && typeof runtimePayload.page_contract === 'object')
        ? (runtimePayload.page_contract as PageContract)
        : ({} as PageContract);
      this.pageContracts = {
        ...this.pageContracts,
        [runtimePageKey]: runtimeContract,
      };
      this.persist();
      return runtimeContract;
    },
    async ensureReady() {
      if (this.isReady) {
        return;
      }
      await this.loadAppInit();
    },
    setActiveProjectContext(context?: Record<string, unknown> | null) {
      this.activeProjectContext = normalizeProjectEntryContext(context) || null;
    },
    clearActiveProjectContext() {
      this.activeProjectContext = null;
    },
    async resolvePrimaryEntryPath(fallback = MY_WORK_PATH) {
      const preferredContext = normalizeProjectEntryContext(this.activeProjectContext);
      if (preferredContext?.project_id) {
        this.activeProjectContext = preferredContext;
        return PROJECT_MANAGEMENT_PATH;
      }
      try {
        const result = await intentRequest<{
          available?: boolean;
          route?: string;
          project_context?: Record<string, unknown>;
        }>({
          intent: 'project.entry.context.resolve',
          params: {},
        });
        const resolvedContext = normalizeProjectEntryContext(result?.project_context);
        if (resolvedContext?.project_id && result?.available !== false) {
          this.activeProjectContext = resolvedContext;
          return String(result.route || PROJECT_MANAGEMENT_PATH).trim() || PROJECT_MANAGEMENT_PATH;
        }
      } catch {
        // degrade to fallback
      }
      this.activeProjectContext = null;
      return this.resolveLandingPath(fallback);
    },
    resolveLandingPath(fallback = '/') {
      const defaultRoutePath = String(this.defaultRoute?.route || '').trim();
      const defaultRouteSceneKey = String(this.defaultRoute?.scene_key || '').trim();
      const startsWithNativeActionRoute = /^\/(a|f|r)\//.test(defaultRoutePath);
      if (defaultRoutePath.startsWith('/') && !startsWithNativeActionRoute) {
        if (
          defaultRoutePath.startsWith('/workbench')
          && defaultRouteSceneKey
          && !getSceneByKey(defaultRouteSceneKey)
        ) {
          return buildSceneRegistryFallbackPath({
            sceneKey: defaultRouteSceneKey,
            menuId: Number(this.defaultRoute?.menu_id || 0) || undefined,
            label: defaultRouteSceneKey,
          });
        }
        const normalized = normalizeLegacyWorkbenchPath(defaultRoutePath);
        if (isUnifiedHomePath(normalized)) return '/';
        if (normalized) return normalized;
      }
      if (defaultRouteSceneKey) {
        if (isUnifiedHomeSceneKey(defaultRouteSceneKey)) {
          return '/';
        }
        const scene = getSceneByKey(defaultRouteSceneKey);
        const rawPath = String(scene?.target?.route || scene?.route || `/s/${defaultRouteSceneKey}`).trim();
        const normalized = normalizeLegacyWorkbenchPath(rawPath);
        if (isUnifiedHomePath(normalized)) return '/';
        if (normalized) return normalized;
        return `/s/${defaultRouteSceneKey}`;
      }
      const candidate = String(this.roleSurface?.landing_path || '').trim();
      if (candidate.startsWith('/')) {
        const normalized = normalizeLegacyWorkbenchPath(candidate);
        if (isUnifiedHomePath(normalized)) return '/';
        return normalized || fallback;
      }
      const sceneKey = String(this.roleSurface?.landing_scene_key || '').trim();
      if (sceneKey) {
        if (isUnifiedHomeSceneKey(sceneKey)) {
          return '/';
        }
        const scene = getSceneByKey(sceneKey);
        const rawPath = String(scene?.target?.route || scene?.route || `/s/${sceneKey}`).trim();
        const normalized = normalizeLegacyWorkbenchPath(rawPath);
        if (isUnifiedHomePath(normalized)) return '/';
        return normalized || `/s/${sceneKey}`;
      }
      return fallback;
    },
  },
});

function isUnifiedHomeSceneKey(sceneKey: string): boolean {
  const normalized = String(sceneKey || '').trim().toLowerCase();
  return normalized === 'workspace.home' || normalized === 'portal.dashboard';
}

function isUnifiedHomePath(path: string): boolean {
  const normalized = String(path || '').trim().toLowerCase();
  return normalized === '/' || normalized === '/s/workspace.home' || normalized === '/s/portal.dashboard';
}

function addKeys(node: NavNode, index = 0): NavNode {
  const key = (node as NavNode & { xmlid?: string }).xmlid || node.key || `menu_${node.menu_id || node.id || index}`;
  const children = node.children?.map((child, idx) => addKeys(child, idx)) ?? [];
  return { ...node, key, children };
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

function defaultExpandedKeys(tree: NavNode[]): string[] {
  const keys: string[] = [];
  tree.forEach((node) => {
    if (node.key && node.children?.length) {
      keys.push(node.key);
    }
    node.children?.forEach((child) => {
      if (child.key && child.children?.length) {
        keys.push(child.key);
      }
    });
  });
  return keys;
}
