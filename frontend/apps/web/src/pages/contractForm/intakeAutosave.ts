const INTAKE_AUTOSAVE_FIELDS = [
  'name',
  'manager_id',
  'owner_id',
  'project_type_id',
  'project_category_id',
  'location',
  'start_date',
  'end_date',
] as const;

export function persistIntakeAutosavePayload(key: string, values: Record<string, unknown>) {
  const storageKey = String(key || '').trim();
  if (!storageKey || typeof window === 'undefined') return;
  try {
    const payload = {
      saved_at: Date.now(),
      values: INTAKE_AUTOSAVE_FIELDS.reduce<Record<string, unknown>>((acc, field) => {
        const fallback = field.endsWith('_id') ? false : '';
        acc[field] = values[field] ?? fallback;
        return acc;
      }, {}),
    };
    window.localStorage.setItem(storageKey, JSON.stringify(payload));
  } catch {
    // ignore storage exceptions
  }
}

export function restoreIntakeAutosavePayload(key: string) {
  const storageKey = String(key || '').trim();
  if (!storageKey || typeof window === 'undefined') return {};
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as { values?: Record<string, unknown> };
    const values = parsed?.values;
    if (!values || typeof values !== 'object') return {};
    return INTAKE_AUTOSAVE_FIELDS.reduce<Record<string, unknown>>((acc, field) => {
      if (!(field in values)) return acc;
      const nextValue = values[field];
      if (nextValue === null || nextValue === undefined || nextValue === '') return acc;
      acc[field] = nextValue;
      return acc;
    }, {});
  } catch {
    return {};
  }
}

export function clearIntakeAutosavePayload(key: string) {
  const storageKey = String(key || '').trim();
  if (!storageKey || typeof window === 'undefined') return;
  try {
    window.localStorage.removeItem(storageKey);
  } catch {
    // ignore storage exceptions
  }
}
