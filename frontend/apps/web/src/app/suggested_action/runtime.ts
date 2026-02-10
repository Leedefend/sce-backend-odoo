import type {
  SuggestedActionCapabilityOptions,
  SuggestedActionExecuteOptions,
  SuggestedActionParsed,
} from './types';

function isSafeRelativePath(path: string) {
  if (!path.startsWith('/')) return false;
  if (path.startsWith('//')) return false;
  const lowered = path.toLowerCase();
  if (lowered.includes('javascript:')) return false;
  if (lowered.includes('%2f%2f')) return false;
  try {
    const decoded = decodeURIComponent(path).toLowerCase();
    if (decoded.startsWith('//') || decoded.includes('javascript:')) return false;
  } catch {
    // Ignore decode error and keep original checks.
  }
  return true;
}

function safeNavigate(path: string) {
  if (!isSafeRelativePath(path)) return false;
  window.location.href = path;
  return true;
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
  if (path.includes('?')) return `${path}&${cleaned}`;
  return `${path}?${cleaned}`;
}

function appendHash(path: string, hash?: string) {
  const h = String(hash || '').trim().replace(/^#+/, '');
  if (!h) return path;
  return `${path}#${h}`;
}

export function canRunSuggestedAction(
  parsed: SuggestedActionParsed,
  options: SuggestedActionCapabilityOptions = {},
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
    parsed.kind === 'open_my_work_todo' ||
    parsed.kind === 'open_my_work_done' ||
    parsed.kind === 'open_my_work_failed' ||
    parsed.kind === 'open_my_work_section' ||
    parsed.kind === 'open_my_work' ||
    parsed.kind === 'open_usage_analytics' ||
    parsed.kind === 'open_locked' ||
    parsed.kind === 'open_preview' ||
    parsed.kind === 'open_ready' ||
    parsed.kind === 'open_hidden' ||
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
  if (parsed.kind === 'copy_action') return Boolean(String(parsed.raw || '').trim());
  if (parsed.kind === 'copy_json_error') {
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

export function executeSuggestedAction(
  parsed: SuggestedActionParsed,
  options: SuggestedActionExecuteOptions = {},
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
  if (parsed.kind === 'open_my_work_todo') {
    return finish(safeNavigate(appendQuery('/my-work?section=todo', parsed.query)));
  }
  if (parsed.kind === 'open_my_work_done') {
    return finish(safeNavigate(appendQuery('/my-work?section=done', parsed.query)));
  }
  if (parsed.kind === 'open_my_work_failed') {
    return finish(safeNavigate(appendQuery('/my-work?section=failed', parsed.query)));
  }
  if (parsed.kind === 'open_my_work_section' && parsed.section) {
    return finish(safeNavigate(`/my-work?section=${encodeURIComponent(parsed.section)}`));
  }
  if (parsed.kind === 'open_usage_analytics') {
    return finish(safeNavigate(appendQuery('/admin/usage-analytics', parsed.query)));
  }
  if (parsed.kind === 'open_locked') {
    return finish(safeNavigate('/admin/usage-analytics?state=locked'));
  }
  if (parsed.kind === 'open_preview') {
    return finish(safeNavigate('/admin/usage-analytics?state=preview'));
  }
  if (parsed.kind === 'open_ready') {
    return finish(safeNavigate('/admin/usage-analytics?state=ready'));
  }
  if (parsed.kind === 'open_hidden') {
    return finish(safeNavigate('/admin/usage-analytics?visibility=hidden'));
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
    return finish(safeNavigate(appendHash(appendQuery(`/s/${encodeURIComponent(parsed.sceneKey)}`, parsed.query), parsed.hash)));
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
  if (parsed.kind === 'copy_action') {
    void copyText(parsed.raw || '');
    return finish(true);
  }
  if (parsed.kind === 'copy_json_error') {
    const payload = {
      trace_id: String(options.traceId || '').trim() || undefined,
      reason_code: String(options.reasonCode || '').trim() || undefined,
      message: String(options.message || '').trim() || undefined,
    };
    void copyText(JSON.stringify(payload));
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
