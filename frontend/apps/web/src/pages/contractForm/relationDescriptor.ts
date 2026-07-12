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

export function relationCreateMode(descriptor?: FieldDescriptor): 'page' | 'quick' | 'none' {
  const entry = relationEntry(descriptor);
  if (!entry) return 'none';
  if (entry.createMode === 'page' && entry.actionId) return 'page';
  if (entry.createMode === 'quick' && entry.canCreate) return 'quick';
  if (entry.model === 'sc.dictionary' && entry.canCreate && Object.keys(entry.defaultVals || {}).length) {
    return 'quick';
  }
  return 'none';
}

export function relationInlineCreate(descriptor?: FieldDescriptor) {
  const entry = relationEntry(descriptor);
  if (!entry?.inlineCreate?.enabled) {
    return {
      enabled: false,
      createOnNoMatch: false,
      nameField: '',
      match: entry?.inlineCreate?.match || 'exact_label',
    };
  }
  return {
    enabled: true,
    createOnNoMatch: entry.inlineCreate.createOnNoMatch,
    nameField: entry.inlineCreate.nameField,
    match: entry.inlineCreate.match,
  };
}

export function dynamicDomainDependencyFields(descriptor?: FieldDescriptor) {
  const raw = (descriptor as Record<string, unknown> | undefined)?.domain;
  if (typeof raw !== 'string' || !raw.trim()) return [];
  const deps = new Set<string>();
  const tuplePattern = /\(['"]([\w.]+)['"]\s*,\s*['"]([=!<>]{1,2}|in|not in|ilike|like)['"]\s*,\s*([A-Za-z_]\w*)\)/g;
  let match: RegExpExecArray | null;
  while ((match = tuplePattern.exec(raw.trim()))) {
    const valueField = match[3];
    if (valueField) deps.add(valueField);
  }
  return Array.from(deps);
}

export function isBlockAllDomain(domain: unknown) {
  return Array.isArray(domain)
    && domain.length === 1
    && Array.isArray(domain[0])
    && String(domain[0][0] || '') === 'id'
    && String(domain[0][1] || '') === '='
    && Number(domain[0][2]) === -1;
}

export function relationSearchDialogContract(descriptor?: FieldDescriptor): Record<string, unknown> {
  const entry = (descriptor as Record<string, unknown> | undefined)?.relation_entry;
  if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return {};
  const dialog = (entry as Record<string, unknown>).search_dialog;
  if (!dialog || typeof dialog !== 'object' || Array.isArray(dialog)) return {};
  return dialog as Record<string, unknown>;
}

export function fallbackRelationSearchColumns(descriptor?: FieldDescriptor): RelationSearchColumn[] {
  return [{
    name: 'display_name',
    label: String(descriptor?.string || '名称'),
  }];
}

export function relationSearchColumnsFromContract(dialog: Record<string, unknown>): RelationSearchColumn[] {
  const columns = Array.isArray(dialog.columns) ? dialog.columns : [];
  const out: RelationSearchColumn[] = [];
  for (const item of columns) {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    const name = String(row.name || row.field || '').trim();
    if (!name || name === 'id') continue;
    const label = String(row.label || row.string || name).trim() || name;
    out.push({ name, label });
    if (out.length >= 8) break;
  }
  return out;
}

export function normalizeRelationSearchColumns(
  data: Record<string, unknown> | undefined,
  fallbackDescriptor?: FieldDescriptor,
): RelationSearchColumn[] {
  const fields = data?.fields && typeof data.fields === 'object'
    ? data.fields as Record<string, FieldDescriptor>
    : {};
  const views = data?.views && typeof data.views === 'object'
    ? data.views as Record<string, unknown>
    : {};
  const tree = views.tree && typeof views.tree === 'object'
    ? views.tree as Record<string, unknown>
    : {};
  const rawColumns = Array.isArray(tree.columns_schema) && tree.columns_schema.length
    ? tree.columns_schema
    : Array.isArray(tree.columns)
      ? tree.columns
      : [];
  const out: RelationSearchColumn[] = [];
  for (const item of rawColumns) {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : null;
    const name = String(row?.name || item || '').trim();
    if (!name || name === 'id') continue;
    const field = fields[name];
    const label = String(row?.label || row?.string || field?.string || name).trim();
    out.push({ name, label });
    if (out.length >= 6) break;
  }
  if (!out.length) return fallbackRelationSearchColumns(fallbackDescriptor);
  return out;
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
