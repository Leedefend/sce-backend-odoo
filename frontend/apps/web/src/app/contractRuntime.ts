export function toPositiveInt(raw: unknown): number | null {
  const parsed = Number(raw || 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

export function parseMaybeJsonRecord(raw: unknown): Record<string, unknown> {
  if (!raw) return {};
  if (typeof raw === 'object' && !Array.isArray(raw)) {
    return raw as Record<string, unknown>;
  }
  if (typeof raw !== 'string') return {};
  const text = raw.trim();
  if (!text) return {};
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
  } catch {
    return {};
  }
  return {};
}

export function detectObjectMethodFromActionKey(key: string, fallback = ''): string {
  if (fallback) return fallback;
  const match = key.match(/^obj_([^_]+(?:_[^_]+)*)_/);
  return match?.[1] || '';
}

export function normalizeActionKind(kind: unknown): string {
  return String(kind || '').trim().toLowerCase();
}

