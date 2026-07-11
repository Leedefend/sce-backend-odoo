import { computed, type Ref } from 'vue';
import { uniqueFields } from '../runtime/actionViewRequestRuntime';
import {
  collectUnifiedPageContractV2FieldWidgets,
  collectUnifiedPageContractV2FieldStatus,
  resolveUnifiedPageContractV2,
  resolveUnifiedPageContractV2ListProfile,
} from '../contracts/unifiedPageContractV2';

type Dict = Record<string, unknown>;

type UseActionViewContractShapeRuntimeOptions = {
  pageText: (key: string, fallback: string) => string;
  actionContract: Ref<Record<string, unknown> | null>;
  advancedFields: Ref<string[]>;
  activeGroupByField: Ref<string>;
};

type KanbanProfile = {
  titleField: string;
  primaryFields: string[];
  secondaryFields: string[];
  statusFields: string[];
  metricFields: string[];
  quickActionCount: number;
};

type SortOption = {
  label: string;
  value: string;
};

type ListColumnOption = {
  name: string;
  label: string;
  optional: string;
  defaultVisible: boolean;
  sortable?: boolean;
  type?: string;
  widget?: string;
  cellRole?: string;
  mutation?: Record<string, unknown>;
  selection?: Array<{ value: string; label: string }>;
  toneByValue?: Record<string, string>;
};

function normalizeFieldNames(rows: unknown): string[] {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((item) => {
      if (typeof item === 'string' || typeof item === 'number') return String(item || '').trim();
      const row = (item || {}) as Dict;
      return String(row.field || row.name || row.field_name || '').trim();
    })
    .filter((name) => /^[A-Za-z_][A-Za-z0-9_]*$/.test(name));
}

function collectSlotFieldNames(value: unknown): string[] {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return [];
  return Object.values(value as Dict).flatMap((slotValue) => {
    if (typeof slotValue === 'string' || typeof slotValue === 'number') {
      return [String(slotValue || '').trim()].filter(Boolean);
    }
    if (Array.isArray(slotValue)) {
      return normalizeFieldNames(slotValue);
    }
    if (slotValue && typeof slotValue === 'object') {
      return normalizeFieldNames([slotValue]);
    }
    return [];
  });
}

function collectDisplayRowLabels(rows: unknown, labels: Record<string, string>) {
  if (!Array.isArray(rows)) return;
  rows.forEach((item) => {
    if (!item || typeof item !== 'object' || Array.isArray(item)) return;
    const row = item as Dict;
    const name = String(row.name || row.field || row.field_name || '').trim();
    const label = String(row.label || row.string || row.display_label || '').trim();
    if (name && label) labels[name] = label;
  });
}

export function extractKanbanFieldsFromContract(contract: unknown): string[] {
  const typed = (contract || {}) as Dict;
  const directViews = typed.views as Dict | undefined;
  if (directViews) {
    const kanbanBlock = (directViews.kanban || {}) as Dict;
    const nestedKanban = (kanbanBlock.kanban || {}) as Dict;
    const fields = uniqueFields([
      ...normalizeFieldNames(kanbanBlock.fields),
      ...normalizeFieldNames(nestedKanban.fields),
      ...collectSlotFieldNames(kanbanBlock.slots),
      ...collectSlotFieldNames(nestedKanban.slots),
    ]);
    if (fields.length) return fields;
  }
  const v2 = resolveUnifiedPageContractV2(typed);
  if (String(v2?.pageInfo?.viewType || '').trim() === 'kanban') {
    return uniqueFields(
      collectUnifiedPageContractV2FieldWidgets(typed)
        .map((widget) => String(widget.fieldCode || '').trim())
        .filter((name) => /^[A-Za-z_][A-Za-z0-9_]*$/.test(name)),
    );
  }
  return [];
}

