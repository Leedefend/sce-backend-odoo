import { defineStore } from 'pinia';
import type { AppInitResponse, LoginResponse, NavMeta, NavNode } from '@sc/schema';
import { intentRequest } from '../api/intents';

export interface SessionState {
  token: string | null;
  user: AppInitResponse['user'] | null;
  menuTree: NavNode[];
  currentAction: NavMeta | null;
}

export const useSessionStore = defineStore('session', {
  state: (): SessionState => ({
    token: null,
    user: null,
    menuTree: [],
    currentAction: null,
  }),
  actions: {
    setToken(token: string) {
      this.token = token;
    },
    clearSession() {
      this.token = null;
      this.user = null;
      this.menuTree = [];
      this.currentAction = null;
    },
    setActionMeta(meta: NavMeta) {
      this.currentAction = meta;
    },
    async login(username: string, password: string) {
      const result = await intentRequest<LoginResponse>({
        intent: 'login',
        params: { login: username, password },
      });
      this.token = result.token;
    },
    async loadAppInit() {
      const result = await intentRequest<AppInitResponse>({
        intent: 'app.init',
        params: { scene: 'web', with_preload: false },
      });
      this.user = result.user;
      this.menuTree = result.nav ?? [];
    },
  },
});
