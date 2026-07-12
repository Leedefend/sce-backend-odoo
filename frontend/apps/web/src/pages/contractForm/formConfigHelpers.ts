import type { FormConfigAuditResult, FormConfigOperationLogEntry, LowCodeFieldSize } from './types';
import { normalizeLowCodeColumnsOrNull } from './fieldUtils';
import { nativeLayoutNodeType, type NativeLayoutLikeNode } from './nativeLayoutUtils';

export function normalizeFormConfigOperationLogEntries(raw: unknown, operator = '当前用户') {
  if (!Array.isArray(raw)) return [];
  const allowedStatus = new Set<FormConfigOperationLogEntry['status']>(['pending', 'saved', 'reverted', 'done']);
  return raw
    .map((item) => {
      const row = item && typeof item === 'object' && !Array.isArray(item)
        ? item as Record<string, unknown>
        : {};
      const id = String(row.id || '').trim();
      const at = String(row.at || '').trim();
      const action = String(row.action || '').trim();
      const summary = String(row.summary || '').trim();
      if (!id || !at || !action || !summary) return null;
      return {
        id,
        at,
        operator: String(row.operator || operator || '当前用户').trim(),
        action,
        summary,
        status: allowedStatus.has(row.status as FormConfigOperationLogEntry['status'])
          ? row.status as FormConfigOperationLogEntry['status']
          : 'done',
      };
    })
    .filter((item): item is FormConfigOperationLogEntry => Boolean(item));
}

export function buildFormConfigOperationLogStorageKey(params: {
  db: unknown;
  modelName: unknown;
  actionId: unknown;
  viewId: unknown;
  page: unknown;
  userId: unknown;
}) {
  const db = String(params.db || '').trim() || 'default';
  const modelName = String(params.modelName || '').trim() || 'unknown';
  const action = Number(params.actionId || 0) || 0;
  const view = String(params.viewId || '0').trim() || '0';
  const page = String(params.page || '').trim();
  const userId = String(params.userId || '').trim() || 'anonymous';
  return `sc_form_config_operation_log:${db}:${modelName}:action:${action}:view:${view}:page:${page}:user:${userId}`;
}

export function createFormConfigOperationLogEntry(
  action: string,
  summary: string,
  operator: string,
  status: FormConfigOperationLogEntry['status'] = 'pending',
): FormConfigOperationLogEntry | null {
  const normalizedAction = String(action || '').trim();
  const normalizedSummary = String(summary || '').trim();
  if (!normalizedAction || !normalizedSummary) return null;
  const now = new Date();
  return {
    id: `${now.getTime()}-${Math.random().toString(36).slice(2, 8)}`,
    at: now.toISOString(),
    operator: String(operator || '当前用户').trim(),
    action: normalizedAction,
    summary: normalizedSummary,
    status,
  };
}

export function appendFormConfigOperationLogEntry(
  entries: FormConfigOperationLogEntry[],
  entry: FormConfigOperationLogEntry,
  limit = 50,
) {
  const currentKey = formConfigOperationCoalesceKey(entry.action, entry.summary);
  const latest = entries[0];
  const latestKey = latest ? formConfigOperationCoalesceKey(latest.action, latest.summary) : '';
  if (entry.status === 'pending' && latest?.status === 'pending' && currentKey && currentKey === latestKey) {
    return [
      { ...entry, id: latest.id },
      ...entries.slice(1),
    ].slice(0, limit);
  }
  return [entry, ...entries].slice(0, limit);
}

export function formConfigOperationSubject(action: string, summary: string) {
  const normalizedAction = String(action || '').trim();
  const normalizedSummary = String(summary || '').trim();
  if (!normalizedSummary) return '';
  if (normalizedAction === '调整页面列数') return '页面';
  const match = normalizedSummary.match(/^(.+?)\s+(设置为|移动到|调整到|调整为|改为|添加到)/);
  if (match?.[1]) return match[1].trim();
  return normalizedSummary;
}

export function formConfigOperationCoalesceKey(action: string, summary: string) {
  const normalizedAction = String(action || '').trim();
  const subject = formConfigOperationSubject(normalizedAction, summary);
  if (!normalizedAction || !subject) return '';
  return `${normalizedAction}:${subject}`;
}

