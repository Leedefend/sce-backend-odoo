import { createRouter, createWebHistory } from 'vue-router';
import { useSessionStore } from '../stores/session';
import LoginView from '../views/LoginView.vue';
import HomeView from '../views/HomeView.vue';
import MenuView from '../views/MenuView.vue';
import ActionViewShell from '../views/ActionViewShell.vue';
import WorkbenchView from '../views/WorkbenchView.vue';
import SceneView from '../views/SceneView.vue';
import ProjectsIntakeView from '../views/ProjectsIntakeView.vue';
import ReleaseProductEntryView from '../views/ReleaseProductEntryView.vue';
import ReleaseOperatorView from '../views/ReleaseOperatorView.vue';
import MyWorkView from '../views/MyWorkView.vue';
import SceneHealthView from '../views/SceneHealthView.vue';
import ScenePackagesView from '../views/ScenePackagesView.vue';
import UsageAnalyticsView from '../views/UsageAnalyticsView.vue';
import CapabilityMatrixView from '../views/CapabilityMatrixView.vue';
import ModelFormPage from '../pages/ModelFormPage.vue';
import { ApiError } from '../api/client';
import { ErrorCodes } from '../app/error_codes';
import { normalizeEditionQuery, parseEditionKeyFromQuery } from '../app/routeQuery';
import { PROJECT_INTAKE_SCENE_PATH } from '../app/projectCreationBaseline';
import { resolveMenuAction, resolveScenePathFromMenuResolve } from '../app/resolvers/menuResolver';

const APP_TITLE = '智能施工企业管理平台';

function routeTitle(routeName: string | symbol | null | undefined): string {
  const name = typeof routeName === 'string' ? routeName : '';
  const map: Record<string, string> = {
    login: '登录',
    home: '工作台',
    'my-work': '我的工作',
    'project-management-dashboard': '项目管理驾驶舱',
    'release-product-entry': '产品切片入口',
    'release-operator': '发布控制台',
    scene: '业务场景',
    menu: '业务菜单',
    workbench: '工作台',
    'scene-health': '场景健康',
    'scene-packages': '场景发布包',
    'usage-analytics': '使用分析',
    'capability-matrix': '能力矩阵',
    'scene-capability-matrix': '能力矩阵',
  };
  return map[name] || '系统';
}

function applyDocumentTitle(routeName: string | symbol | null | undefined) {
  document.title = `${routeTitle(routeName)} - ${APP_TITLE}`;
}

