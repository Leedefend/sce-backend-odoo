export function dictOrEmpty(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

export function mergeFieldLabelsFromSource(source: unknown, out: Record<string, string>) {
  if (!source || typeof source !== 'object' || Array.isArray(source)) return;
  const row = source as Record<string, unknown>;
  const directLabels = dictOrEmpty(row.fieldLabels || row.field_labels);
  Object.entries(directLabels).forEach(([name, value]) => {
    const label = String(value || '').trim();
    if (name && label) out[name] = label;
  });
  Object.values(row).forEach((value) => {
    if (value && typeof value === 'object') {
      if (Array.isArray(value)) {
        value.forEach((item) => mergeFieldLabelsFromSource(item, out));
      } else {
        mergeFieldLabelsFromSource(value, out);
      }
    }
  });
}