export function formatFormConfigOperationTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
}

export function formConfigOperationStatusLabel(status: FormConfigOperationLogEntry['status']) {
  if (status === 'pending') return '待保存';
  if (status === 'saved') return '已保存';
  if (status === 'reverted') return '已撤销';
  return '已执行';
}

function escapeFormConfigOperationRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function formatFormConfigOperationSummary(summary: string, replacementEntries: Array<[string, string]>) {
  let text = String(summary || '').trim();
  if (!text) return '';
  replacementEntries.forEach(([fieldKey, label]) => {
    const pattern = new RegExp(`(^|[^A-Za-z0-9_])${escapeFormConfigOperationRegExp(fieldKey)}(?=$|[^A-Za-z0-9_])`, 'g');
    text = text.replace(pattern, `$1${label}`);
  });
  return text;
}

export function readableFallbackFieldLabel(fieldKey: string) {
  const key = String(fieldKey || '').trim();
  if (!key) return '';
  return key
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function lowCodeFieldSizeLabel(size: LowCodeFieldSize) {
  if (size === 'wide') return '加宽';
  if (size === 'full') return '整行';
  if (size === 'large') return '大输入框';
  return '标准';
}

export function normalizeConfigPageLabel(value: string) {
  return String(value || '')
    .trim()
    .replace(/^新建\s*/, '')
    .replace(/\s*这个页面$/, '')
    .trim();
}

export function buildFormFieldConfigScope(pageLabel: string) {
  const page = normalizeConfigPageLabel(pageLabel) || '当前表单';
  return {
    scope: page,
    saveTarget: '只影响当前页面，不影响其它页面',
    summary: `本页调整${page}的字段名称、显示、顺序、分组和新增字段，保存后只影响当前页面。`,
  };
}

export function formatFormConfigAuditSummary(
  result: FormConfigAuditResult | null | undefined,
  showTechnicalDetails: boolean,
) {
  if (!result) return '';
  if (!showTechnicalDetails) {
    const layoutText = result.hasBusinessConfigFormLayout
      ? (result.layoutMatchesFields ? '，布局已对齐' : '，布局需要重新保存')
      : '';
    const takeoverText = result.skippedLegacyPolicyFields.length
      ? `，${result.skippedLegacyPolicyFields.length} 个旧字段规则已由当前页面配置接管`
      : '';
    return `检查通过，当前页面 ${result.businessConfigFormFields.length} 个字段配置可生效${layoutText}${takeoverText}。`;
  }
  const conflictText = result.skippedLegacyPolicyFields.length
    ? `业务配置已接管旧规则字段：${result.skippedLegacyPolicyFields.join('、')}`
    : '无被接管的旧规则字段';
  const activeLegacyText = result.activeLegacyPolicyFields.length
    ? `系统补充配置生效：${result.activeLegacyPolicyFields.join('、')}`
    : '无系统补充配置生效';
  const layoutText = result.hasBusinessConfigFormLayout
    ? `正式布局 ${result.businessConfigFormLayoutFields.length}，${result.layoutMatchesFields ? '字段顺序一致' : '字段顺序不一致'}`
    : '未固化正式布局';
  return `配置字段 ${result.businessConfigFormFields.length} / 系统补充配置 ${result.legacyPolicyFields.length}，${layoutText}，${conflictText}，${activeLegacyText}`;
}

export function isSuggestedInternalFormField(fieldKey: string, label = '') {
  const name = String(fieldKey || '').trim();
  const text = `${name} ${String(label || '').trim()}`.toLowerCase();
  if (!name) return false;
  if (name.startsWith('legacy_source_')) return true;
  if (name.startsWith('activity_') || name.startsWith('alias_') || name.startsWith('message_') || name.startsWith('rating_')) return true;
  if (['access_token', 'access_url', 'access_warning', 'website_message_ids'].includes(name)) return true;
  return [
    'last updated on',
    'project manager',
    '初始录入',
    '录入时间',
    '来源',
    '协作成员',
    'collaborator',
  ].some((keyword) => text.includes(keyword));
}

export function normalizeFieldGroupTitle(value: unknown) {
  return String(value || '').trim();
}

export function isReadableFieldGroupTitle(value: unknown) {
  const text = normalizeFieldGroupTitle(value);
  if (!text) return false;
  if (['group', 'page', 'notebook', 'sheet', 'container'].includes(text.toLowerCase())) return false;
  if (/^默认分组\s*\d*$/i.test(text)) return false;
  if (/^[a-z][a-z0-9_:. -]*$/i.test(text) && /[_:.]/.test(text)) return false;
  return true;
}

export function inferLowCodeLayoutColumns(nodes: NativeLayoutLikeNode[]): 1 | 2 | 3 | null {
  const counts: Record<1 | 2 | 3, number> = { 1: 0, 2: 0, 3: 0 };
  const directFieldCount = (node: NativeLayoutLikeNode) => {
    const children = Array.isArray(node?.children) ? node.children as NativeLayoutLikeNode[] : [];
    return children.filter((child) => nativeLayoutNodeType(child) === 'field' && child.visible !== false).length;
  };
  const walk = (items: NativeLayoutLikeNode[]) => {
    items.forEach((node) => {
      const attrs = node && typeof node.attributes === 'object' && node.attributes
        ? node.attributes as Record<string, unknown>
        : {};
      const nodeType = nativeLayoutNodeType(node);
      const columns = normalizeLowCodeColumnsOrNull(
        attrs.col
        ?? attrs.columns
        ?? attrs.cols
        ?? (node as { col?: unknown; cols?: unknown; columns?: unknown }).col
        ?? (node as { col?: unknown; cols?: unknown; columns?: unknown }).cols
        ?? (node as { col?: unknown; cols?: unknown; columns?: unknown }).columns,
      );
      const fieldCount = directFieldCount(node);
      const hasFields = fieldCount > 0;
      if (columns && (nodeType === 'group' || hasFields)) {
        counts[columns] += Math.max(1, fieldCount);
      }
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeLayoutLikeNode[]);
      });
    });
  };
  walk(nodes);
  const ranked = (Object.entries(counts) as Array<[string, number]>)
    .filter(([, count]) => count > 0)
    .sort((left, right) => right[1] - left[1] || Number(right[0]) - Number(left[0]));
  return ranked.length ? normalizeLowCodeColumnsOrNull(ranked[0][0]) : null;
}

