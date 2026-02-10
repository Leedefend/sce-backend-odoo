export type SuggestedActionKind =
  | 'refresh'
  | 'retry'
  | 'go_back'
  | 'relogin'
  | 'check_permission'
  | 'open_home'
  | 'open_my_work'
  | 'open_usage_analytics'
  | 'open_scene_health'
  | 'open_scene_packages'
  | 'open_projects_list'
  | 'open_projects_board'
  | 'open_dashboard'
  | 'open_record'
  | 'open_scene'
  | 'open_url'
  | 'open_route'
  | 'open_menu'
  | 'open_action'
  | 'copy_trace'
  | 'copy_reason'
  | 'copy_message'
  | 'copy_full_error'
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
  query?: string;
};

export function normalizeSuggestedAction(value?: string) {
  return String(value || '').trim().toLowerCase();
}

export function parseSuggestedAction(value?: string): SuggestedActionParsed {
  const raw = normalizeSuggestedAction(value);
  if (!raw) return { kind: '', raw: '' };
  if (raw === 'refresh' || raw === 'refresh_list') return { kind: 'refresh', raw };
  if (raw === 'retry' || raw === 'retry_later') return { kind: 'retry', raw };
  if (raw === 'go_back' || raw === 'back') return { kind: 'go_back', raw };
  if (raw === 'relogin' || raw === 'login_again') return { kind: 'relogin', raw };
  if (raw === 'check_permission' || raw === 'request_permission') return { kind: 'check_permission', raw };
  if (raw === 'open_home' || raw === 'go_home') return { kind: 'open_home', raw };
  if (raw === 'open_my_work' || raw === 'open_todo') return { kind: 'open_my_work', raw };
  if (raw === 'open_usage_analytics' || raw === 'open_capability_visibility') {
    return { kind: 'open_usage_analytics', raw };
  }
  if (raw === 'open_scene_health') return { kind: 'open_scene_health', raw };
  if (raw === 'open_scene_packages') return { kind: 'open_scene_packages', raw };
  if (raw === 'open_projects_list') return { kind: 'open_projects_list', raw };
  if (raw === 'open_projects_board') return { kind: 'open_projects_board', raw };
  if (raw === 'open_dashboard') return { kind: 'open_dashboard', raw };
  if (raw === 'copy_trace' || raw === 'copy_trace_id') return { kind: 'copy_trace', raw };
  if (raw === 'copy_reason' || raw === 'copy_reason_code') return { kind: 'copy_reason', raw };
  if (raw === 'copy_message' || raw === 'copy_error_message') return { kind: 'copy_message', raw };
  if (raw === 'copy_full_error' || raw === 'copy_error_bundle') return { kind: 'copy_full_error', raw };
  if (raw === 'open_record') return { kind: 'open_record', raw };
  const recordMatch = raw.match(/^open_record:([^:]+):([0-9]+)(?:\?(.+))?$/);
  if (recordMatch) {
    const model = String(recordMatch[1] || '').trim();
    const recordId = Number(recordMatch[2]);
    const query = String(recordMatch[3] || '').trim();
    if (model && Number.isFinite(recordId) && recordId > 0) {
      return { kind: 'open_record', raw, model, recordId, query };
    }
  }
  if (raw.startsWith('open_scene:')) {
    const payload = raw.slice('open_scene:'.length).trim();
    const [sceneKey, queryRaw] = payload.split('?');
    if (sceneKey && queryRaw) return { kind: 'open_scene', raw, sceneKey, query: queryRaw };
    if (sceneKey) return { kind: 'open_scene', raw, sceneKey };
  }
  const menuMatch = raw.match(/^open_menu:([0-9]+)(?:\?(.+))?$/);
  if (menuMatch) {
    const menuId = Number(menuMatch[1]);
    const query = String(menuMatch[2] || '').trim();
    if (Number.isFinite(menuId) && menuId > 0 && query) return { kind: 'open_menu', raw, menuId, query };
    if (Number.isFinite(menuId) && menuId > 0) return { kind: 'open_menu', raw, menuId };
  }
  const actionMatch = raw.match(/^open_action:([0-9]+)(?:\?(.+))?$/);
  if (actionMatch) {
    const actionId = Number(actionMatch[1]);
    const query = String(actionMatch[2] || '').trim();
    if (Number.isFinite(actionId) && actionId > 0 && query) return { kind: 'open_action', raw, actionId, query };
    if (Number.isFinite(actionId) && actionId > 0) return { kind: 'open_action', raw, actionId };
  }
  if (raw.startsWith('open_route:')) {
    const url = raw.slice('open_route:'.length).trim();
    if (url.startsWith('/')) return { kind: 'open_route', raw, url };
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
  if (parsed.kind === 'go_back') return 'Go back';
  if (parsed.kind === 'relogin') return 'Go to login';
  if (parsed.kind === 'check_permission') return 'View permissions';
  if (parsed.kind === 'open_home') return 'Go home';
  if (parsed.kind === 'open_my_work') return 'Open my work';
  if (parsed.kind === 'open_usage_analytics') return 'Open usage analytics';
  if (parsed.kind === 'open_scene_health') return 'Open scene health';
  if (parsed.kind === 'open_scene_packages') return 'Open scene packages';
  if (parsed.kind === 'open_projects_list') return 'Open projects list';
  if (parsed.kind === 'open_projects_board') return 'Open projects board';
  if (parsed.kind === 'open_dashboard') return 'Open dashboard';
  if (parsed.kind === 'open_record') return 'Open record';
  if (parsed.kind === 'open_scene') return 'Open scene';
  if (parsed.kind === 'open_menu') return 'Open menu';
  if (parsed.kind === 'open_action') return 'Open action';
  if (parsed.kind === 'open_route') return 'Open route';
  if (parsed.kind === 'open_url') return 'Open link';
  if (parsed.kind === 'copy_trace') return 'Copy trace';
  if (parsed.kind === 'copy_reason') return 'Copy reason';
  if (parsed.kind === 'copy_message') return 'Copy message';
  if (parsed.kind === 'copy_full_error') return 'Copy full error';
  return '';
}

export function suggestedActionHint(parsed: SuggestedActionParsed): string {
  if (parsed.kind === 'refresh') return 'Refresh the latest data and retry.';
  if (parsed.kind === 'retry') return 'Retry this action after a short delay.';
  if (parsed.kind === 'go_back') return 'Go back to the previous page.';
  if (parsed.kind === 'relogin') return 'Login again and retry.';
  if (parsed.kind === 'check_permission') return 'Check role permissions, then retry.';
  if (parsed.kind === 'open_home') return 'Go back to home and continue.';
  if (parsed.kind === 'open_my_work') return 'Open My Work and continue processing pending items.';
  if (parsed.kind === 'open_usage_analytics') return 'Open usage analytics to inspect capability visibility.';
  if (parsed.kind === 'open_scene_health') return 'Open scene health to inspect diagnostics.';
  if (parsed.kind === 'open_scene_packages') return 'Open scene packages for governance actions.';
  if (parsed.kind === 'open_projects_list') return 'Open projects list scene.';
  if (parsed.kind === 'open_projects_board') return 'Open projects board scene.';
  if (parsed.kind === 'open_dashboard') return 'Open system dashboard.';
  if (parsed.kind === 'open_record') return 'Open the related record and resolve blockers first.';
  if (parsed.kind === 'open_scene') return 'Open the related scene and continue.';
  if (parsed.kind === 'open_menu') return 'Open the related menu and continue.';
  if (parsed.kind === 'open_action') return 'Open the related action and continue.';
  if (parsed.kind === 'open_route') return 'Open the related route and continue.';
  if (parsed.kind === 'open_url') return 'Open the provided link and continue.';
  if (parsed.kind === 'copy_trace') return 'Copy trace id for troubleshooting.';
  if (parsed.kind === 'copy_reason') return 'Copy reason code for troubleshooting.';
  if (parsed.kind === 'copy_message') return 'Copy error message for troubleshooting.';
  if (parsed.kind === 'copy_full_error') return 'Copy full error bundle for troubleshooting.';
  return '';
}

function safeNavigate(path: string) {
  if (!path.startsWith('/')) return false;
  window.location.href = path;
  return true;
}

export function canRunSuggestedAction(
  parsed: SuggestedActionParsed,
  options: {
    hasRetryHandler?: boolean;
    hasActionHandler?: boolean;
    traceId?: string;
    reasonCode?: string;
    message?: string;
  } = {},
) {
  if (!parsed.kind) return false;
  if (parsed.kind === 'refresh' || parsed.kind === 'retry') return Boolean(options.hasRetryHandler);
  if (parsed.kind === 'go_back') return window.history.length > 1;
  if (parsed.kind === 'open_record') {
    if (parsed.model && parsed.recordId) return true;
    return Boolean(options.hasActionHandler);
  }
  if (parsed.kind === 'open_scene') return Boolean(parsed.sceneKey);
  if (parsed.kind === 'open_menu') return Boolean(parsed.menuId);
  if (parsed.kind === 'open_action') return Boolean(parsed.actionId);
  if (parsed.kind === 'open_route') return Boolean(parsed.url);
  if (parsed.kind === 'open_url') return Boolean(parsed.url);
  if (
    parsed.kind === 'check_permission' ||
    parsed.kind === 'relogin' ||
    parsed.kind === 'open_home' ||
    parsed.kind === 'open_my_work' ||
    parsed.kind === 'open_usage_analytics' ||
    parsed.kind === 'open_scene_health' ||
    parsed.kind === 'open_scene_packages' ||
    parsed.kind === 'open_projects_list' ||
    parsed.kind === 'open_projects_board' ||
    parsed.kind === 'open_dashboard'
  ) {
    return true;
  }
  if (parsed.kind === 'copy_trace') return Boolean(String(options.traceId || '').trim());
  if (parsed.kind === 'copy_reason') return Boolean(String(options.reasonCode || '').trim());
  if (parsed.kind === 'copy_message') return Boolean(String(options.message || '').trim());
  if (parsed.kind === 'copy_full_error') {
    return Boolean(
      String(options.traceId || '').trim() ||
        String(options.reasonCode || '').trim() ||
        String(options.message || '').trim(),
    );
  }
  return false;
}

async function copyText(value: string) {
  const text = String(value || '').trim();
  if (!text) return false;
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // fallback below
  }
  try {
    const el = document.createElement('textarea');
    el.value = text;
    el.setAttribute('readonly', 'true');
    el.style.position = 'fixed';
    el.style.opacity = '0';
    document.body.appendChild(el);
    el.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(el);
    return ok;
  } catch {
    return false;
  }
}

