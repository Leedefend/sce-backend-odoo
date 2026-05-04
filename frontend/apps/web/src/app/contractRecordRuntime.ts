import type { ActionContract, ViewButton, ViewContract } from '@sc/schema';
import { detectObjectMethodFromActionKey, normalizeActionKind, parseMaybeJsonRecord, toPositiveInt } from './contractRuntime';
import {
  collectUnifiedPageContractV2ButtonStatus,
  collectUnifiedPageContractV2FieldContainerStatus,
  collectUnifiedPageContractV2FieldWidgets,
  collectUnifiedPageContractV2FieldStatus,
  resolveUnifiedPageContractV2,
  resolveUnifiedPageContractV2GlobalStatus,
  type UnifiedPageContractV2Action,
  type UnifiedPageContractV2ButtonStatus,
} from './contracts/unifiedPageContractV2';

export type RecordRuntimeButton = ViewButton & {
  actionKind?: string;
  actionId?: number;
  buttonContext?: Record<string, unknown>;
  domainRaw?: string;
  actionTarget?: string;
  sourceLevel?: string;
  disabled?: boolean;
  disabledReason?: string;
};

export type RecordRuntimeContract = {
  view: ViewContract | null;
  fieldNames: string[];
  headerButtons: RecordRuntimeButton[];
  statButtons: RecordRuntimeButton[];
  rights: {
    read: boolean;
    write: boolean;
    create: boolean;
    unlink: boolean;
  };
};

type FormFieldNode = { name?: string; string?: string };

type FormGroupNode = {
  fields?: FormFieldNode[];
  sub_groups?: FormGroupNode[];
};

type FormPageNode = {
  title?: string | null;
  groups?: FormGroupNode[];
};

type RawFormLayoutNode = {
  type?: string;
  name?: string;
  string?: string;
  fields?: Array<{ name?: string; string?: string }>;
  groups?: FormGroupNode[];
  pages?: FormPageNode[];
};

function resolveRights(contract: ActionContract) {
  const globalStatus = resolveUnifiedPageContractV2GlobalStatus(contract);
  const pageAuth = String(globalStatus?.pageAuth || '').trim().toLowerCase();
  if (globalStatus?.pageVisible === false || pageAuth === 'none') {
    return { read: false, write: false, create: false, unlink: false };
  }
  const head = contract.head?.permissions;
  const effective = contract.permissions?.effective?.rights;
  const resolve = (key: 'read' | 'write' | 'create' | 'unlink') => {
    const a = head?.[key];
    if (typeof a === 'boolean') return a;
    const b = effective?.[key];
    if (typeof b === 'boolean') return b;
    return true;
  };
  return {
    read: resolve('read'),
    write: pageAuth === 'read' ? false : resolve('write'),
    create: pageAuth === 'read' ? false : resolve('create'),
    unlink: pageAuth === 'read' ? false : resolve('unlink'),
  };
}

function mapContractButton(raw: Record<string, unknown>): RecordRuntimeButton | null {
  const key = String(raw.key || '').trim();
  if (!key) return null;
  const label = String(raw.label || key).trim();
  const level = String(raw.level || '').trim().toLowerCase();
  const kind = normalizeActionKind(raw.kind);
  const payload = parseMaybeJsonRecord(raw.payload);
  const actionId = toPositiveInt(payload.action_id) ?? toPositiveInt(payload.ref);
  const methodName = detectObjectMethodFromActionKey(key, String(payload.method || '').trim());
  if (kind === 'open' && !actionId) return null;
  if ((kind === 'object' || kind === 'server') && !methodName) return null;

  return {
    name: kind === 'open' ? `__open__${String(actionId || '')}` : methodName,
    string: label,
    type: kind === 'open' ? 'action_open' : kind === 'server' ? 'server' : 'object',
    actionKind: kind,
    actionId: actionId || undefined,
    buttonContext: parseMaybeJsonRecord(payload.context_raw),
    domainRaw: String(payload.domain_raw || '').trim() || undefined,
    actionTarget: String(payload.target || '').trim() || undefined,
    sourceLevel: level,
  };
}

function normalizeFieldName(raw: unknown): string {
  return String(raw || '').trim();
}