export function layoutHasReadableFieldGroups(nodes: NativeLayoutLikeNode[]) {
  let found = false;
  const visit = (rows: NativeLayoutLikeNode[]) => {
    rows.forEach((node) => {
      if (found || !node || typeof node !== 'object') return;
      const row = node as Record<string, unknown>;
      const type = nativeLayoutNodeType(node);
      const title = normalizeFieldGroupTitle(row.string || row.label || row.title);
      const children = Array.isArray(row.children) ? row.children as NativeLayoutLikeNode[] : [];
      const directFields = children
        .filter((child) => nativeLayoutNodeType(child) === 'field' && String(child?.name || '').trim())
        .length;
      if (type === 'group' && isReadableFieldGroupTitle(title) && directFields) {
        found = true;
        return;
      }
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const childRows = row[key];
        if (Array.isArray(childRows)) visit(childRows as NativeLayoutLikeNode[]);
      });
    });
  };
  visit(nodes);
  return found;
}

export function fieldStructureTitle(pageTitle: string, groupTitle: string) {
  const page = String(pageTitle || '').trim();
  const group = String(groupTitle || '').trim();
  if (page && group && page !== group) return `${page} / ${group}`;
  return page || group || '主表区域';
}

export function collectNativeLayoutGroupTitles(nodes: NativeLayoutLikeNode[]) {
  const titles: string[] = [];
  const walk = (rows: NativeLayoutLikeNode[], pageTitle = '', groupTitle = '') => {
    rows.forEach((node) => {
      const type = nativeLayoutNodeType(node);
      const title = String(node?.string || node?.label || '').trim();
      const nextPage = type === 'page' && title ? title : pageTitle;
      const nextGroup = type === 'group' && isReadableFieldGroupTitle(title)
        ? fieldStructureTitle(nextPage, title)
        : groupTitle;
      if (type === 'page' && isReadableFieldGroupTitle(title)) titles.push(title);
      if (type === 'group' && isReadableFieldGroupTitle(nextGroup)) titles.push(nextGroup);
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeLayoutLikeNode[], nextPage, nextGroup);
      });
    });
  };
  walk(Array.isArray(nodes) ? nodes : []);
  return titles;
}

