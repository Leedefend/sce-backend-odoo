import type { FormConfigOperationLogEntry } from './types';
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