function resolveMenuAcrossNavigationTrees(session: ReturnType<typeof useSessionStore>, menuId: number) {
  const primary = resolveMenuAction(session.releaseNavigationTree, menuId);
  if (primary.kind !== 'broken' || !session.releaseNavigationTree.length) {
    return primary;
  }
  if (primary.reason && primary.reason !== 'menu not found') {
    return primary;
  }
  return resolveMenuAction(session.menuTree, menuId);
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'home', component: HomeView, meta: { layout: 'shell' } },
    { path: '/my-work', name: 'my-work', component: MyWorkView, meta: { layout: 'shell' } },
    { path: '/capability-matrix', name: 'capability-matrix', component: CapabilityMatrixView, meta: { layout: 'shell' } },
    { path: '/portal/capability-matrix', redirect: '/s/portal.capability_matrix', meta: { layout: 'shell' } },
    { path: '/pm/dashboard', name: 'project-management-dashboard', redirect: '/s/project.management', meta: { layout: 'shell' } },
    { path: '/s/project.management', name: 'scene-project-management', component: SceneView, meta: { layout: 'shell', sceneKey: 'project.management' } },
    { path: PROJECT_INTAKE_SCENE_PATH, name: 'scene-projects-intake', component: ProjectsIntakeView, meta: { layout: 'shell' } },
    { path: '/s/project.initiation', redirect: PROJECT_INTAKE_SCENE_PATH, meta: { layout: 'shell' } },
    { path: '/s/portal.capability_matrix', name: 'scene-capability-matrix', component: CapabilityMatrixView, meta: { layout: 'shell' } },
    { path: '/release/:productKey', name: 'release-product-entry', component: ReleaseProductEntryView, meta: { layout: 'shell' } },
    { path: '/release/operator', name: 'release-operator', component: ReleaseOperatorView, meta: { layout: 'shell' } },
    { path: '/s/:sceneKey', name: 'scene', component: SceneView, meta: { layout: 'shell' } },
    { path: '/m/:menuId', name: 'menu', component: MenuView, meta: { layout: 'shell' } },
    { path: '/a/:actionId', name: 'action', component: ActionViewShell, meta: { layout: 'shell' } },
    { path: '/compat/action/:actionId', name: 'compat-action', component: ActionViewShell, meta: { layout: 'shell' } },
    { path: '/r/:model/:id', name: 'record', component: ModelFormPage, meta: { layout: 'shell' } },
    { path: '/f/:model/:id', name: 'model-form', component: ModelFormPage, meta: { layout: 'shell' } },
    { path: '/compat/record/:model/:id', name: 'compat-record', component: ModelFormPage, meta: { layout: 'shell' } },
    // Diagnostic-only surface; must not be used as product navigation.
    { path: '/workbench', name: 'workbench', component: WorkbenchView, meta: { layout: 'shell' } },
    { path: '/admin/scene-health', name: 'scene-health', component: SceneHealthView, meta: { layout: 'shell', adminOnly: true } },
    { path: '/admin/scene-packages', name: 'scene-packages', component: ScenePackagesView, meta: { layout: 'shell', adminOnly: true } },
    { path: '/admin/usage-analytics', name: 'usage-analytics', component: UsageAnalyticsView, meta: { layout: 'shell', adminOnly: true } },
  ],
});

router.beforeEach(async (to) => {
  applyDocumentTitle(to.name);
  const session = useSessionStore();
  const normalizedEditionQuery = normalizeEditionQuery(to.query);
  if (normalizedEditionQuery.changed) {
    return {
      path: to.path,
      query: normalizedEditionQuery.query,
      hash: to.hash,
      replace: true,
    };
  }
  const routeEditionKey = parseEditionKeyFromQuery(normalizedEditionQuery.query);
  const editionChanged = to.name !== 'login' ? session.syncRequestedEditionKey(routeEditionKey) : false;
  if (to.name !== 'login' && !session.token) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.name !== 'login' && session.token && (!session.isReady || editionChanged)) {
    try {
      await session.loadAppInit();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        return { name: 'login', query: { redirect: to.fullPath } };
      }
      return true;
    }
  }
  if (to.name === 'menu') {
    const menuId = Number(to.params.menuId || 0);
    if (Number.isFinite(menuId) && menuId > 0) {
      const result = resolveMenuAcrossNavigationTrees(session, menuId);
      const scenePath = resolveScenePathFromMenuResolve(result, menuId);
      if (scenePath?.path) {
        return {
          path: scenePath.path,
          query: {
            ...to.query,
            menu_id: scenePath.menuId || menuId,
            scene_key: scenePath.sceneKey,
            action_id: scenePath.actionId || undefined,
          },
          replace: true,
        };
      }
      const actionId = result.kind === 'leaf'
        ? Number(result.meta.action_id || 0)
        : Number(result.kind === 'redirect' ? result.target.action_id || 0 : 0);
      if (actionId > 0) {
        return {
          name: 'workbench',
          query: {
            ...to.query,
            reason: ErrorCodes.CONTRACT_CONTEXT_MISSING,
            diag: 'menu_route_missing_scene_identity',
            action_id: actionId,
            menu_id: result.kind === 'leaf' ? menuId : (result.target.menu_id || menuId),
          },
          replace: true,
        };
      }
    }
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
