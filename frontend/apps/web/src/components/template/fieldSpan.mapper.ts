export type ResolveFieldSpanClassOptions = {
  fieldName: string;
  fieldType: string;
};

export function resolveFieldSpanClass(options: ResolveFieldSpanClassOptions) {
  const normalizedType = String(options.fieldType || '').trim().toLowerCase();
  if (['text', 'html', 'many2many', 'one2many'].includes(normalizedType)) {
    return 'field--full';
  }

  const normalizedName = String(options.fieldName || '').trim().toLowerCase();
  if (['description', 'note', 'remark', 'address', 'location', 'content'].some((key) => normalizedName.includes(key))) {
    return 'field--full';
  }

  return 'field--half';
}
