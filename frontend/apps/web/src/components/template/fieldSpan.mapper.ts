export type ResolveFieldSpanClassOptions = {
  fieldType: string;
};

export function resolveFieldSpanClass(options: ResolveFieldSpanClassOptions) {
  const normalizedType = String(options.fieldType || '').trim().toLowerCase();
  if (['text', 'html', 'many2many', 'one2many'].includes(normalizedType)) {
    return 'field--full';
  }

  return 'field--normal';
}
