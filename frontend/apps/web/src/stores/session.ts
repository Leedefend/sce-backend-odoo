import { defineStore } from 'pinia';
import type { AppInitResponse, LoginResponse, NavMeta, NavNode } from '@sc/schema';
import { intentRequest } from '../api/intents';

export interface SessionState {
  token: string | null;
  user: AppInitResponse['user'] | null;
  menuTree: NavNode[];
  currentAction: NavMeta | null;
  isReady: boolean;
}

const STORAGE_KEY = 'sc_frontend_session_v0_2';

export const useSessionStore = defineStore('session', {
  state: (): SessionState => ({
    token: null,
    user: null,
    menuTree: [],
    currentAction: null,
    isReady: false,
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
          this.currentAction = parsed.currentAction ?? null;
        } catch {
          // ignore corrupted cache
        }
      }
      const token = sessionStorage.getItem('sc_auth_token');
      if (token) {
        this.token = token;
      }
    },
    clearSession() {
      this.token = null;
      this.user = null;
      this.menuTree = [];
      this.currentAction = null;
      this.isReady = false;
      localStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem('sc_auth_token');
    },
    setActionMeta(meta: NavMeta) {
      this.currentAction = meta;
      this.persist();
    },
    persist() {
      const snapshot: Partial<SessionState> = {
        user: this.user,
        menuTree: this.menuTree,
        currentAction: this.currentAction,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
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
      const result = await intentRequest<AppInitResponse>({
        intent: 'app.init',
        params: {
          scene: 'web',
          with_preload: false,
          root_xmlid: 'smart_construction_core.menu_sc_root',
        },
      });
      if (import.meta.env.DEV) {
        // eslint-disable-next-line no-console
        console.info('[debug] app.init result', result);
      }
      this.user = result.user;
      const candidates = [
        result.nav,
        // tolerate legacy/misaligned keys during bootstrap
        (result as AppInitResponse & { menuTree?: NavNode[] }).menuTree,
        (result as AppInitResponse & { menu_tree?: NavNode[] }).menu_tree,
        (result as AppInitResponse & { menus?: NavNode[] }).menus,
        (result as AppInitResponse & { sections?: NavNode[] }).sections,
      ];
      const nav = candidates.find((entry) => Array.isArray(entry)) ?? [];
      if (import.meta.env.DEV) {
        // eslint-disable-next-line no-console
        console.info('[debug] app.init nav length', (nav as NavNode[]).length);
      }
      this.menuTree = nav as NavNode[];
      if (!this.menuTree.length) {
        await this.loadNavFallback();
      }
      this.isReady = true;
      this.persist();
    },
    async loadNavFallback() {
      try {
        const result = await intentRequest<{ nav?: NavNode[] }>({
          intent: 'ui.contract',
          params: { op: 'nav', root_xmlid: 'smart_construction_core.menu_sc_root' },
        });
        const nav = result.nav ?? [];
        if (import.meta.env.DEV) {
          // eslint-disable-next-line no-console
          console.info('[debug] ui.contract nav length', nav.length);
        }
        if (nav.length) {
          this.menuTree = nav;
          this.persist();
        }
      } catch (err) {
        if (import.meta.env.DEV) {
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
  },
});
