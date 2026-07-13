import type { FieldDescriptor } from '@sc/schema';
import {
  fieldType,
  normalizeRelationIds,
  parseMany2oneDisplay,
  toDateInputValue,
  toDatetimeInputValue,
} from './fieldUtils';
import type { RelationOption } from './types';

export type FormRecordHydrationTarget = {
  formData: Record<string, unknown>;
  relationOptions: Record<string, RelationOption[]>;
  relationKeywords: Record<string, string>;
  upsertRelationOption: (fieldName: string, option: RelationOption | null) => void;
  initOne2manyRows: (fieldName: string, source: unknown) => void;
};

export function applyIncomingFormFieldValue(params: {
  fieldName: string;
  descriptor?: FieldDescriptor;
  incoming: unknown;
  target: FormRecordHydrationTarget;
}) {
  const name = String(params.fieldName || '').trim();
  if (!name) return;
  const ttype = fieldType(params.descriptor);
  const { formData, relationOptions, relationKeywords, upsertRelationOption, initOne2manyRows } = params.target;
  if (ttype === 'many2many' || ttype === 'one2many') {
    formData[name] = Array.isArray(params.incoming) ? params.incoming : [];
    if (ttype === 'one2many') initOne2manyRows(name, formData[name]);
    return;
  }
  if (ttype === 'many2one') {
    const option = parseMany2oneDisplay(params.incoming);
    upsertRelationOption(name, option);
    const ids = normalizeRelationIds(params.incoming);
    formData[name] = ids.length ? ids[0] : false;
    const matched = ids.length
      ? (relationOptions[name] || []).find((item) => item.id === ids[0])
      : null;
    relationKeywords[name] = matched?.label || option?.label || '';
    return;
  }
  if (ttype === 'date') {
    formData[name] = toDateInputValue(params.incoming);
    return;
  }
  if (ttype === 'datetime') {
    formData[name] = toDatetimeInputValue(params.incoming);
    return;
  }
  formData[name] = params.incoming;
}

export function snapshotOriginalFormValues(fieldNames: string[], formData: Record<string, unknown>) {
  return fieldNames.reduce<Record<string, unknown>>((acc, name) => {
    const value = formData[name];
    if (Array.isArray(value)) {
      acc[name] = [...value];
    } else if (value && typeof value === 'object') {
      acc[name] = JSON.parse(JSON.stringify(value));
    } else {
      acc[name] = value;
    }
    return acc;
  }, {});
}
