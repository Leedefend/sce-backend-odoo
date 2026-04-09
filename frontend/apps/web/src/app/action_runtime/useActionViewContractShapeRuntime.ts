import { computed, type Ref } from 'vue';
import { uniqueFields } from '../runtime/actionViewRequestRuntime';
import {
  resolveContractKanbanSemantics,
  resolveContractListSemantics,
  resolveContractViewRenderPolicy,
} from '../contractTakeover';

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

function asDict(value: unknown): Dict {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  return value as Dict;
}

function semanticZones(contract: unknown): Dict[] {
  const typed = asDict(contract);
  const semanticPage = asDict(typed.semantic_page);
  const rows = semanticPage.zones;
  if (!Array.isArray(rows)) return [];
  return rows.filter((item) => item && typeof item === 'object' && !Array.isArray(item)) as Dict[];
}

function findZoneBlocks(contract: unknown, zoneKey: string, blockType: string): Dict[] {
  const zone = semanticZones(contract).find((item) => String(item.key || '').trim() === zoneKey);
  const blocks = Array.isArray(zone?.blocks) ? zone?.blocks : [];
  return blocks
    .filter((item) => item && typeof item === 'object' && !Array.isArray(item))
    .filter((item) => String((item as Dict).type || '').trim() === blockType) as Dict[];
}

export function useActionViewContractShapeRuntime(options: UseActionViewContractShapeRuntimeOptions) {
  const contractColumnLabels = computed<Record<string, string>>(() => {
    const rows = options.actionContract.value?.fields || {};
    return Object.entries(rows).reduce<Record<string, string>>((acc, [name, descriptor]) => {
      const descriptorRow = (descriptor || {}) as Dict;
      const label = String(descriptorRow.string || '').trim();
      if (label) acc[name] = label;
      return acc;
    }, {});
  });

  function extractColumnsFromContract(contract: unknown, sceneColumns: string[] = []) {
    if (Array.isArray(sceneColumns) && sceneColumns.length) {
      return sceneColumns;
    }
    const detailBlocks = findZoneBlocks(contract, 'detail_zone', 'relation_table_block');
    const zoneColumns = detailBlocks
      .flatMap((block) => {
        const data = asDict(block.data);
        const rows = data.columns;
        if (!Array.isArray(rows)) return [];
        return rows.map((item) => String(item || '').trim()).filter(Boolean);
      });
    if (zoneColumns.length) {
      return zoneColumns;
    }

    const listSemantics = resolveContractListSemantics(contract);
    const semanticColumns = Array.isArray(listSemantics.columns)
      ? listSemantics.columns
        .map((item) => String(((item as Dict).name || '')).trim())
        .filter(Boolean)
      : [];
    if (semanticColumns.length) {
      return semanticColumns;
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
    const normalized = rawColumns
      .map((item) => String(item || '').trim())
      .filter(Boolean);
    if (!normalized.length) return normalized;
    const fieldEntries = Object.entries(fields || {});
    if (!fieldEntries.length) return normalized;
    const fieldNames = new Set(fieldEntries.map(([name]) => String(name || '').trim()).filter(Boolean));
    const labelToField = fieldEntries.reduce<Record<string, string>>((acc, [name, descriptor]) => {
      const label = String(((descriptor || {}) as Dict).string || '').trim();
      if (label && !acc[label]) {
        acc[label] = name;
      }
      return acc;
    }, {});
    return normalized.map((column) => {
      if (fieldNames.has(column)) return column;
      return labelToField[column] || column;
    });
  }

  function extractKanbanFields(contract: unknown) {
    const detailBlocks = findZoneBlocks(contract, 'detail_zone', 'relation_card_block');
    const zoneFields = detailBlocks
      .flatMap((block) => {
        const data = asDict(block.data);
        const rows = data.fields;
        if (!Array.isArray(rows)) return [];
        return rows.map((item) => String(item || '').trim()).filter(Boolean);
      });
    if (zoneFields.length) {
      return zoneFields;
    }

    const kanbanSemantics = resolveContractKanbanSemantics(contract);
    if (Array.isArray(kanbanSemantics.card_fields) && kanbanSemantics.card_fields.length) {
      return kanbanSemantics.card_fields.map((item) => String(item || '')).filter(Boolean);
    }
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
    const detailBlocks = findZoneBlocks(contract, 'detail_zone', 'relation_card_block');
    const detailCard = detailBlocks[0] || {};
    const detailData = asDict(detailCard.data);
    const zoneSemantics = asDict(detailData.kanban_semantics);
    if (zoneSemantics.title_field || zoneSemantics.card_fields) {
      const cardFields = Array.isArray(zoneSemantics.card_fields)
        ? zoneSemantics.card_fields.map((item) => String(item || '').trim()).filter(Boolean)
        : [];
      return {
        titleField: String(zoneSemantics.title_field || '').trim(),
        primaryFields: cardFields.slice(0, 2),
        secondaryFields: cardFields.slice(2, 5),
        statusFields: [String(zoneSemantics.group_by_field || zoneSemantics.stage_field || '').trim()].filter(Boolean),
        metricFields: Array.isArray(zoneSemantics.metric_fields)
          ? zoneSemantics.metric_fields.map((item) => String(item || '').trim()).filter(Boolean)
          : [],
        quickActionCount: Number(zoneSemantics.quick_action_count || 0),
      };
    }

    const kanbanSemantics = resolveContractKanbanSemantics(contract);
    if (kanbanSemantics.title_field || kanbanSemantics.card_fields) {
      const cardFields = Array.isArray(kanbanSemantics.card_fields)
        ? kanbanSemantics.card_fields.map((item) => String(item || '').trim()).filter(Boolean)
        : [];
      return {
        titleField: String(kanbanSemantics.title_field || '').trim(),
        primaryFields: cardFields.slice(0, 2),
        secondaryFields: cardFields.slice(2, 5),
        statusFields: [String(kanbanSemantics.group_by_field || kanbanSemantics.stage_field || '').trim()].filter(Boolean),
        metricFields: Array.isArray(kanbanSemantics.metric_fields)
          ? kanbanSemantics.metric_fields.map((item) => String(item || '').trim()).filter(Boolean)
          : [],
        quickActionCount: Number(kanbanSemantics.quick_action_count || 0),
      };
    }
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

  function resolveModeRecommendedRuntime(contract: unknown, mode: string) {
    return resolveContractViewRenderPolicy(contract, mode).recommendedRuntime;
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

  return {
    contractColumnLabels,
    extractColumnsFromContract,
    convergeColumnsForSurface,
    extractKanbanFields,
    extractKanbanProfile,
    extractAdvancedViewFields,
    advancedRowTitle,
    advancedFieldLabel,
    advancedRowMeta,
    buildGroupKey,
    resolveModelFromContract,
    resolveModeRecommendedRuntime,
  };
}
