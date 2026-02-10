import type { SuggestedActionKind, SuggestedActionParsed } from './types';

const SIMPLE_ALIASES: Record<string, SuggestedActionKind> = {
  refresh: 'refresh',
  refresh_list: 'refresh',
  retry: 'retry',
  retry_later: 'retry',
  go_back: 'go_back',
  back: 'go_back',
  open_login: 'open_login',
  go_login: 'open_login',
  relogin: 'relogin',
  login_again: 'relogin',
  check_permission: 'check_permission',
  request_permission: 'check_permission',
  open_home: 'open_home',
  go_home: 'open_home',
  open_my_work: 'open_my_work',
  open_todo: 'open_my_work_todo',
  open_done: 'open_my_work_done',
  open_failed: 'open_my_work_failed',
  open_usage_analytics: 'open_usage_analytics',
  open_capability_visibility: 'open_usage_analytics',
  open_locked: 'open_locked',
  open_preview: 'open_preview',
  open_ready: 'open_ready',
  open_hidden: 'open_hidden',
  open_scene_health: 'open_scene_health',
  open_scene_packages: 'open_scene_packages',
  open_projects_list: 'open_projects_list',
  open_projects_board: 'open_projects_board',
  open_dashboard: 'open_dashboard',
  copy_trace: 'copy_trace',
  copy_trace_id: 'copy_trace',
  copy_reason: 'copy_reason',
  copy_reason_code: 'copy_reason',
  copy_message: 'copy_message',
  copy_error_message: 'copy_message',
  copy_error_line: 'copy_error_line',
  copy_compact_error: 'copy_error_line',
  copy_action: 'copy_action',
  copy_suggested_action: 'copy_action',
  copy_json_error: 'copy_json_error',
  copy_error_json: 'copy_json_error',
  copy_full_error: 'copy_full_error',
  copy_error_bundle: 'copy_full_error',
  open_record: 'open_record',
};

const QUERY_ONLY_PREFIXES: Array<{ prefix: string; kind: SuggestedActionKind }> = [
  { prefix: 'open_login?', kind: 'open_login' },
  { prefix: 'open_todo?', kind: 'open_my_work_todo' },
  { prefix: 'open_done?', kind: 'open_my_work_done' },
  { prefix: 'open_failed?', kind: 'open_my_work_failed' },
  { prefix: 'open_my_work?', kind: 'open_my_work' },
  { prefix: 'open_usage_analytics?', kind: 'open_usage_analytics' },
  { prefix: 'open_scene_health?', kind: 'open_scene_health' },
  { prefix: 'open_scene_packages?', kind: 'open_scene_packages' },
  { prefix: 'open_projects_list?', kind: 'open_projects_list' },
  { prefix: 'open_projects_board?', kind: 'open_projects_board' },
];

const QUERY_HASH_PREFIXES: Array<{ prefix: string; kind: SuggestedActionKind }> = [
  { prefix: 'open_home?', kind: 'open_home' },
  { prefix: 'open_dashboard?', kind: 'open_dashboard' },
];

const SCENE_SECTION_PATTERNS = [/^open_my_work_section:([a-z0-9_]+)$/i, /^open_my_work:([a-z0-9_]+)$/i];

