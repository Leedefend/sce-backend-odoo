import type { LocationQueryRaw, LocationQueryValueRaw } from 'vue-router';

export const CONTRACT_NAV_QUERY_KEYS = [
  'menu_id',
  'menu_xmlid',
  'action_id',
  'hud',
  'surface',
  'scene',
  'scene_key',
  'context_raw',
  'preset',
  'preset_filter',
  'search',
  'ctx_source',
] as const;

export function pickContractNavQuery(
  source: Record<string, unknown>,
  extra?: Record<string, unknown>,
) {
  const out: LocationQueryRaw = {};
  const normalize = (value: unknown): LocationQueryValueRaw | LocationQueryValueRaw[] | undefined => {
    if (value === undefined || value === null || value === '') return undefined;
    if (Array.isArray(value)) {
      return value
        .map((item) => (item === undefined || item === null ? '' : String(item)))
        .filter((item) => item !== '');
    }
    if (typeof value === 'boolean') {
      return value ? '1' : '0';
    }
    if (typeof value === 'string' || typeof value === 'number') {
      return value;
    }
    return JSON.stringify(value);
  };
  CONTRACT_NAV_QUERY_KEYS.forEach((key) => {
    const normalized = normalize(source[key]);
    if (normalized !== undefined) {
      out[key] = normalized;
    }
  });
  Object.entries(extra || {}).forEach(([key, value]) => {
    const normalized = normalize(value);
    if (normalized === undefined) {
      delete out[key];
      return;
    }
    out[key] = normalized;
  });
  return out;
}