export function collectNativeFieldStructureGroups(nodes: NativeLayoutLikeNode[]) {
  const groups = new Map<string, { key: string; title: string; fieldKeys: string[] }>();
  const fieldSeen = new Set<string>();
  let anonymousGroupIndex = 0;
  const addField = (title: string, fieldKey: string) => {
    const normalizedField = String(fieldKey || '').trim();
    if (!normalizedField || fieldSeen.has(normalizedField)) return;
    fieldSeen.add(normalizedField);
    const groupTitle = title || '主表区域';
    const groupKey = groupTitle;
    if (!groups.has(groupKey)) groups.set(groupKey, { key: groupKey, title: groupTitle, fieldKeys: [] });
    groups.get(groupKey)?.fieldKeys.push(normalizedField);
  };
  const rawChildren = (node: NativeLayoutLikeNode) => {
    const rows: NativeLayoutLikeNode[] = [];
    (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
      const children = node?.[key];
      if (Array.isArray(children)) rows.push(...children as NativeLayoutLikeNode[]);
    });
    return rows;
  };
  const directVisibleFieldNames = (node: NativeLayoutLikeNode) => rawChildren(node)
    .filter((child) => nativeLayoutNodeType(child) === 'field')
    .map((child) => String(child?.name || '').trim())
    .filter(Boolean);
  const groupTitleForNode = (node: NativeLayoutLikeNode, pageTitle: string, groupTitle: string) => {
    const type = nativeLayoutNodeType(node);
    const title = String(node?.string || node?.label || '').trim();
    if (type === 'page' && isReadableFieldGroupTitle(title)) return title;
    if (type === 'group' && isReadableFieldGroupTitle(title)) return fieldStructureTitle(pageTitle, title);
    if (type === 'group' && directVisibleFieldNames(node).length) {
      anonymousGroupIndex += 1;
      return fieldStructureTitle(pageTitle, `默认分组 ${anonymousGroupIndex}`);
    }
    return groupTitle;
  };
  const walk = (rows: NativeLayoutLikeNode[], pageTitle = '', groupTitle = '') => {
    rows.forEach((node) => {
      const type = nativeLayoutNodeType(node);
      const title = String(node?.string || node?.label || '').trim();
      const nextPage = type === 'page' && title ? title : pageTitle;
      const nextGroup = groupTitleForNode(node, nextPage, groupTitle);
      const name = String(node?.name || '').trim();
      if (type === 'field' && name) addField(fieldStructureTitle(nextPage, nextGroup), name);
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeLayoutLikeNode[], nextPage, nextGroup);
      });
    });
  };
  walk(Array.isArray(nodes) ? nodes : []);
  return Array.from(groups.values());
}

export function fieldGroupTitleMatches(value: unknown, target: string) {
  const current = normalizeFieldGroupTitle(value);
  const normalizedTarget = normalizeFieldGroupTitle(target);
  if (!current || !normalizedTarget) return false;
  return current === normalizedTarget
    || current.endsWith(` / ${normalizedTarget}`)
    || normalizedTarget.endsWith(` / ${current}`);
}

export function buildCurrentFormGroupOptions(params: {
  nativeGroups: Array<{ title: string }>;
  runtimeGroupTitles: string[];
  fieldKeys: string[];
  resolveDraftGroupTitle: (fieldKey: string) => string;
}) {
  const groupTitles = params.nativeGroups
    .map((group) => normalizeFieldGroupTitle(group.title))
    .filter(Boolean);
  params.runtimeGroupTitles.forEach((title) => {
    const normalized = normalizeFieldGroupTitle(title);
    if (normalized) groupTitles.push(normalized);
  });
  params.fieldKeys.forEach((fieldKey) => {
    const title = params.resolveDraftGroupTitle(fieldKey);
    if (title) groupTitles.push(title);
  });
  const businessGroupTitles = groupTitles.filter((title) => title !== '主表区域');
  return Array.from(new Set(businessGroupTitles.length ? businessGroupTitles : groupTitles));
}

