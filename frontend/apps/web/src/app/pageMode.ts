export type PageMode = 'dashboard' | 'workspace' | 'list' | 'ledger';

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
    return 'ledger';
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
  if (normalized === 'ledger') return '业务台账';
  return '工作台';
}
