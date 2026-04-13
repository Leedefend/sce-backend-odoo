import { computed, ref } from 'vue';
import { apiRequestRaw } from '../api/client';
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

function normalizeRoute(routeRaw: string): string | null {
  const route = String(routeRaw || '').trim();
  if (!route) {
    return null;
  }
  if (route.startsWith('/native/action/')) {
    return route.replace('/native/action/', '/a/');
  }
  return route;
}

function normalizeTargetType(targetTypeRaw: string): ExplainedMenuNode['target_type'] {
  const targetType = asText(targetTypeRaw) as ExplainedMenuNode['target_type'];
  if (targetType === 'native') {
    return 'action';
  }
  if (targetType === 'directory') {
    return 'action';
  }
  if (targetType === 'unavailable') {
    return 'action';
  }
  return targetType || 'unavailable';
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
  const targetType = normalizeTargetType(asText(row.target_type));
  const deliveryMode = asText(row.delivery_mode) as ExplainedMenuNode['delivery_mode'];
  const displayName = asText(row.name) || asText(row.label) || asText(row.title) || key;
  const directRoute = normalizeRoute(asText(row.route));
  const fallbackRoute = directRoute || pickFirstActionRoute(children);
  const isClickableRaw = asBool(row.is_clickable, false);
  const isClickable = Boolean(fallbackRoute) ? true : isClickableRaw;
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
    active_match: (asDict(row.active_match) || {}) as ExplainedMenuNode['active_match'],
    availability_status: asText(row.availability_status) || 'blocked',
    reason_code: asText(row.reason_code) || '',
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
