import type { FormConfigOperationLogEntry } from './types';

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
