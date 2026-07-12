import type { FieldDescriptor } from '@sc/schema';
import { toPositiveInt } from '../../app/contractRuntime';
import { cleanRelationDisplayLabel } from './fieldUtils';
import type { RelationOption, RelationSearchColumn, RelationUiLabels } from './types';

export function relationEntry(descriptor?: FieldDescriptor) {
  const entry = (descriptor as Record<string, unknown> | undefined)?.relation_entry;
  if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return null;
  const row = entry as Record<string, unknown>;
  const actionId = toPositiveInt(row.action_id);
  const menuId = toPositiveInt(row.menu_id);
  const createModeRaw = String(row.create_mode || '').trim().toLowerCase();
  const createMode = createModeRaw === 'page' || createModeRaw === 'quick' ? createModeRaw : 'disabled';
  const defaultVals = row.default_vals && typeof row.default_vals === 'object' && !Array.isArray(row.default_vals)
    ? (row.default_vals as Record<string, unknown>)
    : {};
  const defaultFromFields = row.default_from_fields && typeof row.default_from_fields === 'object' && !Array.isArray(row.default_from_fields)
    ? (row.default_from_fields as Record<string, unknown>)
    : {};
  const domain = Array.isArray(row.domain) ? row.domain as unknown[] : [];
  const inlineRaw = row.inline_create && typeof row.inline_create === 'object' && !Array.isArray(row.inline_create)
    ? row.inline_create as Record<string, unknown>
    : {};
  const switchRaw = row.switch_context && typeof row.switch_context === 'object' && !Array.isArray(row.switch_context)
    ? row.switch_context as Record<string, unknown>
    : {};
  return {
    model: String(row.model || '').trim(),
    actionId,
    menuId,
    canRead: row.can_read !== false,
    canOpen: row.can_open !== false,
    canCreate: Boolean(row.can_create),
    createMode,
    defaultVals,
    defaultFromFields,
    domain,
    order: String(row.order || '').trim(),
    displayField: String(row.display_field || row.displayField || '').trim(),
    switchContext: {
      enabled: switchRaw.enabled === true,
      codeField: String(switchRaw.code_field || switchRaw.codeField || '').trim(),
      labelField: String(switchRaw.label_field || switchRaw.labelField || '').trim(),
      defaultValuesField: String(switchRaw.default_values_field || switchRaw.defaultValuesField || '').trim(),
      defaultClearFields: Array.isArray(switchRaw.default_clear_fields)
        ? switchRaw.default_clear_fields.map((item) => String(item || '').trim()).filter(Boolean)
        : [],
    },
    reasonCode: String(row.reason_code || '').trim(),
    inlineCreate: {
      enabled: inlineRaw.enabled === true,
      createOnNoMatch: inlineRaw.create_on_no_match === true,
      nameField: String(inlineRaw.name_field || 'name').trim() || 'name',
      match: String(inlineRaw.match || '').trim() || 'exact_label',
    },
  };
}

export function relationColorField(descriptor?: FieldDescriptor) {
  const row = descriptor && typeof descriptor === 'object' ? descriptor as Record<string, unknown> : {};
  const options = row.widget_options && typeof row.widget_options === 'object' && !Array.isArray(row.widget_options)
    ? row.widget_options as Record<string, unknown>
    : row.options && typeof row.options === 'object' && !Array.isArray(row.options)
      ? row.options as Record<string, unknown>
      : {};
  const colorField = String(options.color_field || '').trim();
  return colorField || '';
}

export function relationReadFields(descriptor?: FieldDescriptor) {
  const fields = new Set(['id', 'name', 'display_name']);
  const entry = relationEntry(descriptor);
  if (entry?.displayField) fields.add(entry.displayField);
  if (entry?.switchContext?.enabled) {
    if (entry.switchContext.codeField) fields.add(entry.switchContext.codeField);
    if (entry.switchContext.labelField) fields.add(entry.switchContext.labelField);
    if (entry.switchContext.defaultValuesField) fields.add(entry.switchContext.defaultValuesField);
  }
  const colorField = relationColorField(descriptor);
  if (colorField) fields.add(colorField);
  return Array.from(fields);
}

export function parseRelationDefaultValues(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object' && !Array.isArray(value)) return value as Record<string, unknown>;
  const raw = String(value || '').trim();
  if (!raw) return {};
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? parsed as Record<string, unknown>
      : {};
  } catch {
    return {};
  }
}

export function relationOptionFromRow(row: Record<string, unknown>, descriptor?: FieldDescriptor): RelationOption | null {
  const id = Number(row.id);
  if (!Number.isFinite(id) || id <= 0) return null;
  const entry = relationEntry(descriptor);
  const displayField = String(entry?.displayField || '').trim();
  const displayValue = displayField ? row[displayField] : '';
  const label = String(displayValue || row.display_name || row.name || `#${id}`).trim();
  const colorField = relationColorField(descriptor);
  const colorValue = colorField ? Number(row[colorField]) : NaN;
  const switchContract = entry?.switchContext?.enabled ? entry.switchContext : null;
  const switchCode = switchContract?.codeField ? String(row[switchContract.codeField] || '').trim() : '';
  const switchLabel = switchContract?.labelField ? String(row[switchContract.labelField] || '').trim() : '';
  const defaultValues = switchContract?.defaultValuesField
    ? parseRelationDefaultValues(row[switchContract.defaultValuesField])
    : {};
  return {
    id: Math.trunc(id),
    label: cleanRelationDisplayLabel(label, id),
    ...(switchCode ? { switchContext: { code: switchCode, label: switchLabel || label, defaultValues } } : {}),
    ...(Number.isFinite(colorValue) ? { color: Math.trunc(colorValue) } : {}),
  };
}

export function relationUiLabels(descriptor?: FieldDescriptor): RelationUiLabels {
  const entry = (descriptor as Record<string, unknown> | undefined)?.relation_entry;
  const labels = entry && typeof entry === 'object' && !Array.isArray(entry)
    ? (entry as Record<string, unknown>).ui_labels
    : null;
  if (!labels || typeof labels !== 'object' || Array.isArray(labels)) return {};
  return Object.entries(labels as Record<string, unknown>).reduce<RelationUiLabels>((acc, [key, value]) => {
    const label = String(value || '').trim();
    if (key && label) acc[key] = label;
    return acc;
  }, {});
}

export function relationUiLabel(descriptor: FieldDescriptor | undefined, key: string, fallback = '') {
  return relationUiLabels(descriptor)[key] || fallback || key;
}

export function relationSearchReadFields(columns: RelationSearchColumn[], dialog: Record<string, unknown> = {}) {
  const out = new Set<string>(['id', 'display_name', 'name']);
  const contractFields = Array.isArray(dialog.read_fields) ? dialog.read_fields : [];
  for (const field of contractFields) {
    const name = String(field || '').trim();
    if (name) out.add(name);
  }
  for (const column of columns) {
    if (column.name) out.add(column.name);
  }
  return Array.from(out);
}
