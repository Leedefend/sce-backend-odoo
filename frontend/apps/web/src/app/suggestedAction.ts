export type SuggestedActionKind =
  | 'refresh'
  | 'retry'
  | 'go_back'
  | 'open_login'
  | 'relogin'
  | 'check_permission'
  | 'open_home'
  | 'open_my_work'
  | 'open_usage_analytics'
  | 'open_scene_health'
  | 'open_scene_packages'
  | 'open_projects_list'
  | 'open_projects_board'
  | 'open_project'
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
  | 'copy_error_line'
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
  projectId?: number;
  query?: string;
  hash?: string;
};

export function normalizeSuggestedAction(value?: string) {
  return String(value || '').trim().toLowerCase();
}

export function parseSuggestedAction(value?: string): SuggestedActionParsed {
  const rawInput = String(value || '').trim();
  const raw = normalizeSuggestedAction(value);
  if (!raw) return { kind: '', raw: '' };
  if (raw === 'refresh' || raw === 'refresh_list') return { kind: 'refresh', raw };
  if (raw === 'retry' || raw === 'retry_later') return { kind: 'retry', raw };
  if (raw === 'go_back' || raw === 'back') return { kind: 'go_back', raw };
  if (raw === 'open_login' || raw === 'go_login') return { kind: 'open_login', raw };
  if (raw.startsWith('open_login?')) {
    const query = rawInput.slice('open_login?'.length).trim();
    if (query) return { kind: 'open_login', raw, query };
  }
  if (raw === 'relogin' || raw === 'login_again') return { kind: 'relogin', raw };
  if (raw === 'check_permission' || raw === 'request_permission') return { kind: 'check_permission', raw };
  if (raw === 'open_home' || raw === 'go_home') return { kind: 'open_home', raw };
  if (raw.startsWith('open_home?')) {
    const payload = rawInput.slice('open_home?'.length).trim();
    const [queryRaw, hashRaw] = payload.split('#');
    const query = String(queryRaw || '').trim();
    const hash = String(hashRaw || '').trim();
    if (query && hash) return { kind: 'open_home', raw, query, hash };
    if (query) return { kind: 'open_home', raw, query };
    if (hash) return { kind: 'open_home', raw, hash };
  }
  if (raw === 'open_my_work' || raw === 'open_todo') return { kind: 'open_my_work', raw };
  if (raw.startsWith('open_my_work?')) {
    const query = raw.slice('open_my_work?'.length).trim();
    if (query) return { kind: 'open_my_work', raw, query };
  }
  if (raw === 'open_usage_analytics' || raw === 'open_capability_visibility') {
    return { kind: 'open_usage_analytics', raw };
  }
  if (raw.startsWith('open_usage_analytics?')) {
    const query = raw.slice('open_usage_analytics?'.length).trim();
    if (query) return { kind: 'open_usage_analytics', raw, query };
  }
  if (raw === 'open_scene_health') return { kind: 'open_scene_health', raw };
  if (raw.startsWith('open_scene_health?')) {
    const query = raw.slice('open_scene_health?'.length).trim();
    if (query) return { kind: 'open_scene_health', raw, query };
  }
  if (raw === 'open_scene_packages') return { kind: 'open_scene_packages', raw };
  if (raw.startsWith('open_scene_packages?')) {
    const query = raw.slice('open_scene_packages?'.length).trim();
    if (query) return { kind: 'open_scene_packages', raw, query };
  }
  if (raw === 'open_projects_list') return { kind: 'open_projects_list', raw };
  if (raw.startsWith('open_projects_list?')) {
    const query = rawInput.slice('open_projects_list?'.length).trim();
    if (query) return { kind: 'open_projects_list', raw, query };
  }
  if (raw === 'open_projects_board') return { kind: 'open_projects_board', raw };
  if (raw.startsWith('open_projects_board?')) {
    const query = rawInput.slice('open_projects_board?'.length).trim();
    if (query) return { kind: 'open_projects_board', raw, query };
  }
  const projectMatch = rawInput.match(/^open_project:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i);
  if (projectMatch) {
    const projectId = Number(projectMatch[1]);
    const query = String(projectMatch[2] || '').trim();
    const hash = String(projectMatch[3] || '').trim();
    if (Number.isFinite(projectId) && projectId > 0 && query && hash) return { kind: 'open_project', raw, projectId, query, hash };
    if (Number.isFinite(projectId) && projectId > 0 && hash) return { kind: 'open_project', raw, projectId, hash };
    if (Number.isFinite(projectId) && projectId > 0 && query) return { kind: 'open_project', raw, projectId, query };
    if (Number.isFinite(projectId) && projectId > 0) return { kind: 'open_project', raw, projectId };
  }
  if (raw === 'open_dashboard') return { kind: 'open_dashboard', raw };
  if (raw.startsWith('open_dashboard?')) {
    const payload = rawInput.slice('open_dashboard?'.length).trim();
    const [queryRaw, hashRaw] = payload.split('#');
    const query = String(queryRaw || '').trim();
    const hash = String(hashRaw || '').trim();
    if (query && hash) return { kind: 'open_dashboard', raw, query, hash };
    if (query) return { kind: 'open_dashboard', raw, query };
    if (hash) return { kind: 'open_dashboard', raw, hash };
  }
  if (raw === 'copy_trace' || raw === 'copy_trace_id') return { kind: 'copy_trace', raw };
  if (raw === 'copy_reason' || raw === 'copy_reason_code') return { kind: 'copy_reason', raw };
  if (raw === 'copy_message' || raw === 'copy_error_message') return { kind: 'copy_message', raw };
  if (raw === 'copy_error_line' || raw === 'copy_compact_error') return { kind: 'copy_error_line', raw };
  if (raw === 'copy_full_error' || raw === 'copy_error_bundle') return { kind: 'copy_full_error', raw };
  if (raw === 'open_record') return { kind: 'open_record', raw };
  const recordMatch = rawInput.match(/^open_record:([^:]+):([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i);
  if (recordMatch) {
    const model = String(recordMatch[1] || '').trim();
    const recordId = Number(recordMatch[2]);
    const query = String(recordMatch[3] || '').trim();
    const hash = String(recordMatch[4] || '').trim();
    if (model && Number.isFinite(recordId) && recordId > 0) {
      return { kind: 'open_record', raw, model, recordId, query, hash };
    }
  }
  if (raw.startsWith('open_scene:')) {
    const payload = rawInput.slice('open_scene:'.length).trim();
    const [payloadWithQuery, hashRaw] = payload.split('#');
    const [sceneKey, queryRaw] = String(payloadWithQuery || '').split('?');
    const hash = String(hashRaw || '').trim();
    if (sceneKey && queryRaw && hash) return { kind: 'open_scene', raw, sceneKey, query: queryRaw, hash };
    if (sceneKey && queryRaw) return { kind: 'open_scene', raw, sceneKey, query: queryRaw };
    if (sceneKey && hash) return { kind: 'open_scene', raw, sceneKey, hash };
    if (sceneKey) return { kind: 'open_scene', raw, sceneKey };
  }
  const menuMatch = rawInput.match(/^open_menu:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i);
  if (menuMatch) {
    const menuId = Number(menuMatch[1]);
    const query = String(menuMatch[2] || '').trim();
    const hash = String(menuMatch[3] || '').trim();
    if (Number.isFinite(menuId) && menuId > 0 && query && hash) return { kind: 'open_menu', raw, menuId, query, hash };
    if (Number.isFinite(menuId) && menuId > 0 && hash) return { kind: 'open_menu', raw, menuId, hash };
    if (Number.isFinite(menuId) && menuId > 0 && query) return { kind: 'open_menu', raw, menuId, query };
    if (Number.isFinite(menuId) && menuId > 0) return { kind: 'open_menu', raw, menuId };
  }
  const actionMatch = rawInput.match(/^open_action:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i);
  if (actionMatch) {
    const actionId = Number(actionMatch[1]);
    const query = String(actionMatch[2] || '').trim();
    const hash = String(actionMatch[3] || '').trim();
    if (Number.isFinite(actionId) && actionId > 0 && query && hash) return { kind: 'open_action', raw, actionId, query, hash };
    if (Number.isFinite(actionId) && actionId > 0 && hash) return { kind: 'open_action', raw, actionId, hash };
    if (Number.isFinite(actionId) && actionId > 0 && query) return { kind: 'open_action', raw, actionId, query };
    if (Number.isFinite(actionId) && actionId > 0) return { kind: 'open_action', raw, actionId };
  }
  if (raw.startsWith('open_route:')) {
    const payload = rawInput.slice('open_route:'.length).trim();
    const [url, hashRaw] = payload.split('#');
    const hash = String(hashRaw || '').trim();
    if (url.startsWith('/') && hash) return { kind: 'open_route', raw, url, hash };
    if (url.startsWith('/')) return { kind: 'open_route', raw, url };
  }
  if (raw.startsWith('open_url:')) {
    const payload = rawInput.slice('open_url:'.length).trim();
    const [url, hashRaw] = payload.split('#');
    const hash = String(hashRaw || '').trim();
    if (url.startsWith('/') && hash) return { kind: 'open_url', raw, url, hash };
    if (url.startsWith('/')) return { kind: 'open_url', raw, url };
  }
  return { kind: '', raw };
}

export function suggestedActionLabel(parsed: SuggestedActionParsed): string {
  if (parsed.kind === 'refresh') return 'Refresh now';
  if (parsed.kind === 'retry') return 'Retry now';
  if (parsed.kind === 'go_back') return 'Go back';
  if (parsed.kind === 'open_login') return 'Open login';
  if (parsed.kind === 'relogin') return 'Go to login';
  if (parsed.kind === 'check_permission') return 'View permissions';
  if (parsed.kind === 'open_home') return 'Go home';
  if (parsed.kind === 'open_my_work') return 'Open my work';
  if (parsed.kind === 'open_usage_analytics') return 'Open usage analytics';
  if (parsed.kind === 'open_scene_health') return 'Open scene health';
  if (parsed.kind === 'open_scene_packages') return 'Open scene packages';
  if (parsed.kind === 'open_projects_list') return 'Open projects list';
  if (parsed.kind === 'open_projects_board') return 'Open projects board';
  if (parsed.kind === 'open_project') return 'Open project';
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
  if (parsed.kind === 'copy_error_line') return 'Copy error line';
  if (parsed.kind === 'copy_full_error') return 'Copy full error';
  return '';
}

export function suggestedActionHint(parsed: SuggestedActionParsed): string {
  if (parsed.kind === 'refresh') return 'Refresh the latest data and retry.';
  if (parsed.kind === 'retry') return 'Retry this action after a short delay.';
  if (parsed.kind === 'go_back') return 'Go back to the previous page.';
  if (parsed.kind === 'open_login') return 'Open login page.';
  if (parsed.kind === 'relogin') return 'Login again and retry.';
  if (parsed.kind === 'check_permission') return 'Check role permissions, then retry.';
  if (parsed.kind === 'open_home') return 'Go back to home and continue.';
  if (parsed.kind === 'open_my_work') return 'Open My Work and continue processing pending items.';
  if (parsed.kind === 'open_usage_analytics') return 'Open usage analytics to inspect capability visibility.';
  if (parsed.kind === 'open_scene_health') return 'Open scene health to inspect diagnostics.';
  if (parsed.kind === 'open_scene_packages') return 'Open scene packages for governance actions.';
  if (parsed.kind === 'open_projects_list') return 'Open projects list scene.';
  if (parsed.kind === 'open_projects_board') return 'Open projects board scene.';
  if (parsed.kind === 'open_project') return 'Open the target project page.';
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
  if (parsed.kind === 'copy_error_line') return 'Copy a compact error line for quick sharing.';
  if (parsed.kind === 'copy_full_error') return 'Copy full error bundle for troubleshooting.';
  return '';
}

function isSafeRelativePath(path: string) {
  if (!path.startsWith('/')) return false;
  if (path.startsWith('//')) return false;
  const lowered = path.toLowerCase();
  if (lowered.includes('javascript:')) return false;
  return true;
}

function safeNavigate(path: string) {
  if (!isSafeRelativePath(path)) return false;
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
  if (parsed.kind === 'open_login') return true;
  if (parsed.kind === 'open_record') {
    if (parsed.model && parsed.recordId) return true;
    return Boolean(options.hasActionHandler);
  }
  if (parsed.kind === 'open_scene') return Boolean(parsed.sceneKey);
  if (parsed.kind === 'open_menu') return Boolean(parsed.menuId);
  if (parsed.kind === 'open_action') return Boolean(parsed.actionId);
  if (parsed.kind === 'open_project') return Boolean(parsed.projectId);
  if (parsed.kind === 'open_route') return Boolean(parsed.url && isSafeRelativePath(parsed.url));
  if (parsed.kind === 'open_url') return Boolean(parsed.url && isSafeRelativePath(parsed.url));
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
  if (parsed.kind === 'copy_error_line') {
    return Boolean(
      String(options.traceId || '').trim() ||
        String(options.reasonCode || '').trim() ||
        String(options.message || '').trim(),
    );
  }
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

function appendHash(path: string, hash?: string) {
  const h = String(hash || '').trim().replace(/^#+/, '');
  if (!h) return path;
  return `${path}#${h}`;
}

export function executeSuggestedAction(
  parsed: SuggestedActionParsed,
  options: {
    onRetry?: () => void;
    onSuggestedAction?: (action: string) => boolean | void;
    onExecuted?: (result: { kind: SuggestedActionKind; raw: string; success: boolean }) => void;
    traceId?: string;
    reasonCode?: string;
    message?: string;
  } = {},
) {
  const finish = (success: boolean) => {
    if (options.onExecuted) {
      options.onExecuted({ kind: parsed.kind, raw: parsed.raw, success });
    }
    return success;
  };
  if (!parsed.kind) return false;
  if (options.onSuggestedAction && parsed.raw) {
    const handled = options.onSuggestedAction(parsed.raw);
    if (handled) return finish(true);
  }
  if ((parsed.kind === 'refresh' || parsed.kind === 'retry') && options.onRetry) {
    options.onRetry();
    return finish(true);
  }
  if (parsed.kind === 'go_back') {
    if (window.history.length <= 1) return finish(false);
    window.history.back();
    return finish(true);
  }
  if (parsed.kind === 'relogin') {
    const redirect = encodeURIComponent(`${window.location.pathname}${window.location.search}`);
    return finish(safeNavigate(`/login?redirect=${redirect}`));
  }
  if (parsed.kind === 'open_login') {
    return finish(safeNavigate(appendQuery('/login', parsed.query)));
  }
  if (parsed.kind === 'check_permission') {
    return finish(safeNavigate('/admin/usage-analytics'));
  }
  if (parsed.kind === 'open_home') {
    return finish(safeNavigate(appendHash(appendQuery('/', parsed.query), parsed.hash)));
  }
  if (parsed.kind === 'open_dashboard') {
    return finish(safeNavigate(appendHash(appendQuery('/', parsed.query), parsed.hash)));
  }
  if (parsed.kind === 'open_my_work') {
    return finish(safeNavigate(appendQuery('/my-work', parsed.query)));
  }
  if (parsed.kind === 'open_usage_analytics') {
    return finish(safeNavigate(appendQuery('/admin/usage-analytics', parsed.query)));
  }
  if (parsed.kind === 'open_scene_health') {
    return finish(safeNavigate(appendQuery('/admin/scene-health', parsed.query)));
  }
  if (parsed.kind === 'open_scene_packages') {
    return finish(safeNavigate(appendQuery('/admin/scene-packages', parsed.query)));
  }
  if (parsed.kind === 'open_projects_list') {
    return finish(safeNavigate(appendQuery('/s/projects.list', parsed.query)));
  }
  if (parsed.kind === 'open_projects_board') {
    return finish(safeNavigate(appendQuery('/projects', parsed.query)));
  }
  if (parsed.kind === 'open_project' && parsed.projectId) {
    return finish(safeNavigate(appendHash(appendQuery(`/projects/${parsed.projectId}`, parsed.query), parsed.hash)));
  }
  if (parsed.kind === 'open_scene' && parsed.sceneKey) {
    return finish(
      safeNavigate(
      appendHash(appendQuery(`/s/${encodeURIComponent(parsed.sceneKey)}`, parsed.query), parsed.hash),
      ),
    );
  }
  if (parsed.kind === 'open_menu' && parsed.menuId) {
    return finish(safeNavigate(appendHash(appendQuery(`/m/${parsed.menuId}`, parsed.query), parsed.hash)));
  }
  if (parsed.kind === 'open_action' && parsed.actionId) {
    return finish(safeNavigate(appendHash(appendQuery(`/a/${parsed.actionId}`, parsed.query), parsed.hash)));
  }
  if (parsed.kind === 'open_record' && parsed.model && parsed.recordId) {
    return finish(
      safeNavigate(
        appendHash(appendQuery(`/r/${encodeURIComponent(parsed.model)}/${parsed.recordId}`, parsed.query), parsed.hash),
      ),
    );
  }
  if (parsed.kind === 'open_route' && parsed.url) {
    return finish(safeNavigate(appendHash(parsed.url, parsed.hash)));
  }
  if (parsed.kind === 'open_url' && parsed.url) {
    return finish(safeNavigate(appendHash(parsed.url, parsed.hash)));
  }
  if (parsed.kind === 'copy_trace') {
    void copyText(options.traceId || '');
    return finish(true);
  }
  if (parsed.kind === 'copy_reason') {
    void copyText(options.reasonCode || '');
    return finish(true);
  }
  if (parsed.kind === 'copy_message') {
    void copyText(options.message || '');
    return finish(true);
  }
  if (parsed.kind === 'copy_error_line') {
    const pieces = [
      String(options.reasonCode || '').trim(),
      String(options.message || '').trim(),
      String(options.traceId || '').trim() ? `trace=${String(options.traceId || '').trim()}` : '',
    ].filter(Boolean);
    void copyText(pieces.join(' | '));
    return finish(true);
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
    return finish(true);
  }
  return finish(false);
}
