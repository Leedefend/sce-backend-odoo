import type { RouteLocationNormalizedLoaded, RouteLocationNormalized } from 'vue-router';
import type { NavNode } from '@sc/schema';
import { findActionMeta, findActionMetaByMenu, findMenuNode } from './menu';
import { getSceneByKey } from './resolvers/sceneRegistry';
import type { PageBreadcrumb, PageIdentityInput } from './pageIdentity';

type RouteLike = RouteLocationNormalized | RouteLocationNormalizedLoaded;

function positiveInteger(value: unknown): number {
  const parsed = Number(Array.isArray(value) ? value[0] : value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : 0;
}

function routeText(value: unknown): string {
  return String(Array.isArray(value) ? value[0] || '' : value || '').trim();
}

function menuLabel(node: NavNode | null): string {
  return String(node?.label || node?.name || node?.title || '').trim();
}

function findMenuPath(nodes: NavNode[], menuId: number, parents: NavNode[] = []): NavNode[] {
  for (const node of nodes) {
    const path = [...parents, node];
    if (Number(node.menu_id || node.id || 0) === menuId) return path;
    const nested = findMenuPath(node.children || [], menuId, path);
    if (nested.length) return nested;
  }
  return [];
}

function menuBreadcrumbs(nodes: NavNode[], menuId: number): PageBreadcrumb[] {
  return findMenuPath(nodes, menuId).map((node) => {
    const id = Number(node.menu_id || node.id || 0);
    const hasTarget = Boolean(node.meta?.action_id || node.meta?.scene_key);
    return { label: menuLabel(node), ...(id > 0 && hasTarget ? { to: `/m/${id}` } : {}) };
  });
}

export function resolveRoutePageIdentity(route: RouteLike, menuTree: NavNode[]): PageIdentityInput {
  const name = String(route.name || '').trim();
  if (name === 'login' || name === 'platform-admin-login') return { fallbackTitle: '登录' };
  if (name === 'access-denied') {
    const from = routeText(route.query.from);
    let targetAction = 0;
    let targetMenu = 0;
    try {
      const target = new URL(from || '/', 'http://page.identity.local');
      targetAction = positiveInteger(target.pathname.match(/^\/a\/(\d+)/)?.[1] || target.searchParams.get('action_id'));
      targetMenu = positiveInteger(target.pathname.match(/^\/m\/(\d+)/)?.[1] || target.searchParams.get('menu_id'));
    } catch {
      // Invalid source URLs are intentionally ignored on the denial surface.
    }
    const targetNode = targetMenu ? findMenuNode(menuTree, targetMenu) : null;
    const targetMeta = (targetMenu ? findActionMetaByMenu(menuTree, targetMenu, targetAction || undefined) : null)
      || (targetAction ? findActionMeta(menuTree, targetAction) : null);
    return {
      actionName: targetMeta?.name,
      menuName: menuLabel(targetNode),
      breadcrumbs: targetMenu ? menuBreadcrumbs(menuTree, targetMenu) : [],
      fallbackTitle: '无权访问',
      state: 'denied',
    };
  }
  if (name === 'not-found') return { fallbackTitle: '记录不存在', state: 'not-found' };
  if (name === 'home' || name === 'scene-home') return { fallbackTitle: '角色首页', breadcrumbs: [{ label: '角色首页' }] };
  if (name === 'my-work' || name === 'scene-my-work') return { fallbackTitle: '我的工作', breadcrumbs: [{ label: '我的工作' }] };

  const menuId = positiveInteger(route.params.menuId || route.query.menu_id);
  const actionId = positiveInteger(route.params.actionId || route.query.action_id);
  const menuNode = menuId ? findMenuNode(menuTree, menuId) : null;
  const action = (menuId ? findActionMetaByMenu(menuTree, menuId, actionId || undefined) : null)
    || (actionId ? findActionMeta(menuTree, actionId) : null);
  const actionName = action?.ui_title || action?.scene_title || action?.menu_title || action?.name;
  const crumbs = menuBreadcrumbs(menuTree, menuId);

  if (name === 'action' || name === 'menu') {
    return {
      kind: 'list',
      actionName,
      menuName: menuLabel(menuNode),
      modelName: action?.model,
      modelLabel: action?.model_label,
      breadcrumbs: crumbs,
    };
  }
  if (name === 'record' || name === 'model-form') {
    const isCreate = routeText(route.params.id) === 'new';
    return {
      kind: isCreate ? 'create' : 'detail',
      actionName,
      menuName: menuLabel(menuNode),
      modelName: route.params.model,
      modelLabel: action?.model_label,
      breadcrumbs: crumbs,
      state: isCreate ? '' : 'loading',
    };
  }
  if (name === 'scene' || name === 'projects-intake' || name.startsWith('scene-')) {
    const sceneKey = routeText(route.params.sceneKey || route.meta?.sceneKey || route.query.scene_key || route.query.scene);
    const scene = sceneKey ? getSceneByKey(sceneKey) : null;
    return { menuName: scene?.label, fallbackTitle: scene?.label || '业务场景', breadcrumbs: crumbs };
  }

  const configured: Record<string, string> = {
    'business-config': '配置工作台',
    'menu-config': '菜单配置',
    'form-field-config': '表单字段配置',
    'scene-health': '场景健康',
    'scene-packages': '场景发布包',
    'usage-analytics': '使用分析',
    'release-operator': '产品发布',
    workbench: '导航异常',
  };
  const title = configured[name] || '工作台';
  return { fallbackTitle: title, breadcrumbs: [{ label: title }] };
}
