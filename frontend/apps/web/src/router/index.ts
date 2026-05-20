import { createRouter, createWebHistory } from 'vue-router';
import { useSessionStore } from '../stores/session';
import LoginView from '../views/LoginView.vue';
import { ApiError } from '../api/client';
import { buildCanonicalSceneRouteTarget, normalizeEmbeddedSceneQuery, normalizeLegacyWorkbenchPath, parseSceneKeyFromQuery } from '../app/routeQuery';
import { getSceneByKey } from '../app/resolvers/sceneRegistry';
import { findMenuNode } from '../app/menu';
import { config } from '../config';

const APP_TITLE = config.appTitle;

function routeTitle(routeName: string | symbol | null | undefined): string {
  const name = typeof routeName === 'string' ? routeName : '';
  const map: Record<string, string> = {
    login: '登录',
    home: '角色首页',
    'scene-home': '角色首页',
    'my-work': '我的工作',
    'scene-my-work': '我的工作',
    'projects-intake': '项目立项',
    scene: '业务场景',
    menu: '业务菜单',
    action: '业务动作',
    workbench: '诊断页',
    'scene-health': '场景健康',
    'scene-packages': '场景发布包',
    'usage-analytics': '使用分析',
    'release-operator': '产品发布',
    'menu-config': '菜单配置',
    'model-form': '业务表单',
    record: '业务记录',
  };
  return map[name] || '系统';
}

function applyDocumentTitle(routeName: string | symbol | null | undefined) {
  document.title = `${routeTitle(routeName)} - ${APP_TITLE}`;
}

function splitRoutePath(rawPath: string) {
  const [path, queryString = ''] = String(rawPath || '').split('?', 2);
  const query: Record<string, string> = {};
  if (queryString) {
    new URLSearchParams(queryString).forEach((value, key) => {
      query[key] = value;
    });
  }
  return { path, query };
}

function positiveInteger(value: unknown): number {
  const parsed = Number(value || 0);
  if (!Number.isFinite(parsed) || parsed <= 0) return 0;
  return Math.trunc(parsed);
}

function resolveExplicitSceneKeyFromMenuContext(menuId: number, session: ReturnType<typeof useSessionStore>): string {
  const menuNode = menuId > 0 ? findMenuNode(session.menuTree, menuId) : null;
  const entryTarget = (menuNode?.meta?.entry_target && typeof menuNode.meta.entry_target === 'object')
    ? menuNode.meta.entry_target as Record<string, unknown>
    : {};
  const entrySceneKey = String(entryTarget.scene_key || '').trim();
  if (entrySceneKey) return entrySceneKey;
  const menuSceneKey = String(menuNode?.meta?.scene_key || '').trim();
  if (menuSceneKey) return menuSceneKey;
  return '';
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/platform-admin/login', name: 'platform-admin-login', component: LoginView },
    { path: '/', name: 'home', component: () => import('../views/HomeView.vue'), meta: { layout: 'shell', sceneKey: 'workspace.home' } },
    { path: '/s/workspace.home', name: 'scene-home', component: () => import('../views/HomeView.vue'), meta: { layout: 'shell', sceneKey: 'workspace.home' } },
    { path: '/my-work', name: 'my-work', component: () => import('../views/MyWorkView.vue'), meta: { layout: 'shell' } },
    { path: '/s/my_work.workspace', name: 'scene-my-work', component: () => import('../views/MyWorkView.vue'), meta: { layout: 'shell', sceneKey: 'my_work.workspace' } },
    { path: '/pm/dashboard', name: 'project-management-dashboard', redirect: '/s/project.management', meta: { layout: 'shell' } },
    { path: '/s/projects.intake', name: 'projects-intake', component: () => import('../views/ProjectsIntakeView.vue'), meta: { layout: 'shell', sceneKey: 'projects.intake' } },
    { path: '/s/:sceneKey', name: 'scene', component: () => import('../views/SceneView.vue'), meta: { layout: 'shell' } },
    { path: '/m/:menuId', name: 'menu', component: () => import('../views/MenuView.vue'), meta: { layout: 'shell' } },
    // Diagnostic-only surface; must not be used as product navigation.
    { path: '/workbench', name: 'workbench', component: () => import('../views/WorkbenchView.vue'), meta: { layout: 'shell' } },
    { path: '/admin/scene-health', name: 'scene-health', component: () => import('../views/SceneHealthView.vue'), meta: { layout: 'shell', adminOnly: true } },
    { path: '/admin/scene-packages', name: 'scene-packages', component: () => import('../views/ScenePackagesView.vue'), meta: { layout: 'shell', adminOnly: true } },
    { path: '/admin/usage-analytics', name: 'usage-analytics', component: () => import('../views/UsageAnalyticsView.vue'), meta: { layout: 'shell', adminOnly: true } },
    { path: '/admin/release-operator', name: 'release-operator', component: () => import('../views/ReleaseOperatorView.vue'), meta: { layout: 'shell', adminOnly: true } },
    { path: '/admin/menu-config', name: 'menu-config', component: () => import('../views/MenuConfigView.vue'), meta: { layout: 'shell' } },
    { path: '/a/:actionId', name: 'action', component: () => import('../views/ActionViewShell.vue'), meta: { layout: 'shell' } },
    { path: '/f/:model/:id', name: 'model-form', component: () => import('../pages/ContractFormPage.vue'), meta: { layout: 'shell' } },
    { path: '/r/:model/:id', name: 'record', component: () => import('../pages/ContractFormPage.vue'), meta: { layout: 'shell' } },
  ],
});

router.beforeEach(async (to) => {
  applyDocumentTitle(to.name);
  const session = useSessionStore();
  const isLoginRoute = to.name === 'login' || to.name === 'platform-admin-login';
  const wantsPlatformAdminEntry = to.path.startsWith('/platform-admin') || String(to.query.platform_admin || '') === '1';
  if (!isLoginRoute && !session.token) {
    return wantsPlatformAdminEntry
      ? { name: 'platform-admin-login', query: { redirect: to.fullPath } }
      : { name: 'login', query: { redirect: to.fullPath } };
  }
  if (!isLoginRoute && session.token && !session.isReady) {
    try {
      await session.ensureReady();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        return { name: 'login', query: { redirect: to.fullPath } };
      }
      return true;
    }
  }
  const normalizedEmbeddedQuery = normalizeEmbeddedSceneQuery(to.query);
  if (normalizedEmbeddedQuery.changed) {
    return { path: to.path, query: normalizedEmbeddedQuery.query };
  }
  const normalizedWorkbenchPath = normalizeLegacyWorkbenchPath(to.fullPath);
  if (normalizedWorkbenchPath !== to.fullPath && normalizedWorkbenchPath !== to.path) {
    return splitRoutePath(normalizedWorkbenchPath);
  }
  const querySceneKey = parseSceneKeyFromQuery(to.query);
  if (to.name === 'action') {
    const actionId = positiveInteger(to.params.actionId || to.query.action_id);
    const menuId = positiveInteger(to.query.menu_id);
    const sceneKey = querySceneKey || resolveExplicitSceneKeyFromMenuContext(menuId, session);
    if (!sceneKey) return true;
    return buildCanonicalSceneRouteTarget(sceneKey, {
      scene: getSceneByKey(sceneKey),
      query: to.query,
      actionId,
      menuId,
    });
  }
  if (to.meta?.adminOnly) {
    if (session.user?.is_platform_admin !== true) {
      return { path: session.resolveLandingPath('/') };
    }
  }
  return true;
});

export default router;
