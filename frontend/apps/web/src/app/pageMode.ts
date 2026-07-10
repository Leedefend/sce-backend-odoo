export const PAGE_MODES = ['dashboard', 'workspace', 'list', 'form', 'detail', 'admin'] as const;

export type PageMode = typeof PAGE_MODES[number];

export function resolvePageMode(sceneKey: string, layoutKind: string): PageMode {
  const key = String(sceneKey || '').trim();
  const kind = String(layoutKind || '').trim().toLowerCase();

  if (key === 'project.management' || key === 'projects.dashboard') {
    return 'dashboard';
  }
  if (kind === 'list') {
    return 'list';
  }
  if (kind === 'ledger') {
    return 'workspace';
  }
  if (kind === 'workspace') {
    return 'workspace';
  }
  return 'workspace';
}

export function pageModeLabel(mode: string): string {
  const normalized = String(mode || '').trim().toLowerCase();
  if (normalized === 'dashboard') return '驾驶舱';
  if (normalized === 'list') return '台账列表';
  if (normalized === 'form') return '业务表单';
  if (normalized === 'detail') return '详情页';
  if (normalized === 'admin') return '配置管理';
  return '工作台';
}
