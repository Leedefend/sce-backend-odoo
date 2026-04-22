import { computed, ref } from 'vue';
import { apiRequestRaw } from '../api/client';
import { findSceneByEntryAuthority } from '../app/resolvers/sceneRegistry';
import type { ExplainedMenuNode, NavigationExplainedPayload } from '../types/navigation';

type Dict = Record<string, unknown>;

const treeState = ref<ExplainedMenuNode[]>([]);
const flatState = ref<ExplainedMenuNode[]>([]);
const loadingState = ref(false);
const loadedState = ref(false);
const errorState = ref<string | null>(null);

function asDict(value: unknown): Dict | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null;
  }
  return value as Dict;
}

function asText(value: unknown): string {
  return String(value || '').trim();
}

function asBool(value: unknown, fallback = false): boolean {
  return typeof value === 'boolean' ? value : fallback;
}

function mergeRouteQuery(route: string, paramsToMerge: Record<string, string | number | undefined>): string {
  const rawRoute = asText(route);
  if (!rawRoute) {
    return '';
  }
  const routeUrl = new URL(rawRoute, 'http://localhost');
  Object.entries(paramsToMerge).forEach(([key, value]) => {
    if (value === undefined || value === null || String(value).trim() === '') {
      return;
    }
    routeUrl.searchParams.set(key, String(value));
  });
  return `${routeUrl.pathname}${routeUrl.search}${routeUrl.hash}`;
}

function buildCanonicalSceneRoute(sceneKey: string, route?: string): string | null {
  const normalizedSceneKey = asText(sceneKey);
  if (!normalizedSceneKey) {
    return null;
  }
  const rawPath = asText(route) || `/s/${normalizedSceneKey}`;
  if (!rawPath) {
    return null;
  }
  const routeUrl = new URL(rawPath, 'http://localhost');
  routeUrl.searchParams.delete('menu_id');
  routeUrl.searchParams.delete('menu_xmlid');
  routeUrl.searchParams.delete('action_id');
  routeUrl.searchParams.delete('scene');
  routeUrl.searchParams.set('scene_key', normalizedSceneKey);
  return `${routeUrl.pathname}${routeUrl.search}${routeUrl.hash}`;
}

function normalizeEntryTarget(raw: unknown): string | null {
  const entryTarget = asDict(raw);
  if (!entryTarget) {
    return null;
  }
  const entryType = asText(entryTarget.type);
  const sceneKey = asText(entryTarget.scene_key);
  const route = asText(entryTarget.route);
  const compatibilityRefs = asDict(entryTarget.compatibility_refs) || {};
  const context = asDict(entryTarget.context) || {};
  const actionId = Number(compatibilityRefs.action_id || context.action_id || 0);

  if (entryType === 'scene' || sceneKey) {
    void actionId;
    return buildCanonicalSceneRoute(sceneKey, route);
  }
  if (entryType === 'compatibility' && route) {
    return normalizeRoute(route);
  }
  return route ? normalizeRoute(route) : null;
}

