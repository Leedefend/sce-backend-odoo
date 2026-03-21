export function normalizeTemplateFieldLabel(label: unknown) {
  return String(label || '').trim();
}

export function resolveSelectPlaceholder(label: unknown) {
  const text = normalizeTemplateFieldLabel(label);
  return text ? `请选择${text}` : '请选择';
}

export function resolveInputPlaceholder(label: unknown) {
  const text = normalizeTemplateFieldLabel(label);
  return text ? `请输入${text}` : '';
}