export function buildFormDesignerGroupNavigatorItems(params: {
  nativeGroups: Array<{ title: string; fieldKeys: string[] }>;
  fieldKeys: string[];
  selectedGroupTitle: string;
  resolveDraftGroupTitle: (fieldKey: string) => string;
}) {
  const configurableFields = new Set(params.fieldKeys);
  const byTitle = new Map<string, { title: string; fieldKeys: string[] }>();
  params.nativeGroups.forEach((group) => {
    const title = normalizeFieldGroupTitle(group.title);
    if (!title || title === '主表区域') return;
    const fieldKeys = group.fieldKeys.filter((fieldKey) => configurableFields.has(fieldKey));
    if (!fieldKeys.length) return;
    if (!byTitle.has(title)) byTitle.set(title, { title, fieldKeys: [] });
    byTitle.get(title)?.fieldKeys.push(...fieldKeys);
  });
  params.fieldKeys.forEach((fieldKey) => {
    const title = params.resolveDraftGroupTitle(fieldKey);
    if (!title || title === '主表区域') return;
    if (!byTitle.has(title)) byTitle.set(title, { title, fieldKeys: [] });
    const entry = byTitle.get(title);
    if (entry && !entry.fieldKeys.includes(fieldKey)) entry.fieldKeys.push(fieldKey);
  });
  return Array.from(byTitle.values()).map((item) => ({
    ...item,
    count: item.fieldKeys.length,
    active: Boolean(params.selectedGroupTitle && fieldGroupTitleMatches(item.title, params.selectedGroupTitle)),
  }));
}

export function buildFormDesignerSearchableFieldRows(params: {
  orderedFieldKeys: string[];
  fallbackFieldKeys: string[];
  nativeGroups: Array<{ title: string; fieldKeys: string[] }>;
  resolveDraftGroupTitle: (fieldKey: string) => string;
  resolveFieldLabel: (fieldKey: string) => string;
}) {
  const keys = params.orderedFieldKeys.length ? params.orderedFieldKeys : params.fallbackFieldKeys;
  return keys.map((fieldKey) => {
    const groupTitle = normalizeFieldGroupTitle(params.resolveDraftGroupTitle(fieldKey))
      || params.nativeGroups.find((group) => group.fieldKeys.includes(fieldKey))?.title
      || '业务配置字段';
    return {
      fieldKey,
      label: params.resolveFieldLabel(fieldKey),
      groupTitle,
    };
  });
}

export function filterFormDesignerFieldRows(
  rows: Array<{ fieldKey: string; label: string; groupTitle: string }>,
  queryText: string,
  defaultLimit = 8,
) {
  const query = String(queryText || '').trim().toLowerCase();
  if (!query) return rows.slice(0, defaultLimit);
  return rows.filter((row) => (
    row.label.toLowerCase().includes(query)
    || row.fieldKey.toLowerCase().includes(query)
    || row.groupTitle.toLowerCase().includes(query)
  ));
}

export function resolveSelectedFormSettingsFieldGroupTitle(params: {
  fieldKey: string;
  draftGroupTitle: string;
  nativeGroups: Array<{ title: string; fieldKeys: string[] }>;
  fallbackDraftTitle: string;
}) {
  const fieldKey = String(params.fieldKey || '').trim();
  if (!fieldKey) return '';
  if (params.draftGroupTitle) return params.draftGroupTitle;
  const nativeGroup = params.nativeGroups.find((group) => group.fieldKeys.includes(fieldKey));
  return nativeGroup?.title || params.fallbackDraftTitle || '业务配置字段';
}

export function mergeLowCodeLayoutWithRuntimeGroupShells<T extends NativeLayoutLikeNode>(base: T[], runtime: NativeLayoutLikeNode[]): T[] {
  if (!Array.isArray(base) || !base.length) return base;
  const existing = new Set(
    collectNativeLayoutGroupTitles(base)
      .map((title) => normalizeFieldGroupTitle(title))
      .filter(Boolean),
  );
  const missing = collectNativeLayoutGroupTitles(runtime)
    .map((title) => normalizeFieldGroupTitle(title))
    .filter((title) => title && title !== '主表区域' && !existing.has(title));
  if (!missing.length) return base;
  return [
    ...base,
    ...Array.from(new Set(missing)).map((title) => ({
      type: 'group',
      string: title,
      label: title,
      children: [],
    } as T)),
  ];
}