function normalizeUniqueFields(items: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const item of items) {
    const name = normalizeFieldName(item);
    if (!name || seen.has(name)) continue;
    seen.add(name);
    result.push(name);
  }
  return result;
}

function extractFieldOrder(contract: ActionContract): string[] {
  const v2Fields = collectUnifiedPageContractV2FieldWidgets(contract).map((widget) => normalizeFieldName(widget.fieldCode));
  if (v2Fields.length) return normalizeUniqueFields(v2Fields);
  const direct = contract.views?.form?.layout || [];
  const ordered: string[] = [];
  for (const node of direct as RawFormLayoutNode[]) {
    const type = normalizeFieldName(node?.type).toLowerCase();
    if (type === 'field') {
      ordered.push(normalizeFieldName(node?.name));
      continue;
    }
    if (type === 'group' && Array.isArray(node?.fields)) {
      for (const child of node.fields) {
        ordered.push(normalizeFieldName(child?.name));
      }
      continue;
    }
    if (type === 'notebook' && Array.isArray(node?.pages)) {
      for (const page of node.pages) {
        for (const group of page?.groups || []) {
          for (const field of group?.fields || []) {
            ordered.push(normalizeFieldName(field?.name));
          }
        }
      }
      continue;
    }
  }

  const normalized = normalizeUniqueFields(ordered);
  const fallback = Array.isArray(contract.views?.form?.fields) ? contract.views?.form?.fields || [] : [];
  const merged = normalizeUniqueFields([...normalized, ...fallback]);
  return merged;
}

function buildV2Fields(contract: ActionContract): Record<string, unknown> {
  const legacy = contract.fields || {};
  const out: Record<string, unknown> = { ...legacy };
  const fieldStatus = collectUnifiedPageContractV2FieldStatus(contract);
  const containerStatus = collectUnifiedPageContractV2FieldContainerStatus(contract);
  collectUnifiedPageContractV2FieldWidgets(contract).forEach((widget) => {
    if (!widget.fieldCode) return;
    const status = fieldStatus[widget.fieldCode];
    const container = containerStatus[widget.fieldCode];
    if (container?.visible === false) return;
    const next = {
      name: widget.fieldCode,
      string: widget.label || widget.fieldCode,
      type: widget.widgetType,
      widget: widget.widgetType,
      readonly: status?.readonly === true || status?.disabled === true || container?.disabled === true,
      required: status?.required === true,
    };
    out[widget.fieldCode] = out[widget.fieldCode]
      ? { ...(out[widget.fieldCode] as Record<string, unknown>), ...next }
      : next;
  });
  return out;
}

function resolveV2ActionButtonStatus(
  raw: UnifiedPageContractV2Action,
  statusById: Record<string, UnifiedPageContractV2ButtonStatus>,
): UnifiedPageContractV2ButtonStatus | null {
  const candidates = [
    raw.sourceWidgetId,
    raw.actionKey ? `btn.${raw.actionKey}` : '',
    raw.actionId,
    raw.actionId?.startsWith('action.') ? `btn.${raw.actionId.slice('action.'.length)}` : '',
  ]
    .map((item) => String(item || '').trim())
    .filter(Boolean);
  for (const key of candidates) {
    if (statusById[key]) return statusById[key];
  }
  return null;
}

function applyV2ButtonStatus<T extends RecordRuntimeButton>(
  row: T,
  status: UnifiedPageContractV2ButtonStatus | null,
): T | null {
  if (status?.visible === false) return null;
  if (status?.disabled === true) {
    row.disabled = true;
    row.disabledReason = status.reasonCode || 'disabled_by_status_contract';
  }
  return row;
}

