const USER_SURFACE_NOISE_MARKERS = ['demo', 'showcase', 'smoke', 'internal', 'ir_cron', 'project_update_all_action'];

export function hasActionViewNoiseMarker(...values: unknown[]): boolean {
  const merged = values
    .map((value) => String(value || '').trim().toLowerCase())
    .filter(Boolean)
    .join(' ');
  if (!merged) return false;
  return USER_SURFACE_NOISE_MARKERS.some((token) => merged.includes(token));
}

export function isActionViewNumericToken(value: unknown): boolean {
  const text = String(value || '').trim();
  return text.length > 0 && /^\d+$/.test(text);
}
