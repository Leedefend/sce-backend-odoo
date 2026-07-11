import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router';
import { useSessionStore } from '../stores/session';
import LoginView from '../views/LoginView.vue';
import { ApiError } from '../api/client';
import { buildCanonicalSceneRouteTarget, normalizeEmbeddedSceneQuery, normalizeLegacyWorkbenchPath, parseSceneKeyFromQuery } from '../app/routeQuery';
import { getSceneByKey } from '../app/resolvers/sceneRegistry';
import { findActionMeta, findActionMetaByMenu, findActionNodeByModel, findMenuNode } from '../app/menu';
import { config } from '../config';
import { BUSINESS_CONFIG_MODELS } from '../app/businessConfigBoundaries';

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
    workbench: '工作台',
    'scene-health': '场景健康',
    'scene-packages': '场景发布包',
    'usage-analytics': '使用分析',
    'release-operator': '产品发布',
    'business-config': '配置工作台',
    'menu-config': '菜单配置',
    'form-field-config': '表单字段配置',
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

function routeQueryText(value: unknown): string {
  if (Array.isArray(value)) return String(value[0] || '').trim();
  return String(value || '').trim();
}

function buildActivityQuery(to: RouteLocationNormalized, allowedKeys: string[]): string {
  const params = new URLSearchParams();
  allowedKeys.forEach((key) => {
    const raw = to.query[key];
    const values = Array.isArray(raw) ? raw : [raw];
    values.forEach((value) => {
      const text = String(value ?? '').trim();
      if (text) params.append(key, text);
    });
  });
  const text = params.toString();
  return text ? `?${text}` : '';
}

function createActivityInstanceId(): string {
  return `ap_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function resolveActivityRoute(to: RouteLocationNormalized, actionId: number, menuId: number, model: string, recordId: string): string {
  if (to.name === 'action') {
    const query = buildActivityQuery(to, [
      'menu_id',
      'action_id',
      'product_domain',
      'entry_intent',
      'disposition_policy',
      'integration_target',
      'entry_target_policy',
      'business_entry_contract_version',
      'allowed_business_category_codes',
      'default_business_category_code',
      'default_business_category_label',
      'current_business_category_code',
      'current_business_category_label',
    ]);
    return `/a/${actionId}${query}`;
  }
  if (to.name === 'record' || to.name === 'model-form') {
    const query = buildActivityQuery(to, [
      'menu_id',
      'action_id',
      'activity_page_id',
      'current_business_category_code',
      'current_business_category_label',
      'default_business_category_code',
      'default_business_category_label',
    ]);
    const prefix = to.name === 'record' ? '/r' : '/f';
    return `${prefix}/${encodeURIComponent(model)}/${encodeURIComponent(recordId)}${query}`;
  }
  if (to.name === 'scene' || to.name === 'projects-intake' || String(to.name || '').startsWith('scene-')) {
    const query = buildActivityQuery(to, ['menu_id', 'action_id', 'scene_key', 'scene']);
    return `${to.path}${query}`;
  }
  if (to.name === 'my-work') return '/my-work';
  return String(to.path || to.fullPath || '').trim();
}

function activityProjectPart(session: ReturnType<typeof useSessionStore>, policy: string): string {
  const normalizedPolicy = String(policy || '').trim().toLowerCase();
  if (normalizedPolicy === 'global' || normalizedPolicy === 'exempt') return 'global';
  const selectedId = Number(session.projectContext?.selected?.id || 0) || 0;
  return selectedId > 0 ? `project:${selectedId}` : 'all';
}

function currentActionMatches(session: ReturnType<typeof useSessionStore>, actionId: number): boolean {
  const current = session.currentAction as Record<string, unknown> | null;
  if (!current || actionId <= 0) return false;
  return positiveInteger(current.action_id || current.actionId || current.id) === actionId;
}

function resolveActivityRoutePolicy(actionId: number, menuId: number, session: ReturnType<typeof useSessionStore>): string {
  const meta = (menuId > 0 ? findActionMetaByMenu(session.menuTree, menuId, actionId) : null)
    || (actionId > 0 ? findActionMeta(session.menuTree, actionId) : null)
    || (currentActionMatches(session, actionId) ? session.currentAction : null)
    || null;
  return String(meta?.project_scope_policy || meta?.projectScopePolicy || '').trim().toLowerCase();
}

function resolveActivityTitle(to: RouteLocationNormalized, session: ReturnType<typeof useSessionStore>): string {
  const businessLabel = routeQueryText(to.query.current_business_category_label || to.query.default_business_category_label);
  if (businessLabel) return businessLabel;
  if (to.name === 'home' || to.name === 'scene-home') return '角色首页';
  if (to.name === 'my-work' || to.name === 'scene-my-work') return '我的工作';
  if (to.name === 'scene') {
    const sceneKey = routeQueryText(to.params.sceneKey || to.query.scene_key || to.query.scene);
    const scene = sceneKey ? getSceneByKey(sceneKey) : null;
    return String(scene?.label || sceneKey || '业务场景').trim();
  }
  if (to.name === 'action') {
    const actionId = positiveInteger(to.params.actionId || to.query.action_id);
    const menuId = positiveInteger(to.query.menu_id);
    const meta = (menuId > 0 ? findActionMetaByMenu(session.menuTree, menuId, actionId) : null)
      || (actionId > 0 ? findActionMeta(session.menuTree, actionId) : null)
      || (currentActionMatches(session, actionId) ? session.currentAction : null)
      || null;
    const menuNode = menuId > 0 ? findMenuNode(session.menuTree, menuId) : null;
    return String(meta?.ui_title || meta?.scene_title || meta?.menu_title || menuNode?.label || meta?.name || `动作 ${actionId}`).trim();
  }
  if (to.name === 'record' || to.name === 'model-form') {
    const model = routeQueryText(to.params.model);
    const id = routeQueryText(to.params.id);
    if (id === 'new') {
      const actionId = positiveInteger(to.query.action_id);
      const menuId = positiveInteger(to.query.menu_id);
      const meta = (menuId > 0 ? findActionMetaByMenu(session.menuTree, menuId, actionId) : null)
        || (actionId > 0 ? findActionMeta(session.menuTree, actionId) : null)
        || (currentActionMatches(session, actionId) ? session.currentAction : null)
        || null;
      const menuNode = menuId > 0 ? findMenuNode(session.menuTree, menuId) : null;
      const baseTitle = String(meta?.ui_title || meta?.scene_title || meta?.menu_title || menuNode?.label || meta?.name || '').trim();
      return baseTitle ? `新建${baseTitle}` : '新建业务表单';
    }
    return `${model || '记录'} #${id || ''}`.trim();
  }
  return routeTitle(to.name);
}

