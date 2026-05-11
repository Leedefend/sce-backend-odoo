import { createRouter, createWebHistory } from 'vue-router';
import { useSessionStore } from '../stores/session';
import LoginView from '../views/LoginView.vue';
import HomeView from '../views/HomeView.vue';
import MenuView from '../views/MenuView.vue';
import ActionView from '../views/ActionViewShell.vue';
import ContractFormPage from '../pages/ContractFormPage.vue';
import WorkbenchView from '../views/WorkbenchView.vue';
import SceneView from '../views/SceneView.vue';
import ProjectsIntakeView from '../views/ProjectsIntakeView.vue';
import MyWorkView from '../views/MyWorkView.vue';
import SceneHealthView from '../views/SceneHealthView.vue';
import ScenePackagesView from '../views/ScenePackagesView.vue';
import UsageAnalyticsView from '../views/UsageAnalyticsView.vue';
import { ApiError } from '../api/client';
import { buildCanonicalSceneRouteTarget, normalizeEmbeddedSceneQuery, normalizeLegacyWorkbenchPath, parseSceneKeyFromQuery } from '../app/routeQuery';
import { getSceneByKey } from '../app/resolvers/sceneRegistry';
import { findMenuNode } from '../app/menu';

const APP_TITLE = '智能施工企业管理平台';

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
    { path: '/', name: 'home', component: HomeView, meta: { layout: 'shell', sceneKey: 'workspace.home' } },
    { path: '/s/workspace.home', name: 'scene-home', component: HomeView, meta: { layout: 'shell', sceneKey: 'workspace.home' } },
    { path: '/my-work', name: 'my-work', component: MyWorkView, meta: { layout: 'shell' } },
    { path: '/s/my_work.workspace', name: 'scene-my-work', component: MyWorkView, meta: { layout: 'shell', sceneKey: 'my_work.workspace' } },
    { path: '/pm/dashboard', name: 'project-management-dashboard', redirect: '/s/project.management', meta: { layout: 'shell' } },
    { path: '/s/projects.intake', name: 'projects-intake', component: ProjectsIntakeView, meta: { layout: 'shell', sceneKey: 'projects.intake' } },
    { path: '/s/:sceneKey', name: 'scene', component: SceneView, meta: { layout: 'shell' } },
    { path: '/m/:menuId', name: 'menu', component: MenuView, meta: { layout: 'shell' } },
    // Diagnostic-only surface; must not be used as product navigation.
    { path: '/workbench', name: 'workbench', component: WorkbenchView, meta: { layout: 'shell' } },
    { path: '/admin/scene-health', name: 'scene-health', component: SceneHealthView, meta: { layout: 'shell', adminOnly: true } },
    { path: '/admin/scene-packages', name: 'scene-packages', component: ScenePackagesView, meta: { layout: 'shell', adminOnly: true } },
    { path: '/admin/usage-analytics', name: 'usage-analytics', component: UsageAnalyticsView, meta: { layout: 'shell', adminOnly: true } },
    { path: '/a/:actionId', name: 'action', component: ActionView, meta: { layout: 'shell' } },
    { path: '/f/:model/:id', name: 'model-form', component: ContractFormPage, meta: { layout: 'shell' } },
    { path: '/r/:model/:id', name: 'record', component: ContractFormPage, meta: { layout: 'shell' } },
  ],
});

router.beforeEach(async (to) => {
  applyDocumentTitle(to.name);
  const session = useSessionStore();
  if (to.name !== 'login' && !session.token) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.name !== 'login' && session.token && !session.isReady) {
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
    const groups = session.user?.groups_xmlids || [];
    const isAdmin =
      groups.includes('base.group_system') ||
      groups.includes('smart_construction_core.group_sc_cap_config_admin');
    if (!isAdmin) {
      return { path: session.resolveLandingPath('/') };
    }
  }
  return true;
});

export default router;
