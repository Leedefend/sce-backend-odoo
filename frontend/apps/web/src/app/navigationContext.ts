export const CONTRACT_NAV_QUERY_KEYS = [
  'menu_id',
  'action_id',
  'hud',
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
  const out: Record<string, unknown> = {};
  CONTRACT_NAV_QUERY_KEYS.forEach((key) => {
    if (source[key] !== undefined) {
      out[key] = source[key];
    }
  });
  return { ...out, ...(extra || {}) };
}
