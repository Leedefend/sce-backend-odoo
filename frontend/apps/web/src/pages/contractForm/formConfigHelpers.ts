import type { FormConfigAuditResult, FormConfigOperationLogEntry, LowCodeFieldSize } from './types';
import {
  lowCodeFieldSizeClass,
  normalizeLowCodeColumns,
  normalizeLowCodeColumnsOrNull,
  normalizeLowCodeFieldSize,
} from './fieldUtils';
import { nativeLayoutNodeType, nativeNodeFieldInfo, type NativeLayoutLikeNode } from './nativeLayoutUtils';

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

export function persistFormConfigOperationLogEntries(
  key: string,
  entries: FormConfigOperationLogEntry[],
  storage: Storage | undefined,
  limit = 50,
) {
  if (!key || !storage) return;
  try {
    storage.setItem(key, JSON.stringify(entries.slice(0, limit)));
  } catch {
    // ignore session storage failures
  }
}

export function readFormConfigOperationLogEntries(
  key: string,
  storage: Storage | undefined,
  operator: string,
) {
  if (!key || !storage) return [];
  try {
    const raw = storage.getItem(key);
    return normalizeFormConfigOperationLogEntries(raw ? JSON.parse(raw) : [], operator);
  } catch {
    return [];
  }
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

export function moveFieldOrderRelative(
  order: string[],
  sourceFieldKey: string,
  targetFieldKey: string,
  placement: 'before' | 'after' = 'before',
): string[] | null {
  const source = String(sourceFieldKey || '').trim();
  const target = String(targetFieldKey || '').trim();
  if (!source || !target || source === target) return null;
  const draft = [...order];
  const from = draft.indexOf(source);
  const to = draft.indexOf(target);
  if (from < 0 || to < 0) return null;
  const [moved] = draft.splice(from, 1);
  const targetIndex = draft.indexOf(target);
  if (targetIndex < 0) return null;
  const insertIndex = placement === 'after' ? targetIndex + 1 : targetIndex;
  draft.splice(insertIndex, 0, moved);
  return draft;
}

export function moveFieldOrderByDelta(order: string[], fieldKey: string, delta: number): string[] | null {
  const key = String(fieldKey || '').trim();
  const draft = [...order];
  const from = draft.indexOf(key);
  const to = from + Number(delta || 0);
  if (!key || from < 0 || to < 0 || to >= draft.length) return null;
  const [moved] = draft.splice(from, 1);
  draft.splice(to, 0, moved);
  return draft;
}

export function moveFieldOrderToGroupEnd(params: {
  order: string[];
  fieldKey: string;
  groupTitle: string;
  resolveFieldGroupTitle: (fieldKey: string) => string;
}): { order: string[]; anchorFieldKey: string; groupTitle: string } | null {
  const source = String(params.fieldKey || '').trim();
  const normalizedTargetGroup = normalizeFieldGroupTitle(params.groupTitle);
  if (!source || !normalizedTargetGroup) return null;
  const draft = params.order.filter((key) => key !== source);
  const targetGroupFieldKeys = draft.filter((key) => (
    fieldGroupTitleMatches(params.resolveFieldGroupTitle(key), normalizedTargetGroup)
  ));
  const anchorFieldKey = targetGroupFieldKeys[targetGroupFieldKeys.length - 1] || '';
  const anchorIndex = anchorFieldKey ? draft.indexOf(anchorFieldKey) : -1;
  draft.splice(anchorIndex >= 0 ? anchorIndex + 1 : draft.length, 0, source);
  return { order: draft, anchorFieldKey, groupTitle: normalizedTargetGroup };
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

export function buildFormConfigFieldLabelReplacementEntries(params: {
  cachedLabels: Record<string, string>;
  nativeLabels: Record<string, string>;
  activeRows: Array<{ fieldKey: string; label: string }>;
  fieldKeys: string[];
  resolveContractLabel: (fieldKey: string) => string;
  resolveDescriptorLabel: (fieldKey: string) => string;
}) {
  const labels = new Map<string, string>();
  const remember = (fieldKey: string, label: string) => {
    const key = String(fieldKey || '').trim();
    const value = String(label || '').trim();
    if (!key || !value || key === value) return;
    labels.set(key, value);
  };
  Object.entries(params.cachedLabels).forEach(([key, label]) => remember(key, label));
  Object.entries(params.nativeLabels).forEach(([key, label]) => remember(key, label));
  params.activeRows.forEach((row) => remember(row.fieldKey, row.label));
  params.fieldKeys.forEach((fieldKey) => {
    const key = String(fieldKey || '').trim();
    if (!key || labels.has(key)) return;
    remember(key, params.resolveContractLabel(key) || params.resolveDescriptorLabel(key));
  });
  return Array.from(labels.entries()).sort((left, right) => right[0].length - left[0].length);
}

export function resolveFormDesignFieldLabel(params: {
  fieldKey: string;
  selectedFieldKey: string;
  selectedFieldLabel: string;
  cachedLabels: Record<string, string>;
  nativeLabels: Record<string, string>;
  activeRows: Array<{ fieldKey: string; label: string }>;
  resolveContractLabel: (fieldKey: string) => string;
  resolveDescriptorLabel: (fieldKey: string) => string;
}) {
  const key = String(params.fieldKey || '').trim();
  if (!key) return '';
  const selectedLabel = params.selectedFieldKey === key ? String(params.selectedFieldLabel || '').trim() : '';
  const cachedLabel = String(params.cachedLabels[key] || '').trim();
  const structuredLabel = String(params.resolveContractLabel(key) || '').trim();
  const nativeLabel = String(params.nativeLabels[key] || '').trim();
  const rowLabel = String(params.activeRows.find((item) => item.fieldKey === key)?.label || '').trim();
  const descriptorLabel = String(params.resolveDescriptorLabel(key) || '').trim();
  for (const label of [selectedLabel, cachedLabel, structuredLabel, nativeLabel, rowLabel, descriptorLabel]) {
    if (label && label !== key) return label;
  }
  return rowLabel || readableFallbackFieldLabel(key);
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

export function normalizeFormConfigAuditResult(raw: Record<string, unknown>): FormConfigAuditResult {
  const normalizeNames = (value: unknown) => (Array.isArray(value) ? value : [])
    .map((item) => String(item || '').trim())
    .filter(Boolean);
  return {
    businessConfigFormFields: normalizeNames(raw.business_config_form_fields),
    businessConfigFormLayoutFields: normalizeNames(raw.business_config_form_layout_fields),
    hasBusinessConfigFormLayout: Boolean(raw.has_business_config_form_layout),
    layoutMatchesFields: Boolean(raw.layout_matches_fields),
    legacyPolicyFields: normalizeNames(raw.legacy_policy_fields),
    skippedLegacyPolicyFields: normalizeNames(raw.skipped_legacy_policy_fields),
    activeLegacyPolicyFields: normalizeNames(raw.active_legacy_policy_fields),
    hasConflict: Boolean(raw.has_conflict),
  };
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

export function effectiveFieldGroupTitleFromDrafts(params: {
  fieldKey: string;
  draftGroups: Record<string, string>;
  nativeBaseGroups: Record<string, string>;
  savedBaseGroups: Record<string, string>;
}) {
  const key = String(params.fieldKey || '').trim();
  if (!key) return '';
  const draft = normalizeFieldGroupTitle(params.draftGroups[key]);
  const nativeBase = normalizeFieldGroupTitle(params.nativeBaseGroups[key]);
  const savedBase = normalizeFieldGroupTitle(params.savedBaseGroups[key]);
  if (draft && draft !== nativeBase) return draft;
  return savedBase || draft || nativeBase;
}

export function changedFieldVisibilityFromDrafts(params: {
  fieldKeys: string[];
  draft: Record<string, boolean>;
  base: Record<string, boolean>;
  dirtyKeys: Record<string, boolean>;
}) {
  return params.fieldKeys.reduce<Record<string, boolean>>((acc, fieldKey) => {
    if (!Object.prototype.hasOwnProperty.call(params.draft, fieldKey)) return acc;
    if (
      params.dirtyKeys[fieldKey]
      || (
        Object.prototype.hasOwnProperty.call(params.base, fieldKey)
        && params.draft[fieldKey] !== params.base[fieldKey]
      )
    ) {
      acc[fieldKey] = params.draft[fieldKey];
    }
    return acc;
  }, {});
}

export function changedFieldGroupFromDrafts(params: {
  draftGroups: Record<string, string>;
  nativeBaseGroups: Record<string, string>;
  savedBaseGroups: Record<string, string>;
  resolveDraftTitle: (fieldKey: string) => string;
}) {
  return Object.keys(params.draftGroups).reduce<Record<string, string>>((acc, fieldKey) => {
    const key = String(fieldKey || '').trim();
    const draft = params.resolveDraftTitle(key);
    const base = normalizeFieldGroupTitle(params.savedBaseGroups[key] || params.nativeBaseGroups[key]);
    if (key && draft && draft !== base) acc[key] = draft;
    return acc;
  }, {});
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

export function extractLowCodeLayoutDraftState(
  formSpec: Record<string, unknown>,
  runtimeColumns: 1 | 2 | 3,
) {
  const explicitColumns = normalizeLowCodeColumnsOrNull(formSpec.columns ?? (formSpec as { cols?: unknown }).cols);
  const columns = explicitColumns || runtimeColumns;
  const groupVisible: Record<string, boolean> = {};
  const groupColumns: Record<string, 1 | 2 | 3> = {};
  const fieldSize: Record<string, LowCodeFieldSize> = {};
  const inferFieldSize = (row: Record<string, unknown>) => {
    const rawClass = String(row.class || row.className || '').trim();
    return normalizeLowCodeFieldSize(
      row.field_size
      || row.fieldSize
      || row.size
      || (rawClass.includes('field--large') ? 'large'
        : (rawClass.includes('field--full') ? 'full'
          : (rawClass.includes('field--wide') ? 'wide' : 'normal'))),
    );
  };
  const collectLayout = (nodes: unknown, activeGroup = '') => {
    for (const raw of Array.isArray(nodes) ? nodes : []) {
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) continue;
      const node = raw as Record<string, unknown>;
      const nodeType = String(node.type || node.kind || node.containerType || '').trim().toLowerCase();
      const title = normalizeFieldGroupTitle(node.string || node.label || node.title);
      const groupTitle = nodeType === 'group' && title ? title : activeGroup;
      if (nodeType === 'group' && title) {
        groupVisible[title] = node.visible !== false;
        groupColumns[title] = normalizeLowCodeColumns(
          node.columns ?? node.cols ?? ((node.attributes && typeof node.attributes === 'object' && !Array.isArray(node.attributes))
            ? (node.attributes as Record<string, unknown>).columns ?? (node.attributes as Record<string, unknown>).cols
            : undefined),
          columns,
        );
      }
      const fieldName = String(node.name || node.field || node.field_name || '').trim();
      if (nodeType === 'field' && fieldName) fieldSize[fieldName] = inferFieldSize(node);
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        collectLayout(node[key], groupTitle);
      });
    }
  };
  collectLayout(formSpec.layout);
  const formFields = Array.isArray(formSpec.fields) ? formSpec.fields as Array<Record<string, unknown>> : [];
  formFields.forEach((row) => {
    const fieldName = String(row.name || row.field || row.field_name || '').trim();
    if (!fieldName || fieldSize[fieldName]) return;
    fieldSize[fieldName] = inferFieldSize(row);
  });
  return {
    columns,
    columnsConfigured: Boolean(explicitColumns),
    groupVisible,
    groupColumns,
    fieldSize,
  };
}

export function extractLowCodeFormFieldDraftState(formSpec: Record<string, unknown>) {
  const fields = Array.isArray(formSpec.fields) ? formSpec.fields as Array<Record<string, unknown>> : [];
  const orderedFieldNames = fields
    .map((row) => ({ name: String(row?.name || row?.field || '').trim(), sequence: Number(row?.sequence || row?.order || 0) }))
    .filter((row) => row.name)
    .sort((a, b) => a.sequence - b.sequence)
    .map((row) => row.name);
  const visibility: Record<string, boolean> = {};
  const groups: Record<string, string> = {};
  fields.forEach((row) => {
    const key = String(row?.name || row?.field || '').trim();
    if (!key) return;
    visibility[key] = row?.visible !== false;
    const rawGroupTitle = row?.group_title || row?.groupTitle || row?.section_title || row?.sectionTitle;
    const groupTitle = isReadableFieldGroupTitle(rawGroupTitle) ? normalizeFieldGroupTitle(rawGroupTitle) : '';
    if (groupTitle) groups[key] = groupTitle;
  });
  return {
    fields,
    orderedFieldNames,
    visibility,
    groups,
  };
}

export type LowCodeLayoutDraftRow = {
  section: 'form' | 'list' | 'kanban';
  object: string;
  field: string;
};

export function collectLowCodeLayoutFromViewOrchestration(views: Record<string, unknown>, modelName: string) {
  const out: LowCodeLayoutDraftRow[] = [];
  const collect = (section: LowCodeLayoutDraftRow['section'], viewKey: string, rowKey: string) => {
    const spec = views[viewKey] && typeof views[viewKey] === 'object' && !Array.isArray(views[viewKey])
      ? views[viewKey] as Record<string, unknown>
      : {};
    const rows = Array.isArray(spec[rowKey]) ? spec[rowKey] as unknown[] : [];
    rows.forEach((row) => {
      const item = row && typeof row === 'object' ? row as Record<string, unknown> : {};
      const field = String(item.name || item.field || '').trim();
      if (field) out.push({ section, object: modelName, field });
    });
  };
  collect('form', 'form', 'fields');
  collect('list', 'tree', 'columns');
  collect('list', 'list', 'columns');
  collect('kanban', 'kanban', 'fields');
  return out;
}

export function buildLowCodeViewOrchestration(params: {
  availableFieldNames: string[];
  layoutDraft: LowCodeLayoutDraftRow[];
  formOrderDraft: string[];
  formOrderEditable: boolean;
  formColumns: 1 | 2 | 3;
  resolveFieldLabel: (name: string) => string;
  resolveFieldGroupTitle: (name: string) => string;
  resolveFieldVisible: (name: string, groupTitle: string) => boolean;
  resolveGroupVisible: (title: string) => boolean;
  resolveGroupColumns: (title: string) => 1 | 2 | 3;
  resolveFieldSize: (name: string) => LowCodeFieldSize;
}) {
  const availableFields = new Set(params.availableFieldNames.map((name) => String(name || '').trim()).filter(Boolean));
  const sectionFields = (section: LowCodeLayoutDraftRow['section']) => params.layoutDraft
    .filter((row) => row.section === section)
    .map((row) => String(row.field || '').trim())
    .filter((name) => name && availableFields.has(name));
  const formDraftNames = params.formOrderDraft.filter((name) => availableFields.has(name));
  const formNames = params.formOrderEditable && formDraftNames.length
    ? formDraftNames
    : (sectionFields('form').length ? sectionFields('form') : formDraftNames);
  const listNames = sectionFields('list');
  const kanbanNames = sectionFields('kanban');
  const views: Record<string, unknown> = {};
  if (formNames.length) {
    const groupBuckets = new Map<string, string[]>();
    formNames.forEach((name) => {
      const title = params.resolveFieldGroupTitle(name);
      const key = title || '业务配置字段';
      if (!groupBuckets.has(key)) groupBuckets.set(key, []);
      groupBuckets.get(key)?.push(name);
    });
    const layoutGroups = Array.from(groupBuckets.entries())
      .filter(([title]) => params.resolveGroupVisible(title))
      .map(([title, names]) => ({
        type: 'group',
        string: title,
        visible: params.resolveGroupVisible(title),
        columns: params.resolveGroupColumns(title),
        children: names.map((name) => {
          const fieldSize = params.resolveFieldSize(name);
          const fieldClass = lowCodeFieldSizeClass(fieldSize);
          return {
            type: 'field',
            name,
            ...(fieldClass ? { class: fieldClass, field_size: fieldSize } : {}),
          };
        }),
      }));
    views.form = {
      columns: params.formColumns,
      fields: formNames.map((name, index) => {
        const groupTitle = params.resolveFieldGroupTitle(name);
        const fieldSize = params.resolveFieldSize(name);
        const fieldClass = lowCodeFieldSizeClass(fieldSize);
        return {
          name,
          label: params.resolveFieldLabel(name),
          visible: params.resolveFieldVisible(name, groupTitle || '业务配置字段'),
          sequence: (index + 1) * 10,
          ...(groupTitle ? { group_title: groupTitle } : {}),
          ...(fieldClass ? { class: fieldClass, field_size: fieldSize } : {}),
        };
      }),
      sections: Array.from(groupBuckets.entries()).map(([title, names], index) => ({
        name: `business_config_section_${index + 1}`,
        title,
        visible: params.resolveGroupVisible(title),
        columns: params.resolveGroupColumns(title),
        sequence: (index + 1) * 10,
        fields: [...names],
      })),
      layout: layoutGroups,
    };
  }
  if (listNames.length) {
    views.tree = {
      columns: listNames.map((name, index) => ({
        name,
        label: params.resolveFieldLabel(name),
        visible: true,
        sequence: (index + 1) * 10,
      })),
    };
  }
  if (kanbanNames.length) {
    views.kanban = {
      fields: kanbanNames.map((name, index) => ({
        name,
        label: params.resolveFieldLabel(name),
        visible: true,
        sequence: (index + 1) * 10,
      })),
      slots: { primary: kanbanNames.slice(0, 3) },
    };
  }
  return Object.keys(views).length ? { views } : undefined;
}

export function lowCodeLayoutFieldLabelFromNodes(name: string, ...nodeGroups: NativeLayoutLikeNode[][]) {
  const targetName = String(name || '').trim();
  if (!targetName) return '';
  const walk = (nodes: NativeLayoutLikeNode[]): string => {
    for (const node of nodes) {
      if (!node || typeof node !== 'object') continue;
      const nodeType = String(node.type || (node as { containerType?: string }).containerType || '').trim().toLowerCase();
      const nodeName = String(node.name || '').trim();
      if (nodeType === 'field' && nodeName === targetName) {
        const fieldInfo = nativeNodeFieldInfo(node);
        const label = String(
          node.string
          || node.label
          || fieldInfo.string
          || fieldInfo.label
          || '',
        ).trim();
        if (label) return label;
      }
      for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
        const children = node[key];
        if (!Array.isArray(children)) continue;
        const found = walk(children as NativeLayoutLikeNode[]);
        if (found) return found;
      }
    }
    return '';
  };
  for (const nodes of nodeGroups) {
    const label = walk(nodes);
    if (label) return label;
  }
  return '';
}

export function normalizeLowCodeApplyParams(raw: Record<string, unknown>): Record<string, unknown> {
  const params = { ...raw };
  for (const key of ['action_id', 'actionId', 'view_id', 'viewId']) {
    if (!(key in params)) continue;
    const numeric = Number(params[key] || 0);
    params[key] = Number.isFinite(numeric) && numeric >= 0 ? Math.trunc(numeric) : 0;
  }
  return params;
}

export function buildLowCodeApplyBaseParams(params: {
  actionId: unknown;
  viewId: unknown;
  targetParams: Record<string, unknown>;
  modelName: string;
}) {
  return normalizeLowCodeApplyParams({
    action_id: Number(params.actionId || 0) || 0,
    view_id: Number(params.viewId || 0) || 0,
    view_type: 'form',
    ...params.targetParams,
    model: String(params.modelName || ''),
  });
}

export function contractFieldSequenceFromOrder(fieldOrder: string[], fieldKey: string, fallback = 100) {
  const index = fieldOrder.indexOf(String(fieldKey || '').trim());
  return index >= 0 ? (index + 1) * 10 : fallback;
}

export function formConfigSaveOperationSummary(params: {
  hasFieldOrderChanges: boolean;
  changedVisibility: Record<string, boolean>;
  changedGroups: Record<string, string>;
  hasFormLayoutChanges: boolean;
  hasGroupLayoutChanges: boolean;
  hasFieldLayoutChanges: boolean;
}) {
  const parts: string[] = [];
  if (params.hasFieldOrderChanges) parts.push('字段顺序');
  const groupCount = Object.keys(params.changedGroups).length;
  if (groupCount) parts.push(`${groupCount} 个字段分组`);
  const visibilityCount = Object.keys(params.changedVisibility).length;
  if (visibilityCount) parts.push(`${visibilityCount} 个字段显示状态`);
  if (params.hasFormLayoutChanges || params.hasGroupLayoutChanges || params.hasFieldLayoutChanges) parts.push('表单布局');
  return parts.length ? `保存并发布：${parts.join('、')}` : '保存并发布表单设置';
}

export function buildLowCodeReturnQuery(params: {
  routeQuery: Record<string, unknown>;
  modelName: string;
  actionId: unknown;
  openPagesFlag: string;
}) {
  const query: Record<string, string> = {};
  const routeQueryText = (key: string) => {
    const value = params.routeQuery[key];
    if (Array.isArray(value)) return String(value[0] || '').trim();
    return String(value || '').trim();
  };
  ['root_menu_xmlid', 'db', 'menu_id'].forEach((key) => {
    const value = routeQueryText(key);
    if (value) query[key] = value;
  });
  const modelName = String(params.modelName || '').trim();
  const actionId = Number(params.actionId || 0) || 0;
  if (modelName) query.model = modelName;
  if (actionId) query.action_id = String(actionId);
  query[params.openPagesFlag] = '1';
  ['page_label', 'view_id', 'role_key'].forEach((key) => {
    const value = routeQueryText(key);
    if (value) query[key] = value;
  });
  return query;
}

export function buildLowCodePreviewQuery(params: {
  routeQuery: Record<string, unknown>;
  returnToBusinessConfigFlag: string;
  openPagesFlag: string;
}) {
  const query: Record<string, string | string[]> = {};
  Object.entries(params.routeQuery).forEach(([key, raw]) => {
    if (['config_mode', 'activity_page_id'].includes(key)) return;
    if (Array.isArray(raw)) {
      const values = raw.map((item) => String(item || '').trim()).filter(Boolean);
      if (values.length) query[key] = values;
      return;
    }
    const value = String(raw || '').trim();
    if (value) query[key] = value;
  });
  query[params.returnToBusinessConfigFlag] = '1';
  query[params.openPagesFlag] = '1';
  return query;
}

export function lowCodeScopedContractName(modelName: string, params: Record<string, unknown>) {
  const actionId = Number(params.action_id || params.actionId || 0);
  const viewId = Number(params.view_id || params.viewId || 0);
  return `view_orchestration:${modelName}:form:action:${Number.isFinite(actionId) ? Math.trunc(actionId) : 0}:view:${Number.isFinite(viewId) ? Math.trunc(viewId) : 0}`;
}

export function normalizeLowCodeContractListRows(rows: unknown) {
  return (Array.isArray(rows) ? rows : [])
    .map((item) => {
      const row = item && typeof item === 'object' && !Array.isArray(item)
        ? item as Record<string, unknown>
        : {};
      return {
        id: Number(row.id || 0),
        name: String(row.name || '').trim(),
        model: String(row.model || '').trim(),
        status: String(row.status || 'draft').trim() || 'draft',
        version_no: Number(row.version_no || 1),
      };
    })
    .filter((row) => row.name);
}

export function lowCodeViewOrchestrationFromContractResponse(response: unknown): Record<string, unknown> {
  const root = response && typeof response === 'object' && !Array.isArray(response)
    ? response as Record<string, unknown>
    : {};
  const json = root.contract_json && typeof root.contract_json === 'object' && !Array.isArray(root.contract_json)
    ? root.contract_json as Record<string, unknown>
    : {};
  const orchestration = json.view_orchestration && typeof json.view_orchestration === 'object' && !Array.isArray(json.view_orchestration)
    ? json.view_orchestration as Record<string, unknown>
    : {};
  return orchestration;
}

export function lowCodeViewsFromContractResponse(response: unknown): Record<string, unknown> {
  const orchestration = lowCodeViewOrchestrationFromContractResponse(response);
  return orchestration.views && typeof orchestration.views === 'object' && !Array.isArray(orchestration.views)
    ? orchestration.views as Record<string, unknown>
    : {};
}

export function lowCodeFormSpecFromViews(views: Record<string, unknown>): Record<string, unknown> {
  return views.form && typeof views.form === 'object' && !Array.isArray(views.form)
    ? views.form as Record<string, unknown>
    : {};
}

export function lowCodeLayoutFromFormSpec(formSpec: Record<string, unknown>) {
  return Array.isArray(formSpec.layout) ? formSpec.layout as NativeLayoutLikeNode[] : [];
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
    } as unknown as T)),
  ];
}
