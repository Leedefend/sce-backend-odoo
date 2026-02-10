import type { SuggestedActionParsed } from './types';

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
  if (raw === 'open_my_work') return { kind: 'open_my_work', raw };
  if (raw === 'open_todo') return { kind: 'open_my_work_todo', raw };
  if (raw.startsWith('open_todo?')) {
    const query = rawInput.slice('open_todo?'.length).trim();
    if (query) return { kind: 'open_my_work_todo', raw, query };
  }
  if (raw === 'open_done') return { kind: 'open_my_work_done', raw };
  if (raw.startsWith('open_done?')) {
    const query = rawInput.slice('open_done?'.length).trim();
    if (query) return { kind: 'open_my_work_done', raw, query };
  }
  if (raw === 'open_failed') return { kind: 'open_my_work_failed', raw };
  if (raw.startsWith('open_failed?')) {
    const query = rawInput.slice('open_failed?'.length).trim();
    if (query) return { kind: 'open_my_work_failed', raw, query };
  }
  const myWorkSectionMatch = rawInput.match(/^open_my_work_section:([a-z0-9_]+)$/i);
  if (myWorkSectionMatch) {
    const section = String(myWorkSectionMatch[1] || '').trim();
    if (section) return { kind: 'open_my_work_section', raw, section };
  }
  const myWorkSectionAlias = rawInput.match(/^open_my_work:([a-z0-9_]+)$/i);
  if (myWorkSectionAlias) {
    const section = String(myWorkSectionAlias[1] || '').trim();
    if (section) return { kind: 'open_my_work_section', raw, section };
  }
  if (raw.startsWith('open_my_work?')) {
    const query = rawInput.slice('open_my_work?'.length).trim();
    if (query) return { kind: 'open_my_work', raw, query };
  }
  if (raw === 'open_usage_analytics' || raw === 'open_capability_visibility') {
    return { kind: 'open_usage_analytics', raw };
  }
  if (raw === 'open_locked') return { kind: 'open_locked', raw };
  if (raw === 'open_preview') return { kind: 'open_preview', raw };
  if (raw === 'open_ready') return { kind: 'open_ready', raw };
  if (raw === 'open_hidden') return { kind: 'open_hidden', raw };
  if (raw.startsWith('open_usage_analytics?')) {
    const query = rawInput.slice('open_usage_analytics?'.length).trim();
    if (query) return { kind: 'open_usage_analytics', raw, query };
  }
  if (raw === 'open_scene_health') return { kind: 'open_scene_health', raw };
  if (raw.startsWith('open_scene_health?')) {
    const query = rawInput.slice('open_scene_health?'.length).trim();
    if (query) return { kind: 'open_scene_health', raw, query };
  }
  if (raw === 'open_scene_packages') return { kind: 'open_scene_packages', raw };
  if (raw.startsWith('open_scene_packages?')) {
    const query = rawInput.slice('open_scene_packages?'.length).trim();
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
  const projectAliasMatch = rawInput.match(/^goto_project:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i);
  const parsedProjectMatch = projectMatch || projectAliasMatch;
  if (parsedProjectMatch) {
    const projectId = Number(parsedProjectMatch[1]);
    const query = String(parsedProjectMatch[2] || '').trim();
    const hash = String(parsedProjectMatch[3] || '').trim();
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
  if (raw === 'copy_action' || raw === 'copy_suggested_action') return { kind: 'copy_action', raw };
  if (raw === 'copy_json_error' || raw === 'copy_error_json') return { kind: 'copy_json_error', raw };
  if (raw === 'copy_full_error' || raw === 'copy_error_bundle') return { kind: 'copy_full_error', raw };
  if (raw === 'open_record') return { kind: 'open_record', raw };
  const recordMatch = rawInput.match(/^open_record:([^:]+):([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i);
  const recordAliasMatch = rawInput.match(/^go_record:([^:]+):([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i);
  const parsedRecordMatch = recordMatch || recordAliasMatch;
  if (parsedRecordMatch) {
    const model = String(parsedRecordMatch[1] || '').trim();
    const recordId = Number(parsedRecordMatch[2]);
    const query = String(parsedRecordMatch[3] || '').trim();
    const hash = String(parsedRecordMatch[4] || '').trim();
    if (model && Number.isFinite(recordId) && recordId > 0) {
      return { kind: 'open_record', raw, model, recordId, query, hash };
    }
  }
  if (raw.startsWith('open_scene:') || raw.startsWith('goto_scene:')) {
    const prefix = raw.startsWith('goto_scene:') ? 'goto_scene:' : 'open_scene:';
    const payload = rawInput.slice(prefix.length).trim();
    const [payloadWithQuery, hashRaw] = payload.split('#');
    const [sceneKey, queryRaw] = String(payloadWithQuery || '').split('?');
    const hash = String(hashRaw || '').trim();
    if (sceneKey && queryRaw && hash) return { kind: 'open_scene', raw, sceneKey, query: queryRaw, hash };
    if (sceneKey && queryRaw) return { kind: 'open_scene', raw, sceneKey, query: queryRaw };
    if (sceneKey && hash) return { kind: 'open_scene', raw, sceneKey, hash };
    if (sceneKey) return { kind: 'open_scene', raw, sceneKey };
  }
  const menuMatch = rawInput.match(/^open_menu:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i);
  const menuAliasMatch = rawInput.match(/^goto_menu:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i);
  const parsedMenuMatch = menuMatch || menuAliasMatch;
  if (parsedMenuMatch) {
    const menuId = Number(parsedMenuMatch[1]);
    const query = String(parsedMenuMatch[2] || '').trim();
    const hash = String(parsedMenuMatch[3] || '').trim();
    if (Number.isFinite(menuId) && menuId > 0 && query && hash) return { kind: 'open_menu', raw, menuId, query, hash };
    if (Number.isFinite(menuId) && menuId > 0 && hash) return { kind: 'open_menu', raw, menuId, hash };
    if (Number.isFinite(menuId) && menuId > 0 && query) return { kind: 'open_menu', raw, menuId, query };
    if (Number.isFinite(menuId) && menuId > 0) return { kind: 'open_menu', raw, menuId };
  }
  const actionMatch = rawInput.match(/^open_action:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i);
  const actionAliasMatch = rawInput.match(/^goto_action:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i);
  const parsedActionMatch = actionMatch || actionAliasMatch;
  if (parsedActionMatch) {
    const actionId = Number(parsedActionMatch[1]);
    const query = String(parsedActionMatch[2] || '').trim();
    const hash = String(parsedActionMatch[3] || '').trim();
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
