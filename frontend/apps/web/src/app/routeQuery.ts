import type { LocationQueryRaw } from 'vue-router';
import { ErrorCodes } from './error_codes';

type QueryLike = LocationQueryRaw;

const SCENE_QUERY_KEYS = ['scene', 'scene_key', 'sceneKey'] as const;
const EDITION_QUERY_KEYS = ['edition', 'edition_key', 'editionKey'] as const;
const ALLOWED_EDITIONS = new Set(['standard', 'preview']);
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

export function normalizeEditionKey(raw: unknown): string {
  const value = firstQueryValue(raw).toLowerCase();
  return ALLOWED_EDITIONS.has(value) ? value : '';
}

export function parseEditionKeyFromQuery(query: QueryLike): string {
  for (const key of EDITION_QUERY_KEYS) {
    const normalized = normalizeEditionKey(query[key]);
    if (normalized) return normalized;
  }
  return '';
}

export function normalizeEditionQuery(query: QueryLike): { query: QueryLike; changed: boolean } {
  const nextQuery: QueryLike = { ...query };
  let changed = false;
  let resolved = '';
  for (const key of EDITION_QUERY_KEYS) {
    const raw = firstQueryValue(nextQuery[key]);
    if (!raw) continue;
    const normalized = normalizeEditionKey(raw);
    if (!resolved && normalized) {
      resolved = normalized;
    }
    if (!normalized || key !== 'edition') {
      delete nextQuery[key];
      changed = true;
      continue;
    }
    if (normalized !== raw) {
      nextQuery[key] = normalized;
      changed = true;
    }
  }
  if (resolved) {
    if (firstQueryValue(nextQuery.edition) !== resolved) {
      nextQuery.edition = resolved;
      changed = true;
    }
  } else if ('edition' in nextQuery) {
    delete nextQuery.edition;
    changed = true;
  }
  return { query: nextQuery, changed };
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

export function buildSceneRegistryFallbackPath(input: {
  sceneKey: string;
  menuId?: number;
  label?: string;
  diag?: string;
}): string {
  const sceneKey = String(input.sceneKey || '').trim();
  const params = new URLSearchParams();
  params.set('reason', ErrorCodes.CONTRACT_CONTEXT_MISSING);
  if (sceneKey) {
    params.set('scene', sceneKey);
  }
  const menuId = Number(input.menuId || 0);
  if (Number.isFinite(menuId) && menuId > 0) {
    params.set('menu_id', String(menuId));
  }
  const label = String(input.label || '').trim();
  if (label) {
    params.set('label', label);
  }
  params.set('diag', String(input.diag || 'scene_registry_missing').trim() || 'scene_registry_missing');
  return `${WORKBENCH_PATH}?${params.toString()}`;
}
