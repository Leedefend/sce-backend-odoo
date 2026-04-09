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

function normalizeNode(raw: unknown, index = 0): ExplainedMenuNode {
  const row = asDict(raw) || {};
  const menuId = Number(row.menu_id || 0) || undefined;
  const key = asText(row.key) || `menu:${menuId || index}`;
  const childrenRaw = Array.isArray(row.children) ? row.children : [];
  const targetType = asText(row.target_type) as ExplainedMenuNode['target_type'];
  const deliveryMode = asText(row.delivery_mode) as ExplainedMenuNode['delivery_mode'];
  return {
    menu_id: menuId,
    key,
    name: asText(row.name) || key,
    icon: asText(row.icon) || null,
    is_visible: asBool(row.is_visible, true),
    is_clickable: asBool(row.is_clickable, false),
    target_type: targetType || 'unavailable',
    delivery_mode: deliveryMode || 'none',
    route: asText(row.route) || null,
    target: asDict(row.target) || {},
    active_match: (asDict(row.active_match) || {}) as ExplainedMenuNode['active_match'],
    availability_status: asText(row.availability_status) || 'blocked',
    reason_code: asText(row.reason_code) || '',
    children: childrenRaw.map((child, childIndex) => normalizeNode(child, childIndex)),
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
      const body = response.body || {};
      const navExplained = asDict(body.nav_explained) || {};
      const treeRows = Array.isArray(navExplained.tree) ? navExplained.tree : [];
      const flatRows = Array.isArray(navExplained.flat) ? navExplained.flat : [];
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
