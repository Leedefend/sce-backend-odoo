export function normalizeLabelMap(value: unknown): Record<string, string> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  return Object.entries(value as Record<string, unknown>).reduce<Record<string, string>>((acc, [key, raw]) => {
    const label = String(raw || '').trim();
    if (key && label) acc[key] = label;
    return acc;
  }, {});
}

export function formUiLabelsFromFormView(formView: unknown): Record<string, string> {
  const row = formView && typeof formView === 'object' && !Array.isArray(formView)
    ? formView as Record<string, unknown>
    : {};
  return normalizeLabelMap(row.ui_labels);
}

export function formUiLabelFromLabels(labels: Record<string, string>, key: string) {
  const fallbackLabels: Record<string, string> = {
    save: '保存',
    saving: '保存中...',
    discard: '放弃',
    reload: '刷新表单数据',
    save_success: '保存成功，已同步最新表单内容。',
  };
  return labels[key] || fallbackLabels[key] || key;
}

export function nativeChatterActionLabel(mode: string, row: Record<string, unknown>) {
  if (mode === 'message') return '记录沟通';
  if (mode === 'note') return '记录备注';
  if (mode === 'activity') return '安排计划';
  return String(row.label || row.key || '').trim();
}

export function activityFieldLabel(payload: Record<string, unknown> | undefined, name: string, fallback: string) {
  const fields = payload?.fields;
  if (!Array.isArray(fields)) return fallback;
  const row = fields.find((item) => (
    item && typeof item === 'object' && String((item as Record<string, unknown>).name || '') === name
  )) as Record<string, unknown> | undefined;
  return String(row?.label || fallback).trim();
}

export function labelFromMap(labels: Record<string, string>, key: string, fallback: string) {
  return String(labels[key] || fallback).trim();
}

export function layoutContainsType(nodes: Array<Record<string, unknown>>, type: string): boolean {
  const target = String(type || '').trim().toLowerCase();
  for (const node of nodes || []) {
    const current = String(node?.type || '').trim().toLowerCase();
    if (current === target) return true;
    const children: Array<Record<string, unknown>> = [];
    for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
      const value = node?.[key];
      if (Array.isArray(value)) children.push(...(value as Array<Record<string, unknown>>));
    }
    if (children.length && layoutContainsType(children, target)) return true;
  }
  return false;
}
