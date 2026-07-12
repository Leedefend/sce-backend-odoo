import { fromDatetimeInputValue, toDateInputValue, toDatetimeInputValue } from './fieldUtils';
import type { One2ManyColumn } from './types';

export function normalizeOne2manyColumnValue(column: One2ManyColumn, value: unknown) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (ttype === 'boolean') return Boolean(value);
  if (ttype === 'integer') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? Math.trunc(parsed) : false;
  }
  if (ttype === 'float' || ttype === 'monetary') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : false;
  }
  if (ttype === 'date') return toDateInputValue(value) || false;
  if (ttype === 'datetime') return fromDatetimeInputValue(value);
  if (ttype === 'selection') return String(value ?? '').trim() || false;
  return String(value ?? '');
}

export function one2manyColumnInputType(column: One2ManyColumn) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (ttype === 'integer' || ttype === 'float' || ttype === 'monetary') return 'number';
  if (ttype === 'date') return 'date';
  if (ttype === 'datetime') return 'datetime-local';
  return 'text';
}

export function one2manyColumnDisplayValue(column: One2ManyColumn, value: unknown) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (value === false || value === null || value === undefined) return '';
  if (ttype === 'date') return toDateInputValue(value);
  if (ttype === 'datetime') return toDatetimeInputValue(value);
  return String(value ?? '');
}

export function isOne2manyEmptyValue(column: One2ManyColumn, value: unknown) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (ttype === 'boolean') return value === false || value === null || value === undefined;
  if (ttype === 'integer' || ttype === 'float' || ttype === 'monetary') {
    return value === false || value === null || value === undefined || Number.isNaN(Number(value));
  }
  if (ttype === 'date' || ttype === 'datetime' || ttype === 'selection') {
    return !String(value ?? '').trim() || value === false;
  }
  return !String(value ?? '').trim();
}

export function formRuntimeReasonLabel(reason: unknown): string {
  const raw = String(reason || '').trim();
  const key = raw.toUpperCase();
  const mapping: Record<string, string> = {
    ACTION_UNSUPPORTED: '当前操作暂不可用',
    BUSINESS_RULE_FAILED: '业务规则限制',
    CONFLICT: '数据已变化',
    FIELD_CREATE_DISABLED: '当前字段暂不支持新增',
    INLINE_CREATE_READY: '可在明细中新增',
    MISSING_PARAMS: '参数不完整',
    NETWORK_ERROR: '网络连接问题',
    NOT_FOUND: '记录不存在',
    PERMISSION_DENIED: '权限不足',
    RELATION_CREATE_FORBIDDEN: '关联数据暂不允许新增',
    RELATION_READ_FORBIDDEN: '关联数据暂不可查看',
    SYSTEM_ERROR: '系统处理问题',
    VALIDATION_ERROR: '校验未通过',
    WRITE_FAILED: '保存失败',
  };
  if (!raw) return '待确认';
  return mapping[key] || raw.replace(/[_-]+/g, ' ').toLowerCase().replace(/(^|\s)\S/g, (s) => s.toUpperCase());
}

export function formRuntimeRowStateLabel(state: unknown): string {
  const raw = String(state || '').trim().toLowerCase();
  const mapping: Record<string, string> = {
    create: '新增明细',
    update: '已更新明细',
    remove: '已移除明细',
    keep: '保持当前明细',
  };
  return mapping[raw] || '已同步明细变化';
}

export function formRuntimeCommandHintLabel(commands: unknown[]): string {
  const values = commands.map((item) => Number(item)).filter((item) => Number.isFinite(item));
  if (!values.length) return '请检查明细变化';
  const labels = values.map((item) => {
    if (item === 0) return '新增';
    if (item === 1) return '更新';
    if (item === 2) return '删除';
    if (item === 3) return '解除关联';
    if (item === 4) return '关联已有';
    if (item === 5) return '清空';
    if (item === 6) return '替换为指定明细';
    return '同步明细';
  });
  return Array.from(new Set(labels)).join('、');
}
