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
  entry_target?: SceneEntryTarget;
}

export interface SceneEntryTarget {
  type?: string;
  scene_key?: string;
  route?: string;
  compatibility_refs?: Record<string, unknown>;
  context?: Record<string, unknown>;
  record_entry?: SceneRecordEntry;
}

export interface SceneRecordEntry {
  model?: string;
  record_id?: number | string;
  action_id?: number;
  menu_id?: number;
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

export interface ScenePage {
  key?: string;
  title?: string;
  page_type?: string;
  layout_mode?: string;
  render_mode?: string;
  scene_key?: string;
}

export interface Scene {
  key: string;
  label: string;
  icon?: string;
  route: string;
  target: SceneTarget;
  page?: ScenePage;
  validation_surface?: Record<string, unknown>;
  capabilities?: string[];
  breadcrumbs?: Array<{ label: string; to?: string }>;
  tiles?: SceneTile[];
  scene_ready?: {
    search_surface?: Record<string, unknown>;
    permission_surface?: Record<string, unknown>;
    action_surface?: Record<string, unknown>;
    workflow_surface?: Record<string, unknown>;
    switch_surface?: Record<string, unknown>;
    product_delivery_surface?: Record<string, unknown>;
    actions?: Array<Record<string, unknown>>;
  };
  layout?: SceneLayout;
}

export const DEFAULT_SCENE_LAYOUT: SceneLayout = {
  kind: 'workspace',
  sidebar: 'fixed',
  header: 'full',
};
const SCENE_REGISTRY_RUNTIME_VERSION = '2026-03-29-restore-cutoff';

let sceneRegistry: Scene[] = [];
let sceneAliases: Record<string, string> = {};
let errors: Array<{ index: number; key?: string | null; route?: string | null; issues: string[] }> = [];

const SCENE_ROUTE_OVERRIDES: Record<string, string> = {
  'my_work.workspace': '/my-work',
};

const UNIFIED_HOME_SCENE_KEYS = new Set(['workspace.home', 'portal.dashboard', 'my_work.workspace']);
const UNIFIED_HOME_ROUTES = new Set(['/', '/my-work', '/s/workspace.home', '/s/portal.dashboard']);

function resolveSceneRoute(code: string, route: string): string {
  const override = SCENE_ROUTE_OVERRIDES[code];
  if (override) return override;
  return route;
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

function isUnifiedHomeSceneKey(sceneKey: string): boolean {
  return UNIFIED_HOME_SCENE_KEYS.has(String(sceneKey || '').trim().toLowerCase());
}

function isUnifiedHomeRoute(route: string): boolean {
  return UNIFIED_HOME_ROUTES.has(String(route || '').trim().toLowerCase());
}

function choosePreferredScene(existing: Scene, incoming: Scene): Scene {
  if (existing.key === 'workspace.home' || incoming.key !== 'workspace.home') {
    return existing;
  }
  return incoming;
}

function dedupeSceneAliases(source: Scene[]): { scenes: Scene[]; aliases: Record<string, string> } {
  const aliases: Record<string, string> = {};
  const deduped: Scene[] = [];
  const routeIndex = new Map<string, number>();

  source.forEach((scene) => {
    const route = String(scene.route || '').trim().toLowerCase();
    const existingIndex = routeIndex.get(route);
    if (existingIndex === undefined) {
      deduped.push(scene);
      routeIndex.set(route, deduped.length - 1);
      return;
    }

    const existing = deduped[existingIndex];
    const homeAliasCollision =
      isUnifiedHomeRoute(route)
      || isUnifiedHomeSceneKey(existing.key)
      || isUnifiedHomeSceneKey(scene.key);

    if (!homeAliasCollision) {
      deduped.push(scene);
      return;
    }

    const preferred = choosePreferredScene(existing, scene);
    const dropped = preferred.key === existing.key ? scene : existing;
    deduped[existingIndex] = preferred;
    aliases[dropped.key] = preferred.key;
  });

  return { scenes: deduped, aliases };
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
        title?: string;
        label?: string;
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
            raw.target.route ||
            raw.target.entry_target
          )
            ? {
                ...raw.target,
                route: resolveSceneRoute(raw.code, String(raw.target.route || route)),
                entry_target: readSceneEntryTarget((raw.target as Record<string, unknown>).entry_target),
              }
            : { route };
        return {
          key: raw.code,
          label: raw.name || raw.title || raw.label || raw.code,
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
  const deduped = dedupeSceneAliases(normalized as Scene[]);
  const validation = validateSceneRegistry(deduped.scenes as Scene[]);
  const nextErrors = validation.errors as Array<{ index: number; key?: string | null; route?: string | null; issues: string[] }>;
  if (nextErrors.length && import.meta.env.DEV) {
    const flattened = nextErrors.map((item) => ({
      index: item.index,
      key: item.key ?? null,
      route: item.route ?? null,
      issues: [...item.issues],
    }));
    // eslint-disable-next-line no-console
    console.warn('[scene-registry] invalid scenes detected', {
      version: SCENE_REGISTRY_RUNTIME_VERSION,
      count: flattened.length,
      issues: flattened,
    });
  }
  sceneAliases = deduped.aliases;
  errors = nextErrors;
  sceneRegistry = validation.validScenes as Scene[];
  return sceneRegistry;
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function asNumber(value: unknown): number {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
}

function asRecord(value: unknown): Record<string, unknown> {
  return (value && typeof value === 'object' && !Array.isArray(value))
    ? value as Record<string, unknown>
    : {};
}

function normalizeRouteValue(route: unknown): string {
  return asText(route).toLowerCase();
}

function isLegacyCompatRoute(route: unknown): boolean {
  const normalized = normalizeRouteValue(route);
  return (
    normalized.startsWith('/compat/action/')
    || normalized.startsWith('/compat/form/')
    || normalized.startsWith('/compat/record/')
  );
}

function normalizeViewModeValue(viewMode: unknown): string {
  return asText(viewMode).toLowerCase();
}

function readSceneEntryTarget(raw: unknown): SceneEntryTarget | undefined {
  const payload = asRecord(raw);
  if (!Object.keys(payload).length) {
    return undefined;
  }
  const compatibilityRefs = asRecord(payload.compatibility_refs);
  const context = asRecord(payload.context);
  const recordEntry = asRecord(payload.record_entry);
  return {
    type: asText(payload.type) || undefined,
    scene_key: asText(payload.scene_key) || undefined,
    route: asText(payload.route) || undefined,
    compatibility_refs: Object.keys(compatibilityRefs).length ? compatibilityRefs : undefined,
    context: Object.keys(context).length ? context : undefined,
    record_entry: Object.keys(recordEntry).length ? {
      model: asText(recordEntry.model) || undefined,
      record_id: recordEntry.record_id as number | string | undefined,
      action_id: asNumber(recordEntry.action_id) || undefined,
      menu_id: asNumber(recordEntry.menu_id) || undefined,
    } : undefined,
  };
}

function targetRefs(target?: SceneTarget | null) {
  const entryTarget = target?.entry_target;
  return {
    entryTarget,
    compatibilityRefs: asRecord(entryTarget?.compatibility_refs),
    context: asRecord(entryTarget?.context),
    recordEntry: entryTarget?.record_entry,
  };
}

function targetNumberCandidates(target: SceneTarget | undefined, field: 'action_id' | 'menu_id') {
  const refs = targetRefs(target);
  return [
    asNumber(target?.[field]),
    asNumber(refs.compatibilityRefs[field]),
    asNumber(refs.context[field]),
    field === 'action_id' ? asNumber(refs.recordEntry?.action_id) : asNumber(refs.recordEntry?.menu_id),
  ].filter((value) => value > 0);
}

function targetRecordIdCandidates(target: SceneTarget | undefined) {
  const refs = targetRefs(target);
  return [
    asNumber(target?.record_id),
    asNumber(refs.compatibilityRefs.record_id),
    asNumber(refs.context.record_id),
    asNumber(refs.recordEntry?.record_id),
  ].filter((value) => value > 0);
}

function targetTextCandidates(
  target: SceneTarget | undefined,
  field: 'model' | 'view_mode' | 'route',
) {
  const refs = targetRefs(target);
  const normalize = field === 'view_mode'
    ? normalizeViewModeValue
    : (field === 'route' ? normalizeRouteValue : asText);
  return [
    normalize(target?.[field]),
    normalize(refs.compatibilityRefs[field]),
    normalize(refs.context[field]),
    field === 'model' ? asText(refs.recordEntry?.model) : '',
    field === 'route' ? normalizeRouteValue(refs.entryTarget?.route) : '',
  ].filter(Boolean);
}

function sceneAuthorityKeyCandidates(scene: Scene) {
  return [
    asText(scene.key),
    asText(scene.target?.entry_target?.scene_key),
  ].filter(Boolean);
}

function sceneMatchesEntryAuthority(
  scene: Scene,
  authority: {
    sceneKey?: unknown;
    actionId?: unknown;
    menuId?: unknown;
    recordId?: unknown;
    model?: unknown;
    viewMode?: unknown;
    route?: unknown;
  },
) {
  const sceneKey = asText(authority.sceneKey);
  const actionId = asNumber(authority.actionId);
  const menuId = asNumber(authority.menuId);
  const recordId = asNumber(authority.recordId);
  const model = asText(authority.model);
  const viewMode = normalizeViewModeValue(authority.viewMode);
  const route = normalizeRouteValue(authority.route);

  if (sceneKey) {
    return sceneAuthorityKeyCandidates(scene).includes(sceneKey);
  }
  if (actionId > 0 && !targetNumberCandidates(scene.target, 'action_id').includes(actionId)) {
    return false;
  }
  if (menuId > 0 && !targetNumberCandidates(scene.target, 'menu_id').includes(menuId)) {
    return false;
  }
  if (recordId > 0 && !targetRecordIdCandidates(scene.target).includes(recordId)) {
    return false;
  }
  if (model && !targetTextCandidates(scene.target, 'model').includes(model)) {
    return false;
  }
  if (viewMode && !targetTextCandidates(scene.target, 'view_mode').includes(viewMode)) {
    return false;
  }
  if (route && !targetTextCandidates(scene.target, 'route').includes(route) && normalizeRouteValue(scene.route) !== route) {
    return false;
  }
  return actionId > 0 || menuId > 0 || recordId > 0 || Boolean(model) || Boolean(viewMode) || Boolean(route);
}

function toSceneFromSceneReadyEntry(entry: unknown): Scene | null {
  if (!entry || typeof entry !== 'object') {
    return null;
  }
  const row = entry as Record<string, unknown>;
  const sceneRow = (row.scene && typeof row.scene === 'object') ? row.scene as Record<string, unknown> : {};
  const pageRow = (row.page && typeof row.page === 'object') ? row.page as Record<string, unknown> : {};
  const layoutRow = (row.layout && typeof row.layout === 'object') ? row.layout as Record<string, unknown> : {};
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
  const switchSurfaceRow = (row.switch_surface && typeof row.switch_surface === 'object')
    ? row.switch_surface as Record<string, unknown>
    : {};
  const productDeliverySurfaceRow = (row.product_delivery_surface && typeof row.product_delivery_surface === 'object')
    ? row.product_delivery_surface as Record<string, unknown>
    : {};
  const blockRows = Array.isArray(row.blocks)
    ? row.blocks as Array<Record<string, unknown>>
    : [];

  const sceneKey = asText(sceneRow.key || pageRow.scene_key);
  const fallbackSceneKey = asText(sceneRow.scene_key || pageRow.key || metaRow.scene_key);
  const resolvedSceneKey = sceneKey || fallbackSceneKey;
  if (!resolvedSceneKey) {
    return null;
  }
  const entryTarget = readSceneEntryTarget(targetRow.entry_target);
  const defaultRoute = `/s/${resolvedSceneKey}`;
  const publicEntryRoute = asText(entryTarget?.route);
  const legacyRoute = asText(pageRow.route) || asText(targetRow.route);
  const rawRoute = publicEntryRoute || legacyRoute || defaultRoute;
  const resolvedRoute = resolveSceneRoute(resolvedSceneKey, rawRoute);
  const route = publicEntryRoute
    ? resolvedRoute
    : (isLegacyCompatRoute(legacyRoute) ? defaultRoute : resolvedRoute);
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
  const target: SceneTarget = {
    route,
    action_id: actionId > 0 ? actionId : undefined,
    menu_id: menuId > 0 ? menuId : undefined,
    model: asText(targetRow.model) || undefined,
    view_mode: asText(targetRow.view_mode) || undefined,
    entry_target: entryTarget,
  };
  const page: ScenePage = {
    key: asText(pageRow.key) || undefined,
    title: asText(pageRow.title) || undefined,
    page_type: asText(pageRow.page_type) || undefined,
    layout_mode: asText(pageRow.layout_mode) || undefined,
    render_mode: asText(pageRow.render_mode) || undefined,
    scene_key: asText(pageRow.scene_key) || undefined,
  };
  const rawLayoutKind = asText(layoutRow.kind);
  const normalizedLayoutKind =
    rawLayoutKind === 'list' || rawLayoutKind === 'record' || rawLayoutKind === 'workspace' || rawLayoutKind === 'ledger'
      ? rawLayoutKind
      : undefined;
  const rawLayoutSidebar = asText(layoutRow.sidebar);
  const normalizedLayoutSidebar =
    rawLayoutSidebar === 'fixed' || rawLayoutSidebar === 'scroll'
      ? rawLayoutSidebar
      : undefined;
  const rawLayoutHeader = asText(layoutRow.header);
  const normalizedLayoutHeader =
    rawLayoutHeader === 'compact' || rawLayoutHeader === 'full'
      ? rawLayoutHeader
      : undefined;

  return {
    key: resolvedSceneKey,
    label: asText(sceneRow.title || sceneRow.label || pageRow.title || pageRow.label || metaRow.label) || resolvedSceneKey,
    route,
    target,
    page,
    validation_surface: validationRow,
    capabilities: requiredCapabilities,
    scene_ready: {
      search_surface: searchRow,
      permission_surface: permissionRow,
      action_surface: actionSurfaceRow,
      workflow_surface: workflowRow,
      switch_surface: switchSurfaceRow,
      product_delivery_surface: productDeliverySurfaceRow,
      actions: actionsRow,
    },
    layout: normalizeSceneLayout({
      kind: normalizedLayoutKind,
      sidebar: normalizedLayoutSidebar,
      header: normalizedLayoutHeader,
    }),
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
  const normalizedKey = String(key || '').trim();
  const resolvedKey = sceneAliases[normalizedKey] || normalizedKey;
  return sceneRegistry.find((scene) => scene.key === resolvedKey) || null;
}

export function getSceneRegistry() {
  return sceneRegistry;
}

export function findSceneByEntryAuthority(authority: {
  sceneKey?: unknown;
  actionId?: unknown;
  menuId?: unknown;
  recordId?: unknown;
  model?: unknown;
  viewMode?: unknown;
  route?: unknown;
}) {
  const sceneKey = asText(authority.sceneKey);
  if (sceneKey) {
    return getSceneByKey(sceneKey);
  }
  const matches = sceneRegistry.filter((scene) => sceneMatchesEntryAuthority(scene, authority));
  if (!matches.length) {
    return null;
  }
  const canonicalKeys = new Set(matches.map((scene) => scene.key));
  if (canonicalKeys.size > 1) {
    return null;
  }
  return matches[0] || null;
}

export function resolveSceneLayout(scene?: Scene | null) {
  return normalizeSceneLayout(scene?.layout);
}
