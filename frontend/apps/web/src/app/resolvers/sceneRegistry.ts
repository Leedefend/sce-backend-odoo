import { validateSceneRegistry } from './sceneRegistryCore';

export interface SceneTarget {
  menu_id?: number;
  menu_xmlid?: string;
  action_id?: number;
  action_xmlid?: string;
  model?: string;
  view_mode?: string;
  record_id?: number | string;
  route?: string;
}

export interface SceneTile {
  key?: string;
  title?: string;
  subtitle?: string;
  icon?: string;
  status?: string;
  state?: 'READY' | 'LOCKED' | 'PREVIEW' | string;
  reason?: string;
  reason_code?: string;
  route?: string;
  intent?: string;
  payload?: Record<string, unknown>;
  capabilities?: string[];
  required_capabilities?: string[];
  requiredCapabilities?: string[];
}

export interface SceneListProfile {
  columns?: string[];
  hidden_columns?: string[];
  column_labels?: Record<string, string>;
  row_primary?: string;
  row_secondary?: string;
}

export interface SceneLayout {
  kind: 'list' | 'record' | 'workspace' | 'ledger';
  sidebar: 'fixed' | 'scroll';
  header: 'compact' | 'full';
}

export interface Scene {
  key: string;
  label: string;
  icon?: string;
  route: string;
  target: SceneTarget;
  validation_surface?: Record<string, unknown>;
  capabilities?: string[];
  breadcrumbs?: Array<{ label: string; to?: string }>;
  tiles?: SceneTile[];
  list_profile?: SceneListProfile;
  filters?: unknown[];
  default_sort?: string;
  scene_ready?: {
    search_surface?: Record<string, unknown>;
    permission_surface?: Record<string, unknown>;
    action_surface?: Record<string, unknown>;
    workflow_surface?: Record<string, unknown>;
    actions?: Array<Record<string, unknown>>;
  };
  layout?: SceneLayout;
}

export const DEFAULT_SCENE_LAYOUT: SceneLayout = {
  kind: 'workspace',
  sidebar: 'fixed',
  header: 'full',
};

let sceneRegistry: Scene[] = [];
let errors: Array<{ index: number; key?: string | null; route?: string | null; issues: string[] }> = [];

const SCENE_ROUTE_OVERRIDES: Record<string, string> = {
  'my_work.workspace': '/my-work',
};

const NATIVE_UI_CONTRACT_ROUTE_PREFIXES = ['/a/', '/f/', '/r/'];

function resolveSceneRoute(code: string, route: string): string {
  const override = SCENE_ROUTE_OVERRIDES[code];
  if (override) return override;
  return route;
}

function normalizeDeliverySceneRoute(sceneKey: string, route: string): string {
  const raw = String(route || '').trim();
  if (!raw) return `/s/${sceneKey}`;
  const lowered = raw.toLowerCase();
  if (NATIVE_UI_CONTRACT_ROUTE_PREFIXES.some((prefix) => lowered.startsWith(prefix))) {
    return `/s/${sceneKey}`;
  }
  return raw;
}

function normalizeSceneLayout(layout?: Partial<SceneLayout> | null): SceneLayout {
  if (!layout || typeof layout !== 'object') {
    return { ...DEFAULT_SCENE_LAYOUT };
  }
  return {
    kind: layout?.kind ?? DEFAULT_SCENE_LAYOUT.kind,
    sidebar: layout?.sidebar ?? DEFAULT_SCENE_LAYOUT.sidebar,
    header: layout?.header ?? DEFAULT_SCENE_LAYOUT.header,
  };
}

function coerceSceneSource(source: Scene[]) {
  return source
    .map((scene) => {
      if (scene && typeof scene === 'object' && 'key' in scene && 'route' in scene) {
        return { ...scene, layout: normalizeSceneLayout(scene.layout) };
      }
      const raw = scene as unknown as {
        code?: string;
        name?: string;
        route?: string;
        target?: SceneTarget;
        layout?: Partial<SceneLayout>;
        icon?: string;
        capabilities?: string[];
        breadcrumbs?: Array<{ label: string; to?: string }>;
        tiles?: SceneTile[];
        list_profile?: SceneListProfile;
        filters?: unknown[];
        default_sort?: string;
      };
      if (raw?.code) {
        const route = resolveSceneRoute(raw.code, raw.route || `/s/${raw.code}`);
        const target =
          raw.target && typeof raw.target === 'object' && (
            raw.target.action_id ||
            raw.target.menu_id ||
            raw.target.model ||
            raw.target.route
          )
            ? {
                ...raw.target,
                route: resolveSceneRoute(raw.code, String(raw.target.route || route)),
              }
            : { route };
        return {
          key: raw.code,
          label: raw.name || raw.code,
          icon: raw.icon,
          route,
          target,
          capabilities: raw.capabilities ?? [],
          breadcrumbs: raw.breadcrumbs ?? [],
          tiles: raw.tiles ?? [],
          list_profile: raw.list_profile,
          filters: raw.filters,
          default_sort: raw.default_sort,
          layout: normalizeSceneLayout(raw.layout),
        } as Scene;
      }
      return null;
    })
    .filter((scene): scene is Scene => Boolean(scene));
}

