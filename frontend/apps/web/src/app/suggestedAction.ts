export type SuggestedActionKind =
  | 'refresh'
  | 'retry'
  | 'relogin'
  | 'check_permission'
  | 'open_record'
  | 'open_scene'
  | 'open_url'
  | 'open_menu'
  | 'open_action'
  | '';

export type SuggestedActionParsed = {
  kind: SuggestedActionKind;
  raw: string;
  model?: string;
  recordId?: number;
  sceneKey?: string;
  url?: string;
  menuId?: number;
  actionId?: number;
};

export function normalizeSuggestedAction(value?: string) {
  return String(value || '').trim().toLowerCase();
}

export function parseSuggestedAction(value?: string): SuggestedActionParsed {
  const raw = normalizeSuggestedAction(value);
  if (!raw) return { kind: '', raw: '' };
  if (raw === 'refresh' || raw === 'refresh_list') return { kind: 'refresh', raw };
  if (raw === 'retry' || raw === 'retry_later') return { kind: 'retry', raw };
  if (raw === 'relogin' || raw === 'login_again') return { kind: 'relogin', raw };
  if (raw === 'check_permission' || raw === 'request_permission') return { kind: 'check_permission', raw };
  if (raw === 'open_record') return { kind: 'open_record', raw };
  if (raw.startsWith('open_record:')) {
    const parts = raw.split(':');
    if (parts.length >= 3) {
      const recordId = Number(parts[2]);
      if (parts[1] && Number.isFinite(recordId) && recordId > 0) {
        return { kind: 'open_record', raw, model: parts[1], recordId };
      }
    }
  }
  if (raw.startsWith('open_scene:')) {
    const sceneKey = raw.slice('open_scene:'.length).trim();
    if (sceneKey) return { kind: 'open_scene', raw, sceneKey };
  }
  if (raw.startsWith('open_menu:')) {
    const menuId = Number(raw.slice('open_menu:'.length).trim());
    if (Number.isFinite(menuId) && menuId > 0) return { kind: 'open_menu', raw, menuId };
  }
  if (raw.startsWith('open_action:')) {
    const actionId = Number(raw.slice('open_action:'.length).trim());
    if (Number.isFinite(actionId) && actionId > 0) return { kind: 'open_action', raw, actionId };
  }
  if (raw.startsWith('open_url:')) {
    const url = raw.slice('open_url:'.length).trim();
    if (url.startsWith('/')) return { kind: 'open_url', raw, url };
  }
  return { kind: '', raw };
}

export function suggestedActionLabel(parsed: SuggestedActionParsed): string {
  if (parsed.kind === 'refresh') return 'Refresh now';
  if (parsed.kind === 'retry') return 'Retry now';
  if (parsed.kind === 'relogin') return 'Go to login';
  if (parsed.kind === 'check_permission') return 'View permissions';
  if (parsed.kind === 'open_record') return 'Open record';
  if (parsed.kind === 'open_scene') return 'Open scene';
  if (parsed.kind === 'open_menu') return 'Open menu';
  if (parsed.kind === 'open_action') return 'Open action';
  if (parsed.kind === 'open_url') return 'Open link';
  return '';
}

export function suggestedActionHint(parsed: SuggestedActionParsed): string {
  if (parsed.kind === 'refresh') return 'Refresh the latest data and retry.';
  if (parsed.kind === 'retry') return 'Retry this action after a short delay.';
  if (parsed.kind === 'relogin') return 'Login again and retry.';
  if (parsed.kind === 'check_permission') return 'Check role permissions, then retry.';
  if (parsed.kind === 'open_record') return 'Open the related record and resolve blockers first.';
  if (parsed.kind === 'open_scene') return 'Open the related scene and continue.';
  if (parsed.kind === 'open_menu') return 'Open the related menu and continue.';
  if (parsed.kind === 'open_action') return 'Open the related action and continue.';
  if (parsed.kind === 'open_url') return 'Open the provided link and continue.';
  return '';
}

function safeNavigate(path: string) {
  if (!path.startsWith('/')) return false;
  window.location.href = path;
  return true;
}

export function canRunSuggestedAction(
  parsed: SuggestedActionParsed,
  options: { hasRetryHandler?: boolean; hasActionHandler?: boolean } = {},
) {
  if (!parsed.kind) return false;
  if (parsed.kind === 'refresh' || parsed.kind === 'retry') return Boolean(options.hasRetryHandler);
  if (parsed.kind === 'open_record') {
    if (parsed.model && parsed.recordId) return true;
    return Boolean(options.hasActionHandler);
  }
  if (parsed.kind === 'open_scene') return Boolean(parsed.sceneKey);
  if (parsed.kind === 'open_menu') return Boolean(parsed.menuId);
  if (parsed.kind === 'open_action') return Boolean(parsed.actionId);
  if (parsed.kind === 'open_url') return Boolean(parsed.url);
  if (parsed.kind === 'check_permission' || parsed.kind === 'relogin') return true;
  return false;
}

export function executeSuggestedAction(
  parsed: SuggestedActionParsed,
  options: {
    onRetry?: () => void;
    onSuggestedAction?: (action: string) => boolean | void;
  } = {},
) {
  if (!parsed.kind) return false;
  if (options.onSuggestedAction && parsed.raw) {
    const handled = options.onSuggestedAction(parsed.raw);
    if (handled) return true;
  }
  if ((parsed.kind === 'refresh' || parsed.kind === 'retry') && options.onRetry) {
    options.onRetry();
    return true;
  }
  if (parsed.kind === 'relogin') {
    const redirect = encodeURIComponent(`${window.location.pathname}${window.location.search}`);
    return safeNavigate(`/login?redirect=${redirect}`);
  }
  if (parsed.kind === 'check_permission') {
    return safeNavigate('/admin/usage-analytics');
  }
  if (parsed.kind === 'open_scene' && parsed.sceneKey) {
    return safeNavigate(`/s/${encodeURIComponent(parsed.sceneKey)}`);
  }
  if (parsed.kind === 'open_menu' && parsed.menuId) {
    return safeNavigate(`/m/${parsed.menuId}`);
  }
  if (parsed.kind === 'open_action' && parsed.actionId) {
    return safeNavigate(`/a/${parsed.actionId}`);
  }
  if (parsed.kind === 'open_record' && parsed.model && parsed.recordId) {
    return safeNavigate(`/r/${encodeURIComponent(parsed.model)}/${parsed.recordId}`);
  }
  if (parsed.kind === 'open_url' && parsed.url) {
    return safeNavigate(parsed.url);
  }
  return false;
}
