import type { LocationQueryRaw } from 'vue-router';

type QueryLike = LocationQueryRaw;
type SceneRouteSource = {
  route?: unknown;
  label?: unknown;
  default_sort?: unknown;
  target?: {
    route?: unknown;
    menu_id?: unknown;
    action_id?: unknown;
    default_order?: unknown;
    order?: unknown;
  };
};

type CanonicalSceneRouteOptions = {
  scene?: SceneRouteSource | null;
  query?: QueryLike;
  menuId?: unknown;
  actionId?: unknown;
  sceneLabel?: unknown;
  order?: unknown;
};

type EntryTargetRouteOptions = {
  query?: QueryLike;
  menuId?: unknown;
  actionId?: unknown;
  keepSceneRoute?: boolean;
  routePath?: string;
};

const SCENE_QUERY_KEYS = ['scene', 'scene_key', 'sceneKey'] as const;
const WORKBENCH_PATH = '/workbench';

export function firstQueryValue(raw: unknown): string {
  if (Array.isArray(raw)) {
    return raw.length ? String(raw[0] ?? '').trim() : '';
  }
  return String(raw ?? '').trim();
}

export function parseSceneKeyFromQuery(query: QueryLike): string {
  for (const key of SCENE_QUERY_KEYS) {
    const raw = firstQueryValue(query[key]);
    if (!raw) continue;
    const [scene] = raw.split('?', 2);
    const normalized = String(scene || '').trim();
    if (normalized) return normalized;
  }
  return '';
}

export function normalizeEmbeddedSceneQuery(query: QueryLike): { query: QueryLike; changed: boolean } {
  const nextQuery: QueryLike = { ...query };
  let changed = false;
  for (const key of SCENE_QUERY_KEYS) {
    const raw = firstQueryValue(nextQuery[key]);
    if (!raw || !raw.includes('?')) continue;
    const [sceneValue, nestedQuery] = raw.split('?', 2);
    const normalizedScene = String(sceneValue || '').trim();
    if (normalizedScene && normalizedScene !== raw) {
      nextQuery[key] = normalizedScene;
      changed = true;
    }
    if (!nestedQuery) continue;
    const params = new URLSearchParams(nestedQuery);
    params.forEach((value, nestedKey) => {
      const existing = firstQueryValue(nextQuery[nestedKey]);
      if (!existing && value) {
        nextQuery[nestedKey] = value;
        changed = true;
      }
    });
  }
  return { query: nextQuery, changed };
}

export function normalizeLegacyWorkbenchPath(rawPath: string): string {
  const candidate = String(rawPath || '').trim();
  if (!candidate.startsWith(WORKBENCH_PATH)) {
    return candidate;
  }
  const [pathname, queryString = ''] = candidate.split('?', 2);
  if (pathname !== WORKBENCH_PATH) {
    return candidate;
  }
  if (!queryString) {
    return '/';
  }
  const params = new URLSearchParams(queryString);
  const reason = firstQueryValue(params.get('reason'));
  if (reason) {
    return candidate;
  }

  let sceneKey = '';
  for (const key of SCENE_QUERY_KEYS) {
    const current = firstQueryValue(params.get(key));
    if (!current) continue;
    sceneKey = current.split('?', 2)[0]?.trim() || '';
    if (sceneKey) break;
  }

  for (const key of SCENE_QUERY_KEYS) {
    params.delete(key);
  }
  const nestedQuery = params.toString();
  if (!sceneKey) {
    return nestedQuery ? `/?${nestedQuery}` : '/';
  }
  return nestedQuery ? `/s/${sceneKey}?${nestedQuery}` : `/s/${sceneKey}`;
}

function positiveInteger(value: unknown): number | undefined {
  const parsed = Number(value || 0);
  if (!Number.isFinite(parsed) || parsed <= 0) return undefined;
  return Math.trunc(parsed);
}

function compactQuery(query: QueryLike): LocationQueryRaw {
  const next: LocationQueryRaw = {};
  Object.entries(query || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    next[key] = value as LocationQueryRaw[string];
  });
  return next;
}

function entryTargetRefs(entryTarget: Record<string, unknown> | null | undefined): Record<string, unknown> {
  const refs = entryTarget?.compatibility_refs;
  return refs && typeof refs === 'object' && !Array.isArray(refs)
    ? refs as Record<string, unknown>
    : {};
}

function entryTargetRecordEntry(entryTarget: Record<string, unknown> | null | undefined): Record<string, unknown> {
  const recordEntry = entryTarget?.record_entry;
  return recordEntry && typeof recordEntry === 'object' && !Array.isArray(recordEntry)
    ? recordEntry as Record<string, unknown>
    : {};
}