function buildSceneRegistry(source: Scene[]) {
  const normalized = coerceSceneSource(source);
  const validation = validateSceneRegistry(normalized as Scene[]);
  const nextErrors = validation.errors as Array<{ index: number; key?: string | null; route?: string | null; issues: string[] }>;
  if (nextErrors.length) {
    // eslint-disable-next-line no-console
    console.warn('[scene-registry] invalid scenes detected', nextErrors);
  }
  errors = nextErrors;
  sceneRegistry = validation.validScenes as Scene[];
  return sceneRegistry;
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function toSceneFromSceneReadyEntry(entry: unknown): Scene | null {
  if (!entry || typeof entry !== 'object') {
    return null;
  }
  const row = entry as Record<string, unknown>;
  const sceneRow = (row.scene && typeof row.scene === 'object') ? row.scene as Record<string, unknown> : {};
  const pageRow = (row.page && typeof row.page === 'object') ? row.page as Record<string, unknown> : {};
  const metaRow = (row.meta && typeof row.meta === 'object') ? row.meta as Record<string, unknown> : {};
  const targetRow = (metaRow.target && typeof metaRow.target === 'object') ? metaRow.target as Record<string, unknown> : {};
  const permissionRow = (row.permission_surface && typeof row.permission_surface === 'object')
    ? row.permission_surface as Record<string, unknown>
    : {};
  const validationRow = (row.validation_surface && typeof row.validation_surface === 'object')
    ? row.validation_surface as Record<string, unknown>
    : ((metaRow.validation_surface && typeof metaRow.validation_surface === 'object')
      ? metaRow.validation_surface as Record<string, unknown>
      : {});
  const searchRow = (row.search_surface && typeof row.search_surface === 'object')
    ? row.search_surface as Record<string, unknown>
    : {};
  const actionsRow = Array.isArray(row.actions)
    ? row.actions as Array<Record<string, unknown>>
    : [];
  const actionSurfaceRow = (row.action_surface && typeof row.action_surface === 'object')
    ? row.action_surface as Record<string, unknown>
    : {};
  const workflowRow = (row.workflow_surface && typeof row.workflow_surface === 'object')
    ? row.workflow_surface as Record<string, unknown>
    : {};
  const blockRows = Array.isArray(row.blocks)
    ? row.blocks as Array<Record<string, unknown>>
    : [];

  const sceneKey = asText(sceneRow.key || pageRow.scene_key);
  if (!sceneKey) {
    return null;
  }
  const defaultRoute = `/s/${sceneKey}`;
  const resolvedRoute = resolveSceneRoute(sceneKey, asText(pageRow.route) || asText(targetRow.route) || defaultRoute);
  const route = normalizeDeliverySceneRoute(sceneKey, resolvedRoute);
  const actionId = Number(targetRow.action_id || 0);
  const menuId = Number(targetRow.menu_id || 0);
  const requiredCapabilities = Array.isArray(permissionRow.required_capabilities)
    ? permissionRow.required_capabilities.map((item) => asText(item)).filter(Boolean)
    : [];
  const listColumns = blockRows
    .map((item) => {
      const fields = Array.isArray(item.fields) ? item.fields : [];
      return fields
        .map((field) => {
          if (typeof field === 'string') return asText(field);
          if (field && typeof field === 'object') {
            const payload = field as Record<string, unknown>;
            return asText(payload.name || payload.field || payload.key);
          }
          return '';
        })
        .filter(Boolean);
    })
    .find((cols) => cols.length > 0) || [];
  const searchFilters = Array.isArray(searchRow.filters) ? searchRow.filters : [];
  const defaultSort = asText(searchRow.default_sort);

  const target: SceneTarget = {
    route,
    action_id: actionId > 0 ? actionId : undefined,
    menu_id: menuId > 0 ? menuId : undefined,
    model: asText(targetRow.model) || undefined,
    view_mode: asText(targetRow.view_mode) || undefined,
  };

  return {
    key: sceneKey,
    label: asText(sceneRow.title) || sceneKey,
    route,
    target,
    validation_surface: validationRow,
    capabilities: requiredCapabilities,
    list_profile: {
      columns: listColumns,
    },
    filters: searchFilters,
    default_sort: defaultSort,
    scene_ready: {
      search_surface: searchRow,
      permission_surface: permissionRow,
      action_surface: actionSurfaceRow,
      workflow_surface: workflowRow,
      actions: actionsRow,
    },
    layout: normalizeSceneLayout(),
  };
}

function scenesFromSceneReadyContract(contract?: { scenes?: unknown[] } | null): Scene[] {
  const rows = Array.isArray(contract?.scenes) ? contract?.scenes : [];
  return rows
    .map((entry) => toSceneFromSceneReadyEntry(entry))
    .filter((entry): entry is Scene => Boolean(entry));
}

buildSceneRegistry([]);

export function getSceneRegistryDiagnostics() {
  return { errors };
}

export function setSceneRegistry(scenes?: Scene[] | null) {
  const source = Array.isArray(scenes) ? scenes : [];
  return buildSceneRegistry(source);
}

export function setSceneRegistryFromSceneReadyContract(contract?: { scenes?: unknown[] } | null) {
  const source = scenesFromSceneReadyContract(contract);
  return buildSceneRegistry(source);
}

export function getSceneByKey(key: string) {
  return sceneRegistry.find((scene) => scene.key === key) || null;
}

export function getSceneRegistry() {
  return sceneRegistry;
}

export function resolveSceneLayout(scene?: Scene | null) {
  return normalizeSceneLayout(scene?.layout);
}
