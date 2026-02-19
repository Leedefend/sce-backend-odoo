import type { ActionContract, ViewButton, ViewContract } from '@sc/schema';
import { detectObjectMethodFromActionKey, normalizeActionKind, parseMaybeJsonRecord, toPositiveInt } from './contractRuntime';

export type RecordRuntimeButton = ViewButton & {
  actionKind?: string;
  actionId?: number;
  buttonContext?: Record<string, unknown>;
  domainRaw?: string;
  actionTarget?: string;
  sourceLevel?: string;
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

function resolveRights(contract: ActionContract) {
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
    write: resolve('write'),
    create: resolve('create'),
    unlink: resolve('unlink'),
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

export function buildRecordRuntimeFromContract(contract: ActionContract): RecordRuntimeContract {
  const fields = contract.fields || {};
  const layout = contract.views?.form?.layout || [];
  const orderFields: string[] = [];
  layout.forEach((node) => {
    if (String(node.type || '').trim().toLowerCase() !== 'field') return;
    const name = String(node.name || '').trim();
    if (!name || orderFields.includes(name)) return;
    orderFields.push(name);
  });
  const fieldNames = orderFields.length ? orderFields : Object.keys(fields);

  const view: ViewContract = {
    model: String(contract.head?.model || contract.model || ''),
    view_type: 'form',
    fields,
    layout: {
      groups: [
        {
          fields: fieldNames.map((name) => ({ name })),
        },
      ],
      headerButtons: [],
      statButtons: [],
    },
  };

  const mergedRows: Array<Record<string, unknown>> = [];
  if (Array.isArray(contract.toolbar?.header)) mergedRows.push(...(contract.toolbar?.header as Array<Record<string, unknown>>));
  if (Array.isArray(contract.buttons)) mergedRows.push(...(contract.buttons as Array<Record<string, unknown>>));

  const mapped = mergedRows.map(mapContractButton).filter((row): row is RecordRuntimeButton => Boolean(row));
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
