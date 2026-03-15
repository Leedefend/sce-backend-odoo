import { defineStore } from 'pinia';
import type { AppInitResponse, LoginResponse, NavMeta, NavNode } from '@sc/schema';
import { intentRequest } from '../api/intents';
import { ApiError } from '../api/client';
import { config } from '../config';
import { getSceneByKey, setSceneRegistry, setSceneRegistryFromSceneReadyContract } from '../app/resolvers/sceneRegistry';
import type { Scene } from '../app/resolvers/sceneRegistry';
import { normalizeLegacyWorkbenchPath } from '../app/routeQuery';
import { applySceneValidationRecoveryStrategyRuntime, setSceneValidationRecoveryStrategy } from '../app/sceneValidationRecoveryStrategy';

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
  advice?: unknown[];
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
  user: AppInitResponse['user'] | null;
  menuTree: NavNode[];
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
  workspaceHome: WorkspaceHomeContract | null;
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

export const useSessionStore = defineStore('session', {
  state: (): SessionState => ({
    token: null,
    user: null,
    menuTree: [],
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
    workspaceHome: null,
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
          this.workspaceHome = parsed.workspaceHome ?? null;
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
      if (this.menuTree.length) {
        this.isReady = true;
        this.initStatus = 'ready';
      }
    },
    clearSession() {
      this.token = null;
      this.user = null;
      this.menuTree = [];
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
      this.workspaceHome = null;
      this.pageContracts = {};
      this.sceneReadyContractV1 = null;
      this.sceneGovernanceV1 = null;
      setSceneRegistry([]);
      this.lastTraceId = '';
      this.lastIntent = '';
      this.lastLatencyMs = null;
      this.lastWriteMode = '';
      this.isReady = false;
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
        workspaceHome: this.workspaceHome,
        pageContracts: this.pageContracts,
        sceneReadyContractV1: this.sceneReadyContractV1,
        sceneGovernanceV1: this.sceneGovernanceV1,
        lastTraceId: this.lastTraceId,
        lastIntent: this.lastIntent,
        lastLatencyMs: this.lastLatencyMs,
        lastWriteMode: this.lastWriteMode,
        initMeta: this.initMeta,
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
    async login(username: string, password: string) {
      const db = String(config.odooDb || '').trim();
      const result = await intentRequest<LoginResponse>({
        intent: 'login',
        params: { login: username, password, ...(db ? { db } : {}) },
      });
      this.setToken(result.token);
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
      this.initStatus = 'loading';
      this.initError = null;
      this.initTraceId = null;
      const debugIntent =
        import.meta.env.DEV ||
        localStorage.getItem('DEBUG_INTENT') === '1' ||
        new URLSearchParams(window.location.search).get('debug') === '1';

      // A1: 打印本次 app.init 的有效参数
      if (debugIntent) {
        console.group('[A1] app.init 请求诊断');
        console.log('1. API Base URL:', import.meta.env.VITE_API_BASE_URL);
        console.log('2. Authorization 存在:', !!this.token);
        if (this.token) {
          console.log('   Token 前10位:', this.token.substring(0, 10) + '...');
        }
        console.log('3. X-Odoo-DB 环境变量:', import.meta.env.VITE_ODOO_DB);
      }

      const requestParams = {
        intent: 'app.init',
        params: {
          scene: 'web',
          with_preload: false,
          root_xmlid: 'smart_construction_core.menu_sc_root',
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
        console.group('[A1] app.init 响应诊断');
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
        console.info('[debug] app.init result', result);
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
      this.workspaceHome = ((result as AppInitResponse & { workspace_home?: WorkspaceHomeContract }).workspace_home ?? null);
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
      const candidates = [result.nav];
      if (debugIntent) {
        console.info('[debug] app.init candidates:', candidates.map(c => ({
          type: typeof c,
          isArray: Array.isArray(c),
          length: Array.isArray(c) ? c.length : 'N/A'
        })));
      }
      const nav = (candidates.find((entry) => Array.isArray(entry)) ?? null) as NavNode[] | null;
      if (!nav) {
        this.initError = 'app.init missing required nav contract';
        this.initStatus = 'error';
        throw new Error('app.init missing required nav contract');
      }
      if (debugIntent) {
        // eslint-disable-next-line no-console
        console.info('[debug] app.init nav length', nav.length);
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
        const normalized = normalizeLegacyWorkbenchPath(candidate);
        return normalized || fallback;
      }
      const sceneKey = String(this.roleSurface?.landing_scene_key || '').trim();
      if (sceneKey) {
        const scene = getSceneByKey(sceneKey);
        const rawPath = String(scene?.target?.route || scene?.route || `/s/${sceneKey}`).trim();
        return normalizeLegacyWorkbenchPath(rawPath) || `/s/${sceneKey}`;
      }
      return fallback;
    },
  },
});

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