function appendQuery(path: string, query?: string) {
  const q = String(query || '').trim();
  if (!q) return path;
  const cleaned = q.replace(/^\?+/, '');
  if (!cleaned) return path;
  return `${path}?${cleaned}`;
}

export function executeSuggestedAction(
  parsed: SuggestedActionParsed,
  options: {
    onRetry?: () => void;
    onSuggestedAction?: (action: string) => boolean | void;
    traceId?: string;
    reasonCode?: string;
    message?: string;
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
  if (parsed.kind === 'go_back') {
    if (window.history.length <= 1) return false;
    window.history.back();
    return true;
  }
  if (parsed.kind === 'relogin') {
    const redirect = encodeURIComponent(`${window.location.pathname}${window.location.search}`);
    return safeNavigate(`/login?redirect=${redirect}`);
  }
  if (parsed.kind === 'check_permission') {
    return safeNavigate('/admin/usage-analytics');
  }
  if (parsed.kind === 'open_home') {
    return safeNavigate('/');
  }
  if (parsed.kind === 'open_dashboard') {
    return safeNavigate('/');
  }
  if (parsed.kind === 'open_my_work') {
    return safeNavigate('/my-work');
  }
  if (parsed.kind === 'open_usage_analytics') {
    return safeNavigate('/admin/usage-analytics');
  }
  if (parsed.kind === 'open_scene_health') {
    return safeNavigate('/admin/scene-health');
  }
  if (parsed.kind === 'open_scene_packages') {
    return safeNavigate('/admin/scene-packages');
  }
  if (parsed.kind === 'open_projects_list') {
    return safeNavigate('/s/projects.list');
  }
  if (parsed.kind === 'open_projects_board') {
    return safeNavigate('/projects');
  }
  if (parsed.kind === 'open_scene' && parsed.sceneKey) {
    return safeNavigate(appendQuery(`/s/${encodeURIComponent(parsed.sceneKey)}`, parsed.query));
  }
  if (parsed.kind === 'open_menu' && parsed.menuId) {
    return safeNavigate(appendQuery(`/m/${parsed.menuId}`, parsed.query));
  }
  if (parsed.kind === 'open_action' && parsed.actionId) {
    return safeNavigate(appendQuery(`/a/${parsed.actionId}`, parsed.query));
  }
  if (parsed.kind === 'open_record' && parsed.model && parsed.recordId) {
    return safeNavigate(
      appendQuery(`/r/${encodeURIComponent(parsed.model)}/${parsed.recordId}`, parsed.query),
    );
  }
  if (parsed.kind === 'open_route' && parsed.url) {
    return safeNavigate(parsed.url);
  }
  if (parsed.kind === 'open_url' && parsed.url) {
    return safeNavigate(parsed.url);
  }
  if (parsed.kind === 'copy_trace') {
    void copyText(options.traceId || '');
    return true;
  }
  if (parsed.kind === 'copy_reason') {
    void copyText(options.reasonCode || '');
    return true;
  }
  if (parsed.kind === 'copy_message') {
    void copyText(options.message || '');
    return true;
  }
  if (parsed.kind === 'copy_full_error') {
    const bundle = JSON.stringify(
      {
        trace_id: String(options.traceId || '').trim() || undefined,
        reason_code: String(options.reasonCode || '').trim() || undefined,
        message: String(options.message || '').trim() || undefined,
      },
      null,
      2,
    );
    void copyText(bundle);
    return true;
  }
  return false;
}