function normalizeRoute(routeRaw: string): string | null {
  const route = String(routeRaw || '').trim();
  if (!route) {
    return null;
  }
  if (route.startsWith('/native/action/')) {
    const [, actionPart = ''] = route.match(/^\/native\/action\/([^?#]+)/) || [];
    const actionId = Number(actionPart || 0);
    if (Number.isFinite(actionId) && actionId > 0) {
      const scene = findSceneByEntryAuthority({ actionId });
      if (scene) {
        return buildCanonicalSceneRoute(scene.key, scene.route || `/s/${scene.key}`);
      }
      return null;
    }
    return null;
  }
  if (route.startsWith('/s/')) {
    const routeUrl = new URL(route, 'http://localhost');
    const sceneKey = asText(routeUrl.pathname.replace(/^\/s\//, ''));
    if (sceneKey) {
      return buildCanonicalSceneRoute(sceneKey, route);
    }
  }
  return route;
}

function normalizeTargetType(targetTypeRaw: string): ExplainedMenuNode['target_type'] {
  const targetType = asText(targetTypeRaw) as ExplainedMenuNode['target_type'];
  if (
    targetType === 'directory'
    || targetType === 'scene'
    || targetType === 'action'
    || targetType === 'native'
    || targetType === 'url'
    || targetType === 'unavailable'
  ) {
    return targetType;
  }
  return 'unavailable';
}

function pickFirstActionRoute(nodes: ExplainedMenuNode[]): string | null {
  for (const node of nodes) {
    if (node.route && node.is_clickable !== false && node.target_type !== 'unavailable') {
      return node.route;
    }
    if (Array.isArray(node.children) && node.children.length) {
      const nested = pickFirstActionRoute(node.children);
      if (nested) {
        return nested;
      }
    }
  }
  return null;
}

function normalizeNode(raw: unknown, index = 0): ExplainedMenuNode {
  const row = asDict(raw) || {};
  const menuId = Number(row.menu_id || 0) || undefined;
  const key = asText(row.key) || `menu:${menuId || index}`;
  const childrenRaw = Array.isArray(row.children) ? row.children : [];
  const children = childrenRaw.map((child, childIndex) => normalizeNode(child, childIndex));
  const declaredTargetType = normalizeTargetType(asText(row.target_type));
  const deliveryMode = asText(row.delivery_mode) as ExplainedMenuNode['delivery_mode'];
  const displayName = asText(row.name) || asText(row.label) || asText(row.title) || key;
  const rawRoute = asText(row.route);
  const directRoute = normalizeEntryTarget(row.entry_target) || normalizeRoute(rawRoute);
  const unresolvedNativeAction = rawRoute.startsWith('/native/action/') && !directRoute;
  const targetType = unresolvedNativeAction ? 'unavailable' : declaredTargetType;
  const fallbackRoute = targetType === 'directory' || targetType === 'unavailable'
    ? directRoute
    : directRoute || pickFirstActionRoute(children);
  const isClickableRaw = asBool(row.is_clickable, false);
  const isClickable = targetType === 'directory'
    ? children.length > 0
    : targetType === 'unavailable'
      ? false
      : Boolean(fallbackRoute) && isClickableRaw;
  return {
    menu_id: menuId,
    key,
    name: displayName,
    icon: asText(row.icon) || null,
    is_visible: asBool(row.is_visible, true),
    is_clickable: isClickable,
    target_type: targetType,
    delivery_mode: deliveryMode || 'none',
    route: fallbackRoute,
    target: asDict(row.target) || {},
    entry_target: (asDict(row.entry_target) || {}) as ExplainedMenuNode['entry_target'],
    active_match: (asDict(row.active_match) || {}) as ExplainedMenuNode['active_match'],
    availability_status: asText(row.availability_status) || 'blocked',
    reason_code: asText(row.reason_code) || (unresolvedNativeAction ? 'menu_scene_identity_missing' : ''),
    children,
  };
}

export function useNavigationMenu() {
  const tree = computed(() => treeState.value);
  const flat = computed(() => flatState.value);
  const loading = computed(() => loadingState.value);
  const loaded = computed(() => loadedState.value);
  const error = computed(() => errorState.value);

  async function loadNavigation(force = false) {
    if (loadingState.value) return;
    if (loadedState.value && !force) return;
    loadingState.value = true;
    errorState.value = null;
    try {
      const response = await apiRequestRaw<NavigationExplainedPayload>('/api/menu/navigation', {
        method: 'POST',
        body: JSON.stringify({}),
      });
      const body = asDict(response.body) || {};
      if (asDict(body.result) || asText(body.jsonrpc)) {
        throw new Error('menu navigation envelope mismatch: expected custom json envelope');
      }
      const navExplained = asDict(body.nav_explained) || {};
      const treeRows = Array.isArray(navExplained.tree) ? navExplained.tree : [];
      const flatRows = Array.isArray(navExplained.flat) ? navExplained.flat : [];
      if (!treeRows.length) {
        throw new Error('nav_explained empty: formal navigation contract is required');
      }
      treeState.value = treeRows.map((item, index) => normalizeNode(item, index));
      flatState.value = flatRows.map((item, index) => normalizeNode(item, index));
      loadedState.value = true;
      if (!treeState.value.length) {
        errorState.value = 'nav_explained empty';
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'load navigation failed';
      errorState.value = message;
      treeState.value = [];
      flatState.value = [];
      loadedState.value = false;
      throw error;
    } finally {
      loadingState.value = false;
    }
  }

  return {
    tree,
    flat,
    loading,
    loaded,
    error,
    loadNavigation,
  };
}
