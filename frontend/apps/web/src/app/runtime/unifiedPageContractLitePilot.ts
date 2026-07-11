import type { NavMeta } from '@sc/schema';
import {
  extractLitePreviewEnvelope,
  isUnifiedPageContractLite,
  type LiteContainer,
  type LiteWidget,
  type UnifiedPageContractLite,
} from '../contracts/unifiedPageContractLite';

type Dict = Record<string, unknown>;

export const LITE_CONTRACT_PILOT_MODEL = 'project.project';
export const LITE_CONTRACT_PILOT_VIEW = 'tree';
export const LITE_CONTRACT_ROLLOUT_ENV = 'VITE_LITE_CONTRACT_ROLLOUT';

type LiteContractRolloutMode = 'off' | 'pilot' | 'all_tree';

function normalizeMode(raw: unknown): string {
  const value = String(raw || '').trim().toLowerCase();
  return value === 'list' ? 'tree' : value;
}

function splitModes(raw: unknown): string[] {
  if (Array.isArray(raw)) {
    return raw.map(normalizeMode).filter(Boolean);
  }
  return String(raw || '').split(',').map(normalizeMode).filter(Boolean);
}

export function isLiteContractPilotEnabled(): boolean {
  return liteContractRolloutMode() !== 'off';
}

export function liteContractRolloutMode(): LiteContractRolloutMode {
  const rollout = String(import.meta.env.VITE_LITE_CONTRACT_ROLLOUT || '').trim().toLowerCase();
  if (rollout === 'all_tree') return 'all_tree';
  if (rollout === 'pilot') return 'pilot';
  return String(import.meta.env.VITE_LITE_CONTRACT_PILOT || '').trim() === '1' ? 'pilot' : 'off';
}

export function isLiteContractPilotCandidate(meta?: NavMeta | null): boolean {
  const rollout = liteContractRolloutMode();
  if (rollout === 'off') return false;
  const model = String(meta?.model || '').trim();
  if (!model) return false;
  const modes = splitModes(meta?.view_modes || []);
  const isTree = !modes.length || modes.includes(LITE_CONTRACT_PILOT_VIEW);
  if (!isTree) return false;
  if (rollout === 'all_tree') return true;
  return model === LITE_CONTRACT_PILOT_MODEL;
}

export function needsLiteContractAllTreeViewPreflight(meta?: NavMeta | null): boolean {
  if (liteContractRolloutMode() !== 'all_tree') return false;
  const model = String(meta?.model || '').trim();
  if (!model) return false;
  return splitModes(meta?.view_modes || []).length === 0;
}

function collectWidgets(containers: LiteContainer[]): LiteWidget[] {
  const out: LiteWidget[] = [];
  const visit = (rows: LiteContainer[]) => {
    rows.forEach((container) => {
      container.widgetList.forEach((widget) => out.push(widget));
      visit(container.children);
    });
  };
  visit(containers);
  return out;
}

function widgetTypeToFieldType(widget: LiteWidget): string {
  const type = String(widget.widgetType || widget.component || '').trim().toLowerCase();
  if (type === 'number') return 'float';
  if (type === 'date') return 'date';
  if (type === 'checkbox') return 'boolean';
  if (type === 'textarea') return 'text';
  if (type === 'select' || type === 'radio') return 'selection';
  return 'char';
}

function normalizeSelection(raw: unknown): Array<[string, string]> | undefined {
  if (!Array.isArray(raw)) return undefined;
  const rows = raw
    .map((item): [string, string] | null => {
      if (Array.isArray(item)) {
        const value = String(item[0] ?? '').trim();
        const label = String(item[1] ?? '').trim();
        return value && label ? [value, label] : null;
      }
      if (!item || typeof item !== 'object') return null;
      const row = item as Dict;
      const value = String(row.value ?? '').trim();
      const label = String(row.label ?? '').trim();
      return value && label ? [value, label] : null;
    })
    .filter((item): item is [string, string] => Boolean(item));
  return rows.length ? rows : undefined;
}

export function adaptLiteContractToActionViewContract(lite: UnifiedPageContractLite): Dict {
  const widgets = collectWidgets(lite.layoutContract.containerList);
  const statusByWidgetId = lite.statusContract.widgetStatus.reduce<Record<string, { visible: boolean; readonly: boolean; required: boolean; disabled: boolean }>>((acc, row) => {
    acc[row.widgetId] = row;
    return acc;
  }, {});
  const visibleWidgets = widgets.filter((widget) => statusByWidgetId[widget.widgetId]?.visible !== false);
  const effectiveWidgets = visibleWidgets.length ? visibleWidgets : widgets;
  const columns = effectiveWidgets
    .map((widget) => String(widget.fieldCode || '').trim())
    .filter(Boolean);
  const uniqueColumns = Array.from(new Set(columns.length ? columns : ['name']));

  const fields = effectiveWidgets.reduce<Record<string, Dict>>((acc, widget) => {
    const name = String(widget.fieldCode || '').trim();
    if (!name || acc[name]) return acc;
    const rawDict = lite.dataContract.dictData[name];
    acc[name] = {
      name,
      string: widget.label || name,
      type: widgetTypeToFieldType(widget),
      widget: widget.component || widget.widgetType,
      required: statusByWidgetId[widget.widgetId]?.required === true,
      readonly: statusByWidgetId[widget.widgetId]?.readonly === true,
      selection: normalizeSelection(rawDict),
    };
    return acc;
  }, {});

  if (!fields.id) {
    fields.id = { name: 'id', string: '编号', type: 'integer' };
  }

  const columnsSchema = uniqueColumns.map((name) => ({
    name,
    label: String(fields[name]?.string || name),
    string: String(fields[name]?.string || name),
    type: String(fields[name]?.type || 'char'),
    widget: String(fields[name]?.widget || fields[name]?.type || ''),
  }));

  return {
    __lite_contract_pilot: true,
    model: lite.pageInfo.model,
    view_type: lite.pageInfo.viewType,
    head: {
      model: lite.pageInfo.model,
      view_type: lite.pageInfo.viewType,
      title: lite.pageInfo.pageId,
    },
    views: {
      tree: {
        model: lite.pageInfo.model,
        columns: uniqueColumns,
        columns_schema: columnsSchema,
      },
    },
    fields,
    list_profile: {
      columns: uniqueColumns,
      column_labels: columnsSchema.reduce<Record<string, string>>((acc, col) => {
        acc[col.name] = col.label;
        return acc;
      }, {}),
    },
    permissions: {
      effective: {
        rights: {
          read: true,
          write: false,
          create: false,
          unlink: false,
        },
      },
    },
    search: {
      defaults: {
        limit: 40,
      },
    },
    meta: {
      lite_contract_version: lite.pageInfo.contractVersion,
      lite_trace_id: lite.meta.traceId,
      lite_etag: lite.meta.etag,
    },
  };
}

export function extractLiteContractFromIntentBody(body: unknown): UnifiedPageContractLite | null {
  const preview = extractLitePreviewEnvelope(body);
  if (!preview || preview.entryPoint !== 'load_contract' || preview.payloadType !== 'lite_contract') return null;
  return isUnifiedPageContractLite(preview.payload) ? preview.payload : null;
}
