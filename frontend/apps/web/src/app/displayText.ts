export function resolveDisplayText(value: unknown): string {
  if (typeof value === 'string') return value.trim();
  if (typeof value === 'number' || typeof value === 'boolean') return String(value).trim();
  if (!value || typeof value !== 'object' || Array.isArray(value)) return '';

  const row = value as Record<string, unknown>;
  const preferredKeys = ['zh_CN', 'zh_Hans', 'zh', 'label', 'name', 'display_name', 'en_US', 'en'] as const;
  for (const key of preferredKeys) {
    const text = resolveDisplayText(row[key]);
    if (text) return text;
  }
  return '';
}
