type QueryLike = Record<string, unknown>;

const SCENE_QUERY_KEYS = ['scene', 'scene_key', 'sceneKey'] as const;

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
