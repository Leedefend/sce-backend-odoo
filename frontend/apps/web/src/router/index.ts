import { createRouter, createWebHistory } from 'vue-router';
import { useSessionStore } from '../stores/session';
import LoginView from '../views/LoginView.vue';
import HomeView from '../views/HomeView.vue';
import MenuView from '../views/MenuView.vue';
import ActionView from '../views/ActionViewShell.vue';
import ContractFormPage from '../pages/ContractFormPage.vue';
import WorkbenchView from '../views/WorkbenchView.vue';
import SceneView from '../views/SceneView.vue';
import ProjectManagementDashboardView from '../views/ProjectManagementDashboardView.vue';
import ProjectsIntakeView from '../views/ProjectsIntakeView.vue';
import ReleaseProductEntryView from '../views/ReleaseProductEntryView.vue';
import ReleaseOperatorView from '../views/ReleaseOperatorView.vue';
import MyWorkView from '../views/MyWorkView.vue';
import SceneHealthView from '../views/SceneHealthView.vue';
import ScenePackagesView from '../views/ScenePackagesView.vue';
import UsageAnalyticsView from '../views/UsageAnalyticsView.vue';
import { ApiError } from '../api/client';
import { normalizeEditionQuery, parseEditionKeyFromQuery } from '../app/routeQuery';

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
    action: '业务动作',
    workbench: '工作台',
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

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'home', component: HomeView, meta: { layout: 'shell' } },
    { path: '/my-work', name: 'my-work', component: MyWorkView, meta: { layout: 'shell' } },
    { path: '/pm/dashboard', name: 'project-management-dashboard', redirect: '/s/project.management', meta: { layout: 'shell' } },
    { path: '/s/project.management', name: 'scene-project-management', component: ProjectManagementDashboardView, meta: { layout: 'shell' } },
    { path: '/s/projects.intake', name: 'scene-projects-intake', component: ProjectsIntakeView, meta: { layout: 'shell' } },
    { path: '/s/project.initiation', redirect: '/s/projects.intake', meta: { layout: 'shell' } },
    { path: '/release/:productKey', name: 'release-product-entry', component: ReleaseProductEntryView, meta: { layout: 'shell' } },
    { path: '/release/operator', name: 'release-operator', component: ReleaseOperatorView, meta: { layout: 'shell' } },
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
