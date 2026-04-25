import { computed, type Ref } from 'vue';
import { uniqueFields } from '../runtime/actionViewRequestRuntime';

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
    const listProfile = (contract.list_profile || {}) as Dict;
    Object.entries((listProfile.column_labels || {}) as Dict).forEach(([name, labelRaw]) => {
      const label = String(labelRaw || '').trim();
      if (label) labels[name] = label;
    });
    const semanticPage = (contract.semantic_page || {}) as Dict;
    const listSemantics = (semanticPage.list_semantics || {}) as Dict;
    const semanticColumns = Array.isArray(listSemantics.columns) ? (listSemantics.columns as Array<Dict>) : [];
    semanticColumns.forEach((row) => {
      const name = String(row.name || '').trim();
      const label = String(row.label || '').trim();
      if (name && label) labels[name] = label;
    });
    return labels;
  });

  function extractColumnsFromContract(contract: unknown, sceneColumns: string[] = []) {
    if (Array.isArray(sceneColumns) && sceneColumns.length) {
      return sceneColumns;
    }
    const typed = (contract || {}) as Dict;
    const uiContract = ((typed.ui_contract || {}) as Dict);
    const directViews = (typed.views || uiContract.views) as Dict | undefined;
    if (directViews) {
      const treeBlock = (directViews.tree || directViews.list || {}) as Dict;
      const treeColumns = treeBlock.columns;
      if (Array.isArray(treeColumns) && treeColumns.length) {
        return treeColumns.map((item) => String(item || '')).filter(Boolean);
      }
      const treeSchema = (treeBlock.columnsSchema || treeBlock.columns_schema) as unknown;
      if (Array.isArray(treeSchema) && treeSchema.length) {
        return treeSchema
          .map((col) => String(((col as Dict).name || '')).trim())
          .filter(Boolean);
      }
    }

    const columns = uiContract.columns;
    if (Array.isArray(columns) && columns.length) {
      return columns.map((item) => String(item || '')).filter(Boolean);
    }
    const schema = uiContract.columnsSchema;
    if (Array.isArray(schema) && schema.length) {
      return schema
        .map((col) => String(((col as Dict).name || '')).trim())
        .filter(Boolean);
    }
    return [];
  }

  function convergeColumnsForSurface(rawColumns: string[], fields: Record<string, unknown>) {
    const normalized = rawColumns.filter(Boolean);
    if (!normalized.length) return normalized;
    void fields;
    return normalized;
  }

  function extractKanbanFields(contract: unknown) {
    const typed = (contract || {}) as Dict;
    const uiContract = ((typed.ui_contract || {}) as Dict);
    const directViews = (typed.views || uiContract.views) as Dict | undefined;
    if (directViews) {
      const kanbanBlock = (directViews.kanban || {}) as Dict;
      if (Array.isArray(kanbanBlock.fields) && kanbanBlock.fields.length) {
        return kanbanBlock.fields.map((item) => String(item || '')).filter(Boolean);
      }
    }
    return [];
  }

  function extractKanbanProfile(contract: unknown): KanbanProfile {
    const typed = (contract || {}) as Dict;
    const uiContract = ((typed.ui_contract || {}) as Dict);
    const directViews = (typed.views || uiContract.views) as Dict | undefined;
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
    const uiContract = ((typed.ui_contract || {}) as Dict);
    const directViews = (typed.views || uiContract.views) as Dict | undefined;
    const treeBlock = (directViews?.tree || directViews?.list || {}) as Dict;
    const searchDefaults = ((typed.search || {}) as Dict).defaults as Dict | undefined;
    const candidates = [
      treeBlock.order,
      treeBlock.default_order,
      searchDefaults?.order,
      uiContract.order,
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
    const typed = (contract || {}) as Dict;
    const uiContract = ((typed.ui_contract || {}) as Dict);
    const directViews = typed.views as Dict | undefined;
    const normalizedViews = uiContract.views as Dict | undefined;
    const viewBlock = (directViews?.[mode] || normalizedViews?.[mode] || {}) as Dict;
    const fallbackNames = ['name', 'display_name', 'id'];
    if (mode === 'pivot') {
      const measures = Array.isArray(viewBlock.measures) ? viewBlock.measures : [];
      const dims = Array.isArray(viewBlock.dimensions) ? viewBlock.dimensions : [];
      const fields = [...dims, ...measures, ...fallbackNames]
        .map((item) => String(item || '').trim())
        .filter(Boolean);
      return uniqueFields(fields);
    }
    if (mode === 'graph') {
      const measure = String(viewBlock.measure || '').trim();
      const dim = String(viewBlock.dimension || '').trim();
      return uniqueFields([dim, measure, ...fallbackNames].filter(Boolean));
    }
    if (mode === 'calendar' || mode === 'gantt') {
      const dateStart = String(viewBlock.date_start || '').trim();
      const dateStop = String(viewBlock.date_stop || '').trim();
      const fields = [dateStart, dateStop, ...fallbackNames];
      return uniqueFields(fields.map((item) => String(item || '').trim()).filter(Boolean));
    }
    if (mode === 'activity') {
      const activityField = String(viewBlock.field || '').trim();
      return uniqueFields([activityField, ...fallbackNames].filter(Boolean));
    }
    if (mode === 'dashboard') {
      const kpis = Array.isArray(viewBlock.kpis) ? viewBlock.kpis : [];
      const cards = Array.isArray(viewBlock.cards) ? viewBlock.cards : [];
      const guessed = [...kpis, ...cards]
        .map((item) => String(((item as Dict).field || '')).trim())
        .filter(Boolean);
      return uniqueFields([...guessed, ...fallbackNames]);
    }
    return fallbackNames;
  }

  function advancedRowTitle(row: Record<string, unknown>) {
    return String(row.display_name || row.name || row.id || options.pageText('advanced_row_title_fallback', '记录')).trim();
  }

  function advancedFieldLabel(field: string) {
    return String(options.contractColumnLabels.value[field] || field).trim();
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
    const nested = ((typed.ui_contract || {}) as Dict);
    const direct = typed.model;
    if (typeof direct === 'string' && direct.trim()) {
      return direct.trim();
    }
    const nestedDirect = nested.model;
    if (typeof nestedDirect === 'string' && nestedDirect.trim()) {
      return nestedDirect.trim();
    }
    const headModel = ((typed.head || {}) as Dict).model;
    if (typeof headModel === 'string' && headModel.trim()) {
      return headModel.trim();
    }
    const nestedHeadModel = ((nested.head || {}) as Dict).model;
    if (typeof nestedHeadModel === 'string' && nestedHeadModel.trim()) {
      return nestedHeadModel.trim();
    }
    const views = (typed.views || {}) as Dict;
    const viewModel = ((views.tree as Dict | undefined)?.model
      || (views.form as Dict | undefined)?.model
      || (views.kanban as Dict | undefined)?.model);
    if (typeof viewModel === 'string' && viewModel.trim()) {
      return viewModel.trim();
    }
    const nestedViews = (nested.views || {}) as Dict;
    const nestedViewModel = ((nestedViews.tree as Dict | undefined)?.model
      || (nestedViews.form as Dict | undefined)?.model
      || (nestedViews.kanban as Dict | undefined)?.model);
    if (typeof nestedViewModel === 'string' && nestedViewModel.trim()) {
      return nestedViewModel.trim();
    }
    return '';
  }

  function extractListProfile(contract: unknown) {
    const typed = (contract || {}) as Dict;
    const rawProfile = (typed.list_profile || {}) as Dict;
    const semanticPage = (typed.semantic_page || {}) as Dict;
    const listSemantics = (semanticPage.list_semantics || {}) as Dict;
    const semanticColumns = Array.isArray(listSemantics.columns) ? (listSemantics.columns as Array<Dict>) : [];
    const columns = Array.isArray(rawProfile.columns) && rawProfile.columns.length
      ? rawProfile.columns.map((item) => String(item || '').trim()).filter(Boolean)
      : semanticColumns.map((row) => String(row.name || '').trim()).filter(Boolean);
    const hiddenColumns = Array.isArray(rawProfile.hidden_columns)
      ? rawProfile.hidden_columns.map((item) => String(item || '').trim()).filter(Boolean)
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
    if (!columns.length && !Object.keys(columnLabels).length && !rowPrimary && !rowSecondary) {
      return null;
    }
    return {
      columns,
      hidden_columns: hiddenColumns,
      column_labels: columnLabels,
      row_primary: rowPrimary,
      row_secondary: rowSecondary,
    };
  }

  return {
    contractColumnLabels,
    extractListProfile,
    extractColumnsFromContract,
    extractListOrderFromContract,
    buildListSortOptions,
    convergeColumnsForSurface,
    extractKanbanFields,
    extractKanbanProfile,
    extractAdvancedViewFields,
    advancedRowTitle,
    advancedFieldLabel,
    advancedRowMeta,
    buildGroupKey,
    resolveModelFromContract,
  };
}