export function extractAdvancedViewFieldsFromContract(contract: unknown, mode: string): string[] {
  const typed = (contract || {}) as Dict;
  const directViews = typed.views as Dict | undefined;
  const viewBlock = (directViews?.[mode] || {}) as Dict;
  const nested = (viewBlock[mode] || {}) as Dict;
  const fallbackNames = ['name', 'display_name', 'id'];
  const blockValue = (key: string) => viewBlock[key] ?? nested[key];
  if (mode === 'pivot') {
    const measures = normalizeFieldNames(blockValue('measures'));
    const dims = normalizeFieldNames(blockValue('dimensions'));
    return uniqueFields([...dims, ...measures, ...fallbackNames]);
  }
  if (mode === 'graph') {
    const measure = String(blockValue('measure') || '').trim();
    const dim = String(blockValue('dimension') || '').trim();
    const measures = normalizeFieldNames(blockValue('measures'));
    const dims = normalizeFieldNames(blockValue('dimensions'));
    return uniqueFields([dim, measure, ...dims, ...measures, ...fallbackNames].filter(Boolean));
  }
  if (mode === 'calendar' || mode === 'gantt') {
    const dateStart = String(blockValue('date_start') || '').trim();
    const dateStop = String(blockValue('date_stop') || '').trim();
    const slotFields = [
      ...collectSlotFieldNames(blockValue('date_slots')),
      ...collectSlotFieldNames(blockValue('resource_slots')),
      ...collectSlotFieldNames(blockValue('color_slots')),
      ...collectSlotFieldNames(blockValue('dependency_slots')),
      ...normalizeFieldNames(blockValue('fields')),
    ];
    return uniqueFields([dateStart, dateStop, ...slotFields, ...fallbackNames].filter(Boolean));
  }
  if (mode === 'activity') {
    const activityField = String(blockValue('field') || '').trim();
    const slotFields = [
      ...collectSlotFieldNames(blockValue('activity_type_slots')),
      ...collectSlotFieldNames(blockValue('deadline_slots')),
      ...collectSlotFieldNames(blockValue('assignee_slots')),
      ...normalizeFieldNames(blockValue('fields')),
    ];
    return uniqueFields([activityField, ...slotFields, ...fallbackNames].filter(Boolean));
  }
  if (mode === 'dashboard') {
    const kpis = Array.isArray(blockValue('kpis')) ? blockValue('kpis') as unknown[] : [];
    const cards = Array.isArray(blockValue('cards')) ? blockValue('cards') as unknown[] : [];
    const guessed = [...kpis, ...cards]
      .map((item) => String(((item as Dict).field || '')).trim())
      .filter(Boolean);
    const slotFields = [
      ...collectSlotFieldNames(blockValue('metric_slots')),
      ...collectSlotFieldNames(blockValue('chart_slots')),
    ];
    return uniqueFields([...guessed, ...slotFields, ...fallbackNames]);
  }
  return fallbackNames;
}

export function extractViewFieldLabelsFromContract(contract: unknown, mode: string): Record<string, string> {
  const typed = (contract || {}) as Dict;
  const directViews = typed.views as Dict | undefined;
  const viewBlock = (directViews?.[mode] || {}) as Dict;
  const nested = (viewBlock[mode] || {}) as Dict;
  const labels: Record<string, string> = {};
  collectDisplayRowLabels(viewBlock.fields, labels);
  collectDisplayRowLabels(viewBlock.columns, labels);
  collectDisplayRowLabels(viewBlock.columns_schema || viewBlock.columnsSchema, labels);
  collectDisplayRowLabels(viewBlock.measures, labels);
  collectDisplayRowLabels(viewBlock.dimensions, labels);
  collectDisplayRowLabels(viewBlock.cards, labels);
  collectDisplayRowLabels(viewBlock.kpis, labels);
  collectDisplayRowLabels(nested.fields, labels);
  collectDisplayRowLabels(nested.columns, labels);
  collectDisplayRowLabels(nested.columns_schema || nested.columnsSchema, labels);
  collectDisplayRowLabels(nested.measures, labels);
  collectDisplayRowLabels(nested.dimensions, labels);
  collectDisplayRowLabels(nested.cards, labels);
  collectDisplayRowLabels(nested.kpis, labels);
  return labels;
}

