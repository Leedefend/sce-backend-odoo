import type { FieldDescriptor } from '@sc/schema';
import { buildX2ManyCommands } from '../../app/x2manyCommands';
import { fieldType, fromDatetimeInputValue, toDateInputValue } from './fieldUtils';

export function isMissingRequiredValue(value: unknown) {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim().length === 0;
  if (typeof value === 'number') return !Number.isFinite(value) || value <= 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'boolean') return false;
  if (typeof value === 'object') return Object.keys(value as Record<string, unknown>).length === 0;
  return false;
}

export function normalizeComparable(value: unknown) {
  if (Array.isArray(value) && value.every((item) => typeof item === 'number')) {
    return JSON.stringify([...value].sort((a, b) => a - b));
  }
  if (Array.isArray(value)) return JSON.stringify(value);
  if (value && typeof value === 'object') return JSON.stringify(value);
  return String(value ?? '');
}

export function parseNumeric(text: unknown) {
  const raw = String(text ?? '').trim();
  if (!raw) return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : null;
}

export function isRequiredFieldEmptyByType(value: unknown, fieldType: string) {
  const ttype = String(fieldType || '').trim().toLowerCase();
  if (Array.isArray(value)) return value.length === 0;
  if (ttype === 'many2one') return !Number(value || 0);
  if (ttype === 'many2many' || ttype === 'one2many') return !Array.isArray(value) || value.length === 0;
  if (value === false || value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  return false;
}

export function normalizeRouteDefault(value: unknown) {
  const raw = Array.isArray(value) ? value[value.length - 1] : value;
  if (typeof raw !== 'string') return raw;
  const normalized = raw.trim();
  if (!normalized) return '';
  if (normalized === 'true') return true;
  if (normalized === 'false') return false;
  if (/^-?\d+(\.\d+)?$/.test(normalized)) return Number(normalized);
  return normalized;
}

export function resolveNavigationUrl(url: string, origin: string) {
  const raw = String(url || '').trim();
  if (!raw) return '';
  if (/^https?:\/\//i.test(raw)) return raw;
  if (raw.startsWith('/')) return `${origin}${raw}`;
  return raw;
}

export function normalizeContractFieldValue(params: {
  name: string;
  value: unknown;
  descriptor?: FieldDescriptor;
  originalValue: unknown;
  mode?: 'write' | 'onchange';
  buildOne2manyValue: (name: string, mode: 'write' | 'onchange') => unknown;
}) {
  const ttype = fieldType(params.descriptor);
  if (ttype === 'boolean') return Boolean(params.value);
  if (ttype === 'integer') {
    const parsed = parseNumeric(params.value);
    return parsed === null ? false : Math.trunc(parsed);
  }
  if (ttype === 'float' || ttype === 'monetary') {
    const parsed = parseNumeric(params.value);
    return parsed === null ? false : parsed;
  }
  if (ttype === 'many2one') {
    if (Array.isArray(params.value) && typeof params.value[0] === 'number') return params.value[0];
    if (typeof params.value === 'number') return params.value;
    const parsed = parseNumeric(params.value);
    return parsed === null ? false : Math.trunc(parsed);
  }
  if (ttype === 'many2many') {
    return buildX2ManyCommands({
      kind: 'many2many',
      current: params.value,
      original: params.originalValue,
      mode: params.mode || 'write',
    });
  }
  if (ttype === 'one2many') return params.buildOne2manyValue(params.name, params.mode || 'write');
  if (ttype === 'date') {
    const normalized = toDateInputValue(params.value);
    return normalized || false;
  }
  if (ttype === 'datetime') return fromDatetimeInputValue(params.value);
  if (ttype === 'char' || ttype === 'text' || ttype === 'html') return String(params.value ?? '');
  return params.value;
}