function registerRouteActivity(to: RouteLocationNormalized) {
  const session = useSessionStore();
  if (!session.token || !session.isReady) return;
  if (to.name === 'login' || to.name === 'platform-admin-login') return;
  if (to.name === 'menu') return;
  if (to.name === 'home' || to.name === 'scene-home') return;
  if (String(to.path || '').startsWith('/admin/')) return;
  if (to.meta?.adminOnly) return;
  const fullPath = String(to.fullPath || '').trim();
  if (!fullPath) return;
  const now = Date.now();
  let key = '';
  let kind: 'menu_action' | 'record_form' | 'scene' | 'workspace' | 'custom' = 'custom';
  let actionId = 0;
  let menuId = 0;
  let model = '';
  let recordId = '';
  let sceneKey = '';
  let projectScopePolicy = '';
  let activityRoute = '';
  if (to.name === 'action') {
    actionId = positiveInteger(to.params.actionId || to.query.action_id);
    menuId = positiveInteger(to.query.menu_id);
    projectScopePolicy = resolveActivityRoutePolicy(actionId, menuId, session);
    key = `action:${actionId}:menu:${menuId}:${activityProjectPart(session, projectScopePolicy)}`;
    kind = 'menu_action';
  } else if (to.name === 'record' || to.name === 'model-form') {
    model = routeQueryText(to.params.model);
    recordId = routeQueryText(to.params.id);
    const activityInstanceId = routeQueryText(to.query.activity_page_id);
    key = recordId === 'new'
      ? `new:${model}:${routeQueryText(to.query.menu_id)}:${activityProjectPart(session, 'current_project')}:${activityInstanceId || now}`
      : `record:${model}:${recordId}`;
    kind = 'record_form';
  } else if (to.name === 'scene' || to.name === 'projects-intake' || String(to.name || '').startsWith('scene-')) {
    sceneKey = routeQueryText(to.params.sceneKey || to.meta?.sceneKey || to.query.scene_key || to.query.scene);
    key = `scene:${sceneKey || String(to.name || 'scene')}:${activityProjectPart(session, 'current_project')}`;
    kind = sceneKey === 'workspace.home' || to.name === 'scene-home' ? 'workspace' : 'scene';
  } else if (to.name === 'home' || to.name === 'my-work') {
    key = `workspace:${String(to.name)}`;
    kind = 'workspace';
  } else {
    key = `route:${String(to.name || to.path)}:${fullPath}`;
  }
  activityRoute = resolveActivityRoute(to, actionId, menuId, model, recordId);
  session.registerActivityPage({
    key,
    title: resolveActivityTitle(to, session),
    route: activityRoute || fullPath,
    kind,
    model: model || undefined,
    action_id: actionId || undefined,
    menu_id: menuId || undefined,
    record_id: recordId || undefined,
    scene_key: sceneKey || undefined,
    project_scope_policy: projectScopePolicy || undefined,
    project_context: session.currentActivityProjectContextSnapshot(),
  });
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
    { path: '/admin/business-config', name: 'business-config', component: () => import('../views/BusinessConfigSurfaceView.vue'), meta: { layout: 'shell' } },
    { path: '/admin/menu-config', name: 'menu-config', component: () => import('../views/MenuConfigView.vue'), meta: { layout: 'shell' } },
    { path: '/admin/form-field-config', name: 'form-field-config', component: () => import('../views/ActionViewShell.vue'), meta: { layout: 'shell' } },
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
  if (to.name === 'form-field-config') {
    const node = findActionNodeByModel(session.menuTree, BUSINESS_CONFIG_MODELS.formFieldPolicy);
    const actionId = positiveInteger(node?.meta?.action_id);
    const menuId = positiveInteger(node?.menu_id || node?.meta?.menu_id);
    if (actionId) {
      return {
        path: `/a/${actionId}`,
        query: menuId ? { menu_id: String(menuId) } : {},
      };
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
  if ((to.name === 'record' || to.name === 'model-form') && routeQueryText(to.params.id) === 'new' && !routeQueryText(to.query.activity_page_id)) {
    return {
      name: to.name,
      params: to.params,
      query: {
        ...to.query,
        activity_page_id: createActivityInstanceId(),
      },
      hash: to.hash,
      replace: true,
    };
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

router.afterEach((to) => {
  registerRouteActivity(to);
});

export default router;