export function useActionViewContractShapeRuntime(options: UseActionViewContractShapeRuntimeOptions) {
  const contractColumnLabels = computed<Record<string, string>>(() => {
    const contract = options.actionContract.value || {};
    const rows = contract.fields || {};
    const labels = Object.entries(rows).reduce<Record<string, string>>((acc, [name, descriptor]) => {
      const descriptorRow = (descriptor || {}) as Dict;
      const label = String(descriptorRow.string || '').trim();
      if (label) acc[name] = label;
      return acc;
    }, {});
    collectUnifiedPageContractV2FieldWidgets(contract).forEach((widget) => {
      if (widget.fieldCode && widget.label) labels[widget.fieldCode] = widget.label;
    });
    const listProfile = resolveUnifiedPageContractV2ListProfile(contract);
    const semanticPage = (contract.semantic_page || {}) as Dict;
    const listSemantics = (semanticPage.list_semantics || {}) as Dict;
    const semanticColumns = Array.isArray(listSemantics.columns) ? (listSemantics.columns as Array<Dict>) : [];
    const directViews = ((contract as Dict).views || {}) as Dict;
    Object.values(directViews).forEach((viewBlock) => {
      if (!viewBlock || typeof viewBlock !== 'object' || Array.isArray(viewBlock)) return;
      const block = viewBlock as Dict;
      collectDisplayRowLabels(block.fields, labels);
      collectDisplayRowLabels(block.columns, labels);
      collectDisplayRowLabels(block.columns_schema || block.columnsSchema, labels);
      collectDisplayRowLabels(block.measures, labels);
      collectDisplayRowLabels(block.dimensions, labels);
      collectDisplayRowLabels(block.cards, labels);
      collectDisplayRowLabels(block.kpis, labels);
    });
    Object.entries((listProfile.column_labels || {}) as Dict).forEach(([name, labelRaw]) => {
      const label = String(labelRaw || '').trim();
      if (label) labels[name] = label;
    });
    semanticColumns.forEach((row) => {
      const name = String(row.name || '').trim();
      const label = String(row.label || '').trim();
      if (name && label) labels[name] = label;
    });
    const head = ((contract as Dict).head && typeof (contract as Dict).head === 'object')
      ? (contract as Dict).head as Dict
      : {};
    const modelName = String((contract as Dict).model || head.model || '').trim();
    if (modelName === 'project.project') {
      labels.name = labels.name || '名称';
      labels.business_nature = labels.business_nature || '经营性质';
    }
    return labels;
  });

  function extractColumnsFromContract(contract: unknown, sceneColumns: string[] = []) {
    const preferred = Array.isArray(sceneColumns)
      ? sceneColumns.map((item) => String(item || '').trim()).filter(Boolean)
      : [];
    const typed = (contract || {}) as Dict;
    const v2Fields = collectUnifiedPageContractV2FieldWidgets(typed).map((widget) => widget.fieldCode).filter(Boolean);
    if (v2Fields.length) return applyPreferredColumnOrder(v2Fields, preferred);
    const directViews = typed.views as Dict | undefined;
    if (directViews) {
      const treeBlock = (directViews.tree || directViews.list || {}) as Dict;
      const treeColumns = treeBlock.columns;
      if (Array.isArray(treeColumns) && treeColumns.length) {
        return applyPreferredColumnOrder(treeColumns.map((item) => String(item || '')).filter(Boolean), preferred);
      }
      const treeSchema = (treeBlock.columnsSchema || treeBlock.columns_schema) as unknown;
      if (Array.isArray(treeSchema) && treeSchema.length) {
        return applyPreferredColumnOrder(treeSchema
          .map((col) => String(((col as Dict).name || '')).trim())
          .filter(Boolean), preferred);
      }
    }
    return preferred;
  }

  function applyPreferredColumnOrder(contractColumns: string[], preferredColumns: string[]) {
    const contract = uniqueFields(contractColumns.map((item) => String(item || '').trim()).filter(Boolean));
    const preferred = uniqueFields(preferredColumns.map((item) => String(item || '').trim()).filter(Boolean));
    if (!contract.length) return preferred;
    if (!preferred.length) return contract;
    const contractSet = new Set(contract);
    return uniqueFields([
      ...preferred.filter((item) => contractSet.has(item)),
      ...contract,
      ...preferred.filter((item) => !contractSet.has(item)),
    ]);
  }

  function extractColumnSchemaFromContract(contract: unknown): Dict[] {
    const typed = (contract || {}) as Dict;
    const v2 = resolveUnifiedPageContractV2(typed);
    if (v2) {
      return collectUnifiedPageContractV2FieldWidgets(typed).map((widget) => ({
        name: widget.fieldCode,
        label: widget.label,
        string: widget.label,
        widget: widget.widgetType,
        componentKey: widget.componentKey,
        ...(widget.componentConfig || {}),
      }));
    }
    const directViews = typed.views as Dict | undefined;
    const treeBlock = directViews ? (directViews.tree || directViews.list || {}) as Dict : {};
    const schema = treeBlock.columnsSchema || treeBlock.columns_schema;
    return Array.isArray(schema) ? (schema as Dict[]) : [];
  }

  function resolveListColumnOptions(contract: unknown, profile: { columns?: string[]; hidden_columns?: string[]; column_labels?: Record<string, string> } | null): ListColumnOption[] {
    const typed = (contract || {}) as Dict;
    const fieldsMap = (typed.fields && typeof typed.fields === 'object') ? typed.fields as Record<string, Dict> : {};
    const preferred = Array.isArray(profile?.columns) ? profile?.columns || [] : [];
    const hidden = new Set(Array.isArray(profile?.hidden_columns) ? profile?.hidden_columns || [] : []);
    const v2FieldStatus = collectUnifiedPageContractV2FieldStatus(contract);
    const schemaRows = extractColumnSchemaFromContract(contract);
    const schemaByName = schemaRows.reduce<Record<string, Dict>>((acc, row) => {
      const name = String(row.name || '').trim();
      if (name && !acc[name]) acc[name] = row;
      return acc;
    }, {});
    const baseColumns = extractColumnsFromContract(contract, preferred);
    const labels = {
      ...contractColumnLabels.value,
      ...((profile?.column_labels || {}) as Record<string, string>),
    };
    return uniqueFields([...baseColumns, ...Array.from(hidden)])
      .map((name) => {
        const schema = schemaByName[name] || {};
        const field = fieldsMap[name] || {};
        const status = v2FieldStatus[name];
        const optional = String(schema.optional || '').trim();
        const invisible = schema.invisible === true || schema.column_invisible === true || status?.visible === false;
        const sortableRaw = Object.prototype.hasOwnProperty.call(schema, 'sortable')
          ? schema.sortable
          : field.sortable;
        const type = String(schema.type || field.type || '').trim();
        const widget = String(schema.widget || field.widget || field.type || '').trim();
        const rawSelection = Array.isArray(schema.selection) ? schema.selection : field.selection;
        return {
          name,
          label: String(labels[name] || schema.label || schema.string || field.string || name).trim() || name,
          optional,
          defaultVisible: !hidden.has(name) && optional !== 'hide' && !invisible,
          sortable: sortableRaw === false ? false : undefined,
          type: type || undefined,
          widget: widget || undefined,
          cellRole: String(schema.cell_role || schema.cellRole || '').trim() || undefined,
          mutation: schema.mutation && typeof schema.mutation === 'object'
            ? schema.mutation as Record<string, unknown>
            : undefined,
          selection: Array.isArray(rawSelection)
            ? rawSelection
                .map((item) => {
                  if (Array.isArray(item)) {
                    return {
                      value: String(item[0] ?? '').trim(),
                      label: String(item[1] ?? '').trim(),
                    };
                  }
                  const row = (item || {}) as Dict;
                  return { value: String(row.value ?? '').trim(), label: String(row.label ?? '').trim() };
                })
                .filter((item) => item.value && item.label)
            : undefined,
          toneByValue: typeof schema.tone_by_value === 'object' && schema.tone_by_value
            ? Object.entries(schema.tone_by_value as Dict).reduce<Record<string, string>>((acc, [value, tone]) => {
                const key = String(value || '').trim();
                const normalizedTone = String(tone || '').trim();
                if (key && normalizedTone) acc[key] = normalizedTone;
                return acc;
              }, {})
            : undefined,
        };
      });
  }

  function convergeColumnsForSurface(rawColumns: string[], fields: Record<string, unknown>) {
    const normalized = rawColumns.filter(Boolean);
    if (!normalized.length) return normalized;
    void fields;
    return normalized;
  }

  function extractKanbanFields(contract: unknown) {
    return extractKanbanFieldsFromContract(contract);
  }

  function extractKanbanProfile(contract: unknown): KanbanProfile {
    const typed = (contract || {}) as Dict;
    const directViews = typed.views as Dict | undefined;
    const block = (directViews?.kanban || {}) as Dict;
    const profile = (block.kanban_profile || {}) as Dict;
    const normalize = (rows: unknown) =>
      Array.isArray(rows) ? rows.map((item) => String(item || '').trim()).filter(Boolean) : [];
    return {
      titleField: String(profile.title_field || '').trim(),
      primaryFields: normalize(profile.primary_fields),
      secondaryFields: normalize(profile.secondary_fields),
      statusFields: normalize(profile.status_fields),
      metricFields: normalize(profile.metric_fields),
      quickActionCount: Number(profile.quick_action_count || 0),
    };
  }

  function extractListOrderFromContract(contract: unknown): string {
    const typed = (contract || {}) as Dict;
    const directViews = typed.views as Dict | undefined;
    const treeBlock = (directViews?.tree || directViews?.list || {}) as Dict;
    const searchDefaults = ((typed.search || {}) as Dict).defaults as Dict | undefined;
    const candidates = [
      treeBlock.order,
      treeBlock.default_order,
      searchDefaults?.order,
      typed.order,
    ];
    for (const item of candidates) {
      const value = String(item || '').trim();
      if (value) return value;
    }
    return '';
  }

  function buildListSortOptions(contract: unknown, currentSort: string, fallbackLabel: string): SortOption[] {
    const rows: SortOption[] = [];
    const add = (valueRaw: unknown, labelRaw?: unknown) => {
      const value = String(valueRaw || '').trim();
      if (!value || rows.some((item) => item.value === value)) return;
      const label = String(labelRaw || value || fallbackLabel).trim() || fallbackLabel;
      rows.push({ label, value });
    };
    const typed = (contract || {}) as Dict;
    const sortOptions = ((typed.search || {}) as Dict).sort_options;
    if (Array.isArray(sortOptions)) {
      sortOptions.forEach((row) => {
        const raw = row as Dict;
        add(raw.value || raw.order, raw.label);
      });
    }
    add(extractListOrderFromContract(contract), fallbackLabel);
    add(currentSort, fallbackLabel);
    return rows;
  }

  function extractAdvancedViewFields(contract: unknown, mode: string) {
    return extractAdvancedViewFieldsFromContract(contract, mode);
  }

  function extractViewFieldLabels(contract: unknown, mode: string) {
    return extractViewFieldLabelsFromContract(contract, mode);
  }

  function advancedRowTitle(row: Record<string, unknown>) {
    return String(row.display_name || row.name || row.id || options.pageText('advanced_row_title_fallback', '记录')).trim();
  }

  function advancedFieldLabel(field: string) {
    return String(contractColumnLabels.value[field] || field).trim();
  }

  function advancedRowMeta(row: Record<string, unknown>) {
    const preferredKeys = options.advancedFields.value.length
      ? options.advancedFields.value
      : Object.keys(row);
    const entries = preferredKeys
      .filter((key) => key !== 'id' && key !== 'name' && key !== 'display_name' && key in row)
      .slice(0, 3)
      .map((key) => `${advancedFieldLabel(key)}: ${String(row[key] ?? '-')}`);
    if (!entries.length) return options.pageText('advanced_row_meta_empty', '无附加字段');
    return entries.join(' · ');
  }

  function buildGroupKey(field: unknown, value: unknown, fallback: unknown) {
    const fieldPart = String(field || options.activeGroupByField.value || 'group').trim() || 'group';
    const valuePart = typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'
      ? String(value)
      : JSON.stringify(value ?? fallback);
    return `${fieldPart}:${valuePart}`;
  }

  function resolveModelFromContract(contract: unknown) {
    const typed = (contract || {}) as Dict;
    const v2 = resolveUnifiedPageContractV2(typed);
    const v2Model = String(v2?.pageInfo?.model || '').trim();
    if (v2Model) {
      return v2Model;
    }
    const direct = typed.model;
    if (typeof direct === 'string' && direct.trim()) {
      return direct.trim();
    }
    const headModel = ((typed.head || {}) as Dict).model;
    if (typeof headModel === 'string' && headModel.trim()) {
      return headModel.trim();
    }
    const views = (typed.views || {}) as Dict;
    const viewModel = ((views.tree as Dict | undefined)?.model
      || (views.form as Dict | undefined)?.model
      || (views.kanban as Dict | undefined)?.model);
    if (typeof viewModel === 'string' && viewModel.trim()) {
      return viewModel.trim();
    }
    return '';
  }

  function extractListProfile(contract: unknown) {
    const typed = (contract || {}) as Dict;
    const rawProfile = resolveUnifiedPageContractV2ListProfile(typed);
    const semanticPage = (typed.semantic_page || {}) as Dict;
    const listSemantics = (semanticPage.list_semantics || {}) as Dict;
    const semanticColumns = Array.isArray(listSemantics.columns) ? (listSemantics.columns as Array<Dict>) : [];
    const columns = Array.isArray(rawProfile.columns) && rawProfile.columns.length
      ? rawProfile.columns.map((item) => String(item || '').trim()).filter(Boolean)
      : semanticColumns.map((row) => String(row.name || '').trim()).filter(Boolean);
    const hiddenColumns = Array.isArray(rawProfile.hidden_columns)
      ? rawProfile.hidden_columns.map((item) => String(item || '').trim()).filter(Boolean)
      : [];
    const factColumns = Array.isArray(rawProfile.fact_columns)
      ? rawProfile.fact_columns.map((item) => String(item || '').trim()).filter(Boolean)
      : [];
    const columnLabels: Record<string, string> = {};
    Object.entries((rawProfile.column_labels || {}) as Dict).forEach(([name, labelRaw]) => {
      const label = String(labelRaw || '').trim();
      if (label) columnLabels[name] = label;
    });
    semanticColumns.forEach((row) => {
      const name = String(row.name || '').trim();
      const label = String(row.label || '').trim();
      if (name && label && !columnLabels[name]) columnLabels[name] = label;
    });
    const rowPrimary = String(rawProfile.row_primary || listSemantics.row_primary || '').trim();
    const rowSecondary = String(rawProfile.row_secondary || listSemantics.row_secondary || '').trim();
    const showRowNumber = rawProfile.show_row_number !== false;
    const statusField = String(rawProfile.status_field || listSemantics.status_field || '').trim();
    const metricFields = Array.isArray(rawProfile.metric_fields || listSemantics.metric_fields)
      ? ((rawProfile.metric_fields || listSemantics.metric_fields) as unknown[])
          .map((item) => String(item || '').trim())
          .filter(Boolean)
      : [];
    const rawBatchPolicy = (rawProfile.batch_policy || listSemantics.batch_policy || {}) as Dict;
    const hasRawBatchPolicy = Object.keys(rawBatchPolicy).length > 0;
    const batchPolicy = {
      enabled: rawBatchPolicy.enabled === true,
      active_field: String(rawBatchPolicy.active_field || '').trim() || undefined,
      assignee_field: String(rawBatchPolicy.assignee_field || '').trim() || undefined,
      archive_value: typeof rawBatchPolicy.archive_value === 'boolean' ? rawBatchPolicy.archive_value : null,
      activate_value: typeof rawBatchPolicy.activate_value === 'boolean' ? rawBatchPolicy.activate_value : null,
      assignee_options: rawBatchPolicy.assignee_options && typeof rawBatchPolicy.assignee_options === 'object'
        ? rawBatchPolicy.assignee_options as Dict
        : null,
      delete_mode: String(rawBatchPolicy.delete_mode || '').trim() || undefined,
      available_actions: Array.isArray(rawBatchPolicy.available_actions)
        ? rawBatchPolicy.available_actions.map((item) => String(item || '').trim()).filter(Boolean)
        : undefined,
    };
    const rawGrouping = (rawProfile.grouping || listSemantics.grouping || {}) as Dict;
    const rawGroupingSort = (rawGrouping.sort || {}) as Dict;
    const grouping = {
      sample_limits: Array.isArray(rawGrouping.sample_limits)
        ? rawGrouping.sample_limits
            .map((item) => Number(item))
            .filter((item) => Number.isFinite(item) && item > 0)
            .map((item) => Math.trunc(item))
        : undefined,
      default_sample_limit: Number.isFinite(Number(rawGrouping.default_sample_limit))
        ? Math.trunc(Number(rawGrouping.default_sample_limit))
        : undefined,
      sort: {
        key: String(rawGroupingSort.key || '').trim() || undefined,
        default_direction: String(rawGroupingSort.default_direction || '').trim() || undefined,
        directions: Array.isArray(rawGroupingSort.directions)
          ? rawGroupingSort.directions.map((item) => String(item || '').trim()).filter(Boolean)
          : undefined,
      },
    };
    const rawPreferencePolicy = (rawProfile.preference_policy || {}) as Dict;
    const preferencePolicy = {
      scope: String(rawPreferencePolicy.scope || '').trim() || undefined,
      allow_visibility: rawPreferencePolicy.allow_visibility !== false,
      allow_order: rawPreferencePolicy.allow_order !== false,
      allow_width: rawPreferencePolicy.allow_width !== false,
      locked_columns: Array.isArray(rawPreferencePolicy.locked_columns)
        ? rawPreferencePolicy.locked_columns.map((item) => String(item || '').trim()).filter(Boolean)
        : [],
      must_request_columns: Array.isArray(rawPreferencePolicy.must_request_columns)
        ? rawPreferencePolicy.must_request_columns.map((item) => String(item || '').trim()).filter(Boolean)
        : [],
    };
    if (!columns.length && !Object.keys(columnLabels).length && !rowPrimary && !rowSecondary && !statusField && !metricFields.length && !Object.keys(rawBatchPolicy).length && !Object.keys(rawGrouping).length) {
      return null;
    }
    return {
      columns,
      fact_columns: factColumns,
      hidden_columns: hiddenColumns,
      column_labels: columnLabels,
      preference_policy: preferencePolicy,
      row_primary: rowPrimary,
      row_secondary: rowSecondary,
      show_row_number: showRowNumber,
      status_field: statusField,
      metric_fields: metricFields,
      ...(hasRawBatchPolicy ? { batch_policy: batchPolicy } : {}),
      grouping,
    };
  }

  return {
    contractColumnLabels,
    extractListProfile,
    resolveListColumnOptions,
    extractColumnsFromContract,
    extractListOrderFromContract,
    buildListSortOptions,
    convergeColumnsForSurface,
    extractKanbanFields,
    extractKanbanProfile,
    extractAdvancedViewFields,
    extractViewFieldLabels,
    advancedRowTitle,
    advancedFieldLabel,
    advancedRowMeta,
    buildGroupKey,
    resolveModelFromContract,
  };
}
