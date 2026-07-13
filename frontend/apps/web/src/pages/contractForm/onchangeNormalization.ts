import type { FieldDescriptor } from '@sc/schema';
import type { OnchangeLinePatch, OnchangeResponse } from '../../api/onchange';
import {
  fieldType,
  normalizeRelationIds,
  parseMany2oneDisplay,
  toDateInputValue,
  toDatetimeInputValue,
} from './fieldUtils';
import type { RelationOption } from './types';
import { normalizeContractFieldValue } from './valueUtils';

export type OnchangeRequestPayloadBuildInput = {
  fields?: Record<string, FieldDescriptor>;
  formData: Record<string, unknown>;
  originalValues: Record<string, unknown>;
  recordId: number | null;
  buildOne2manyValue: (name: string, mode: 'write' | 'onchange') => unknown;
};

export function buildOnchangeRequestPayload(params: OnchangeRequestPayloadBuildInput) {
  const out: Record<string, unknown> = {};
  Object.keys(params.fields || {}).forEach((name) => {
    const descriptor = params.fields?.[name];
    out[name] = normalizeContractFieldValue({
      name,
      value: params.formData[name],
      descriptor,
      originalValue: params.originalValues[name],
      mode: 'onchange',
      buildOne2manyValue: params.buildOne2manyValue,
    });
  });
  if (params.recordId) out.id = params.recordId;
  return out;
}

export type NormalizedOnchangeResponse = {
  patch: Record<string, unknown>;
  modifiersPatch: Record<string, Record<string, unknown>>;
  linePatches: OnchangeLinePatch[];
  warnings: Array<{ title?: string; message?: string; reason_code?: string }>;
};

export function normalizeOnchangeResponse(response?: OnchangeResponse | null): NormalizedOnchangeResponse {
  const patch = response?.patch && typeof response.patch === 'object'
    ? response.patch as Record<string, unknown>
    : {};
  const modifiersPatch = response?.modifiers_patch && typeof response.modifiers_patch === 'object'
    ? response.modifiers_patch as Record<string, Record<string, unknown>>
    : {};
  return {
    patch,
    modifiersPatch,
    linePatches: Array.isArray(response?.line_patches) ? response.line_patches : [],
    warnings: Array.isArray(response?.warnings) ? response.warnings : [],
  };
}

export type NormalizedOnchangeFieldPatch =
  | { kind: 'x2many'; fieldType: 'many2many' | 'one2many'; value: unknown[] }
  | {
    kind: 'many2one';
    option: RelationOption | null;
    nextId: number | false;
    value: number | false | [number, string];
    keyword: string;
  }
  | { kind: 'date'; value: string }
  | { kind: 'datetime'; value: string }
  | { kind: 'plain'; value: unknown };

export function normalizeOnchangeFieldPatch(params: {
  descriptor?: FieldDescriptor | null;
  readonly?: boolean;
  value: unknown;
}): NormalizedOnchangeFieldPatch {
  const ttype = fieldType(params.descriptor);
  if (ttype === 'many2many' || ttype === 'one2many') {
    return { kind: 'x2many', fieldType: ttype, value: Array.isArray(params.value) ? params.value : [] };
  }
  if (ttype === 'many2one') {
    const option = parseMany2oneDisplay(params.value);
    const ids = normalizeRelationIds(params.value);
    const nextId = ids.length ? ids[0] : false;
    return {
      kind: 'many2one',
      option,
      nextId,
      value: params.readonly && option ? [option.id, option.label] : nextId,
      keyword: option?.label || '',
    };
  }
  if (ttype === 'date') return { kind: 'date', value: toDateInputValue(params.value) };
  if (ttype === 'datetime') return { kind: 'datetime', value: toDatetimeInputValue(params.value) };
  return { kind: 'plain', value: params.value };
}