function mapV2ActionButton(
  raw: UnifiedPageContractV2Action,
  statusById: Record<string, UnifiedPageContractV2ButtonStatus>,
): RecordRuntimeButton | null {
  const label = String(raw.label || raw.actionKey || raw.actionId || '').trim();
  const intent = String(raw.intent || '').trim();
  const button = raw.button || {};
  const target = raw.target || {};
  const status = resolveV2ActionButtonStatus(raw, statusById);
  if (intent === 'ui.contract') {
    const actionId = toPositiveInt(target.action_id) ?? toPositiveInt(target.actionId);
    if (!actionId) return null;
    return applyV2ButtonStatus({
      name: `__open__${String(actionId)}`,
      string: label || String(actionId),
      type: 'action_open',
      actionKind: 'open',
      actionId,
      domainRaw: String(target.domain_raw || target.domainRaw || '').trim() || undefined,
      buttonContext: parseMaybeJsonRecord(target.context_raw || target.contextRaw),
      sourceLevel: 'toolbar',
    }, status);
  }
  if (intent !== 'execute_button') return null;
  const name = String(button.name || raw.actionKey || '').trim();
  if (!name) return null;
  return applyV2ButtonStatus({
    name,
    string: label || name,
    type: button.type === 'server_action' ? 'server' : String(button.type || 'object'),
    actionKind: button.type === 'server_action' ? 'server' : 'object',
    sourceLevel: 'toolbar',
  }, status);
}

function buildLayout(contract: ActionContract, fieldNames: string[]): ViewContract['layout'] {
  const chatterRaw = contract.views?.form?.chatter;
  const chatterEnabled =
    typeof chatterRaw === 'object' && chatterRaw !== null
      ? Boolean((chatterRaw as { enabled?: unknown }).enabled)
      : Boolean(chatterRaw);
  return {
    groups: [
      {
        fields: fieldNames.map((name) => ({ name })),
      },
    ],
    headerButtons: [],
    statButtons: [],
    chatter: chatterEnabled
      ? (typeof chatterRaw === 'object' && chatterRaw !== null ? (chatterRaw as Record<string, unknown>) : { enabled: true })
      : undefined,
    ribbon: null,
  };
}

export function buildRecordRuntimeFromContract(contract: ActionContract): RecordRuntimeContract {
  const v2 = resolveUnifiedPageContractV2(contract);
  const fields = buildV2Fields(contract);
  const hasV2Form = v2?.pageInfo?.viewType === 'form' && collectUnifiedPageContractV2FieldWidgets(contract).length > 0;
  const hasFormLayout = Array.isArray(contract.views?.form?.layout) && (contract.views?.form?.layout?.length || 0) > 0;
  const hasFormFields = Array.isArray(contract.views?.form?.fields) && (contract.views?.form?.fields?.length || 0) > 0;
  if (!hasV2Form && !hasFormLayout && !hasFormFields) {
    return {
      view: null,
      fieldNames: [],
      headerButtons: [],
      statButtons: [],
      rights: resolveRights(contract),
    };
  }
  const fieldNames = extractFieldOrder(contract);
  if (!fieldNames.length) {
    return {
      view: null,
      fieldNames: [],
      headerButtons: [],
      statButtons: [],
      rights: resolveRights(contract),
    };
  }

  const view: ViewContract = {
    model: String(contract.head?.model || contract.model || ''),
    view_type: 'form',
    fields,
    layout: buildLayout(contract, fieldNames),
  };

  const mergedRows: Array<Record<string, unknown>> = [];
  if (Array.isArray(contract.toolbar?.header)) mergedRows.push(...(contract.toolbar?.header as Array<Record<string, unknown>>));
  if (Array.isArray(contract.buttons)) mergedRows.push(...(contract.buttons as Array<Record<string, unknown>>));

  const v2ButtonStatus = collectUnifiedPageContractV2ButtonStatus(contract);
  const v2Actions = (v2?.actionContract?.actionRuleList || [])
    .map((row) => mapV2ActionButton(row, v2ButtonStatus))
    .filter((row): row is RecordRuntimeButton => Boolean(row));
  const mapped = v2Actions.length ? v2Actions : mergedRows.map(mapContractButton).filter((row): row is RecordRuntimeButton => Boolean(row));
  const headerButtons = mapped.filter((row) => row.sourceLevel === 'header' || row.sourceLevel === 'toolbar');
  const statButtons = mapped.filter((row) => row.sourceLevel === 'smart' || row.sourceLevel === 'row');
  view.layout.headerButtons = headerButtons;
  view.layout.statButtons = statButtons;

  return {
    view,
    fieldNames,
    headerButtons,
    statButtons,
    rights: resolveRights(contract),
  };
}
