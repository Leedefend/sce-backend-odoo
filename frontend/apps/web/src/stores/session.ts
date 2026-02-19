import { defineStore } from 'pinia';
import type { AppInitResponse, LoginResponse, NavMeta, NavNode } from '@sc/schema';
import { intentRequest } from '../api/intents';
import { ApiError } from '../api/client';
import { setSceneRegistry } from '../app/resolvers/sceneRegistry';
import type { Scene } from '../app/resolvers/sceneRegistry';
import { normalizeLegacyWorkbenchPath } from '../app/routeQuery';

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

const STORAGE_KEY = 'sc_frontend_session_v0_2';

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
      sessionStorage.setItem('sc_auth_token', token);
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
          if (this.scenes.length) {
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
      const token = sessionStorage.getItem('sc_auth_token');
      if (token) {
        this.token = token;
      }
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
      setSceneRegistry([]);
      this.lastTraceId = '';
      this.lastIntent = '';
      this.lastLatencyMs = null;
      this.lastWriteMode = '';
      this.isReady = false;
      localStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem('sc_auth_token');
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
      const result = await intentRequest<LoginResponse>({
        intent: 'login',
        params: { login: username, password },
      });
      this.token = result.token;
      sessionStorage.setItem('sc_auth_token', result.token);
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
      this.scenes = ((result as AppInitResponse & { scenes?: Scene[] }).scenes ?? []).filter(Boolean);
      this.sceneVersion = (result as AppInitResponse & { scene_version?: string; sceneVersion?: string }).scene_version ?? (result as AppInitResponse & { scene_version?: string; sceneVersion?: string }).sceneVersion ?? null;
      const roleSurfaceRaw = (result as AppInitResponse & { role_surface?: Partial<RoleSurface> }).role_surface ?? {};
      this.roleSurface = {
        role_code: String(roleSurfaceRaw.role_code || 'owner'),
        role_label: String(roleSurfaceRaw.role_label || roleSurfaceRaw.role_code || 'Owner'),
        landing_scene_key: String(roleSurfaceRaw.landing_scene_key || ''),
        landing_menu_id: typeof roleSurfaceRaw.landing_menu_id === 'number' ? roleSurfaceRaw.landing_menu_id : null,
        landing_menu_xmlid: String(roleSurfaceRaw.landing_menu_xmlid || ''),
        landing_path: String(roleSurfaceRaw.landing_path || ''),
        scene_candidates: Array.isArray(roleSurfaceRaw.scene_candidates) ? roleSurfaceRaw.scene_candidates.map((item) => String(item || '')).filter(Boolean) : [],
        menu_xmlids: Array.isArray(roleSurfaceRaw.menu_xmlids) ? roleSurfaceRaw.menu_xmlids.map((item) => String(item || '')).filter(Boolean) : [],
      };
      this.roleSurfaceMap = ((result as AppInitResponse & { role_surface_map?: RoleSurfaceMap }).role_surface_map ?? {});
      setSceneRegistry(this.scenes);
      this.initMeta = {
        ...(result.meta ?? {}),
        nav_meta: (result as AppInitResponse & { nav_meta?: unknown }).nav_meta ?? null,
      } as AppInitResponse['meta'];
      const candidates = [
        result.nav,
        // tolerate legacy/misaligned keys during bootstrap
        (result as AppInitResponse & { menuTree?: NavNode[] }).menuTree,
        (result as AppInitResponse & { menu_tree?: NavNode[] }).menu_tree,
        (result as AppInitResponse & { menus?: NavNode[] }).menus,
        (result as AppInitResponse & { sections?: NavNode[] }).sections,
      ];
      if (debugIntent) {
        console.info('[debug] app.init candidates:', candidates.map(c => ({
          type: typeof c,
          isArray: Array.isArray(c),
          length: Array.isArray(c) ? c.length : 'N/A'
        })));
      }
      const nav = (candidates.find((entry) => Array.isArray(entry)) ?? []) as NavNode[];
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
      if (!this.menuTree.length) {
        await this.loadNavFallback();
      }
      this.isReady = true;
      this.initStatus = 'ready';
      this.persist();
    },
    async loadNavFallback() {
      const debugIntent =
        import.meta.env.DEV ||
        localStorage.getItem('DEBUG_INTENT') === '1' ||
        new URLSearchParams(window.location.search).get('debug') === '1';
      try {
        const result = await intentRequest<{ nav?: NavNode[] }>({
          intent: 'ui.contract',
          params: { op: 'nav', root_xmlid: 'smart_construction_core.menu_sc_root' },
        });
        const nav = result.nav ?? [];
        if (debugIntent) {
          // eslint-disable-next-line no-console
          console.info('[debug] ui.contract nav length', nav.length);
        }
        if (nav.length) {
          this.menuTree = nav;
          this.persist();
        }
      } catch (err) {
        if (debugIntent) {
          // eslint-disable-next-line no-console
          console.warn('[debug] ui.contract nav failed', err);
        }
      }
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
        return `/s/${sceneKey}`;
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
