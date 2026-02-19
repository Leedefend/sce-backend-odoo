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

type FormFieldNode = { name?: string; string?: string };

type FormGroupNode = {
  fields?: FormFieldNode[];
  sub_groups?: FormGroupNode[];
};

type FormPageNode = {
  title?: string | null;
  groups?: FormGroupNode[];
};

type FormNotebookNode = {
  pages?: FormPageNode[];
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
  const fields = contract.fields || {};
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
  const merged = normalizeUniqueFields([...normalized, ...fallback, ...Object.keys(fields)]);
  return merged;
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
  const fields = contract.fields || {};
  const fieldNames = extractFieldOrder(contract);

  const view: ViewContract = {
    model: String(contract.head?.model || contract.model || ''),
    view_type: 'form',
    fields,
    layout: buildLayout(contract, fieldNames),
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