export function entryTargetType(entryTarget: Record<string, unknown> | null | undefined): string {
  return String(entryTarget?.type || '').trim();
}

export function entryTargetSceneKey(entryTarget: Record<string, unknown> | null | undefined): string {
  return entryTargetType(entryTarget) === 'scene'
    ? String(entryTarget?.scene_key || '').trim()
    : '';
}

export function entryTargetActionId(entryTarget: Record<string, unknown> | null | undefined): number | undefined {
  const refs = entryTargetRefs(entryTarget);
  const recordEntry = entryTargetRecordEntry(entryTarget);
  return positiveInteger(refs.action_id) ?? positiveInteger(recordEntry.action_id);
}

export function resolveCanonicalScenePath(sceneKey: string, scene?: SceneRouteSource | null): string {
  const key = String(sceneKey || '').trim();
  const rawPath = String(scene?.target?.route || scene?.route || '').trim();
  const normalized = normalizeLegacyWorkbenchPath(rawPath);
  const pathOnly = normalized.split('?', 2)[0] || '';
  if (key && pathOnly === `/s/${key}`) return pathOnly;
  return key ? `/s/${key}` : '/';
}

export function resolveSceneDefaultOrder(sceneKey: string, scene?: SceneRouteSource | null): string {
  void sceneKey;
  const explicit = String(scene?.default_sort || '').trim();
  if (explicit) return explicit;
  const targetOrder = String(scene?.target?.default_order || scene?.target?.order || '').trim();
  if (targetOrder) return targetOrder;
  return '';
}

export function buildCanonicalSceneRouteTarget(sceneKey: string, options: CanonicalSceneRouteOptions = {}) {
  const key = String(sceneKey || '').trim();
  const normalizedQuery = normalizeEmbeddedSceneQuery(options.query || {}).query;
  const query: LocationQueryRaw = { ...normalizedQuery };
  for (const queryKey of SCENE_QUERY_KEYS) {
    delete query[queryKey];
  }
  const scene = options.scene || null;
  const menuId = positiveInteger(options.menuId) ?? positiveInteger(scene?.target?.menu_id);
  const actionId = positiveInteger(options.actionId) ?? positiveInteger(scene?.target?.action_id);
  const sceneLabel = String(options.sceneLabel || scene?.label || '').trim();
  const explicitOrder = firstQueryValue(query.order) || firstQueryValue(query.sort);
  const order = String(options.order || explicitOrder || resolveSceneDefaultOrder(key, scene)).trim();

  return {
    path: resolveCanonicalScenePath(key, scene),
    query: compactQuery({
      ...query,
      scene_key: key || undefined,
      menu_id: menuId,
      action_id: actionId,
      scene_label: sceneLabel || undefined,
      order: order || undefined,
    }),
  };
}

export function buildEntryTargetRouteTarget(
  entryTarget: Record<string, unknown> | null | undefined,
  options: EntryTargetRouteOptions = {},
) {
  const type = entryTargetType(entryTarget);
  const normalizedQuery = normalizeEmbeddedSceneQuery(options.query || {}).query;
  const refs = entryTargetRefs(entryTarget);
  const menuId = positiveInteger(options.menuId) ?? positiveInteger(refs.menu_id);
  const actionId = positiveInteger(options.actionId) ?? entryTargetActionId(entryTarget);
  const domainRaw = firstQueryValue(normalizedQuery.domain_raw) || firstQueryValue(refs.domain_raw);
  const contextRaw = firstQueryValue(normalizedQuery.context_raw) || firstQueryValue(refs.context_raw);
  if (type === 'scene') {
    const sceneKey = entryTargetSceneKey(entryTarget);
    return buildCanonicalSceneRouteTarget(sceneKey, {
      query: normalizedQuery,
      menuId,
      actionId,
      sceneLabel: entryTarget?.scene_label,
    });
  }
  const query = compactQuery({
    ...normalizedQuery,
    menu_id: menuId,
    action_id: actionId,
    domain_raw: domainRaw || undefined,
    context_raw: contextRaw || undefined,
  });
  const route = String(entryTarget?.route || '').trim();
  if (type === 'compatibility' && route && !actionId) {
    return { path: route, query };
  }
  if (options.keepSceneRoute && options.routePath) {
    return { path: options.routePath, query };
  }
  return {
    name: 'action',
    params: { actionId: actionId || 0 },
    query,
  };
}
