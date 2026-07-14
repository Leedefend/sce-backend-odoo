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

export function isTechnicalViewTitle(value: string) {
  const normalized = String(value || '').trim();
  return /^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*){1,}\.(?:tree|list|form|kanban|search|graph|pivot|calendar|activity|gantt)$/i.test(normalized);
}

export function resolvePageTitle(params: {
  menuTitle: string;
  contractTitle: string;
  recordTitle: string;
}) {
  const menuTitle = String(params.menuTitle || '').trim();
  if (menuTitle) return menuTitle;
  const title = String(params.contractTitle || '').trim();
  if (title && !isTechnicalViewTitle(title)) return title;
  const recordTitle = String(params.recordTitle || '').trim();
  if (recordTitle) return recordTitle;
  return '业务表单';
}

export function resolvePageDisplayTitle(params: {
  isProjectIntakeCreateMode: boolean;
  currentBusinessCategoryLabel: string;
  pageTitle: string;
  recordId: number;
}) {
  if (params.isProjectIntakeCreateMode) return '创建项目';
  const businessTitle = String(params.currentBusinessCategoryLabel || params.pageTitle || '').trim();
  if (!businessTitle) return params.pageTitle;
  if (params.recordId) return businessTitle;
  return businessTitle.startsWith('新建') ? businessTitle : `新建${businessTitle}`;
}

export function resolvePageDisplaySubtitle(params: {
  isProjectIntakeCreateMode: boolean;
  currentBusinessCategoryLabel: string;
  pageTitle: string;
  recordTitle: string;
  pageDisplayTitle: string;
  recordId: number;
}) {
  if (params.isProjectIntakeCreateMode) return '填写核心信息即可完成项目立项';
  if (params.currentBusinessCategoryLabel && params.pageTitle !== params.currentBusinessCategoryLabel) return params.pageTitle;
  const recordTitle = String(params.recordTitle || '').trim();
  if (recordTitle && recordTitle !== params.pageDisplayTitle) return recordTitle;
  return params.recordId ? '记录详情' : '';
}

export function resolveSubmitButtonLabel(params: {
  busy: boolean;
  busyKind: string | null;
  footerActionLabel: string;
  hasFooterAction: boolean;
  hasPrimarySubmitAction: boolean;
  isProjectQuickIntakeMode: boolean;
  isProjectIntakeCreateMode: boolean;
  recordId: number;
  saveLabel: string;
  savingLabel: string;
}) {
  if (params.busy && params.busyKind === 'save' && !params.hasPrimarySubmitAction) {
    if (params.isProjectQuickIntakeMode) return '创建中...';
    if (!params.recordId && params.hasFooterAction) return '处理中...';
    return !params.recordId ? '提交中...' : params.savingLabel;
  }
  if (params.busy && params.busyKind === 'action' && (params.hasPrimarySubmitAction || params.hasFooterAction)) {
    return params.hasFooterAction ? '处理中...' : '提交中...';
  }
  if (params.hasFooterAction) return params.footerActionLabel;
  if (params.hasPrimarySubmitAction) return '提交';
  if (params.isProjectQuickIntakeMode && !params.recordId) return '创建并进入项目驾驶舱';
  if (!params.recordId && !params.isProjectIntakeCreateMode) return '提交';
  return params.saveLabel;
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