const PROJECT_PATTERNS = [/^open_project:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i, /^goto_project:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i];
const RECORD_PATTERNS = [/^open_record:([^:]+):([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i, /^go_record:([^:]+):([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i];
const MENU_PATTERNS = [/^open_menu:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i, /^goto_menu:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i];
const ACTION_PATTERNS = [/^open_action:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i, /^goto_action:([0-9]+)(?:\?([^#]+))?(?:#(.+))?$/i];

export function normalizeSuggestedAction(value?: string) {
  return String(value || '').trim().toLowerCase();
}

export function suggestedActionAliasMap(): Readonly<Record<string, SuggestedActionKind>> {
  return SIMPLE_ALIASES;
}

function parseQueryOnly(rawInput: string, prefix: string, kind: SuggestedActionKind, raw: string): SuggestedActionParsed | null {
  if (!raw.startsWith(prefix)) return null;
  const query = rawInput.slice(prefix.length).trim();
  if (!query) return null;
  return { kind, raw, query };
}

function splitQueryHash(payload: string) {
  const [queryRaw, hashRaw] = payload.split('#');
  const query = String(queryRaw || '').trim();
  const hash = String(hashRaw || '').trim();
  return { query, hash };
}

function parseQueryHash(rawInput: string, prefix: string, kind: SuggestedActionKind, raw: string): SuggestedActionParsed | null {
  if (!raw.startsWith(prefix)) return null;
  const { query, hash } = splitQueryHash(rawInput.slice(prefix.length).trim());
  if (query && hash) return { kind, raw, query, hash };
  if (query) return { kind, raw, query };
  if (hash) return { kind, raw, hash };
  return null;
}

function parseSectionAction(rawInput: string, raw: string): SuggestedActionParsed | null {
  for (const pattern of SCENE_SECTION_PATTERNS) {
    const match = rawInput.match(pattern);
    if (!match) continue;
    const section = String(match[1] || '').trim();
    if (section) return { kind: 'open_my_work_section', raw, section };
  }
  return null;
}

function parseNumericIdAction(
  rawInput: string,
  raw: string,
  kind: SuggestedActionKind,
  patterns: RegExp[],
  idKey: 'projectId' | 'menuId' | 'actionId',
): SuggestedActionParsed | null {
  for (const pattern of patterns) {
    const match = rawInput.match(pattern);
    if (!match) continue;
    const id = Number(match[1]);
    if (!Number.isFinite(id) || id <= 0) return null;
    const query = String(match[2] || '').trim();
    const hash = String(match[3] || '').trim();
    if (query && hash) return { kind, raw, [idKey]: id, query, hash } as SuggestedActionParsed;
    if (hash) return { kind, raw, [idKey]: id, hash } as SuggestedActionParsed;
    if (query) return { kind, raw, [idKey]: id, query } as SuggestedActionParsed;
    return { kind, raw, [idKey]: id } as SuggestedActionParsed;
  }
  return null;
}

function parseProject(rawInput: string, raw: string): SuggestedActionParsed | null {
  return parseNumericIdAction(rawInput, raw, 'open_project', PROJECT_PATTERNS, 'projectId');
}

function parseMenu(rawInput: string, raw: string): SuggestedActionParsed | null {
  return parseNumericIdAction(rawInput, raw, 'open_menu', MENU_PATTERNS, 'menuId');
}

function parseAction(rawInput: string, raw: string): SuggestedActionParsed | null {
  return parseNumericIdAction(rawInput, raw, 'open_action', ACTION_PATTERNS, 'actionId');
}

function parseRecord(rawInput: string, raw: string): SuggestedActionParsed | null {
  for (const pattern of RECORD_PATTERNS) {
    const match = rawInput.match(pattern);
    if (!match) continue;
    const model = String(match[1] || '').trim();
    const recordId = Number(match[2]);
    const query = String(match[3] || '').trim();
    const hash = String(match[4] || '').trim();
    if (model && Number.isFinite(recordId) && recordId > 0) {
      return { kind: 'open_record', raw, model, recordId, query, hash };
    }
  }
  return null;
}

function parseScene(rawInput: string, raw: string): SuggestedActionParsed | null {
  if (!raw.startsWith('open_scene:') && !raw.startsWith('goto_scene:')) return null;
  const prefix = raw.startsWith('goto_scene:') ? 'goto_scene:' : 'open_scene:';
  const payload = rawInput.slice(prefix.length).trim();
  const [payloadWithQuery, hashRaw] = payload.split('#');
  const [sceneKey, queryRaw] = String(payloadWithQuery || '').split('?');
  const hash = String(hashRaw || '').trim();
  if (sceneKey && queryRaw && hash) return { kind: 'open_scene', raw, sceneKey, query: queryRaw, hash };
  if (sceneKey && queryRaw) return { kind: 'open_scene', raw, sceneKey, query: queryRaw };
  if (sceneKey && hash) return { kind: 'open_scene', raw, sceneKey, hash };
  if (sceneKey) return { kind: 'open_scene', raw, sceneKey };
  return null;
}

function parsePathAction(rawInput: string, raw: string, prefix: 'open_route:' | 'open_url:', kind: 'open_route' | 'open_url') {
  if (!raw.startsWith(prefix)) return null;
  const payload = rawInput.slice(prefix.length).trim();
  const [url, hashRaw] = payload.split('#');
  const hash = String(hashRaw || '').trim();
  if (url.startsWith('/') && hash) return { kind, raw, url, hash } as SuggestedActionParsed;
  if (url.startsWith('/')) return { kind, raw, url } as SuggestedActionParsed;
  return null;
}

export function parseSuggestedAction(value?: string): SuggestedActionParsed {
  const rawInput = String(value || '').trim();
  const raw = normalizeSuggestedAction(value);
  if (!raw) return { kind: '', raw: '' };

  const simpleKind = SIMPLE_ALIASES[raw];
  if (simpleKind) return { kind: simpleKind, raw };

  for (const item of QUERY_ONLY_PREFIXES) {
    const parsed = parseQueryOnly(rawInput, item.prefix, item.kind, raw);
    if (parsed) return parsed;
  }

  for (const item of QUERY_HASH_PREFIXES) {
    const parsed = parseQueryHash(rawInput, item.prefix, item.kind, raw);
    if (parsed) return parsed;
  }

  const section = parseSectionAction(rawInput, raw);
  if (section) return section;

  const project = parseProject(rawInput, raw);
  if (project) return project;

  const record = parseRecord(rawInput, raw);
  if (record) return record;

  const scene = parseScene(rawInput, raw);
  if (scene) return scene;

  const menu = parseMenu(rawInput, raw);
  if (menu) return menu;

  const action = parseAction(rawInput, raw);
  if (action) return action;

  const route = parsePathAction(rawInput, raw, 'open_route:', 'open_route');
  if (route) return route;

  const openUrl = parsePathAction(rawInput, raw, 'open_url:', 'open_url');
  if (openUrl) return openUrl;

  return { kind: '', raw };
}
