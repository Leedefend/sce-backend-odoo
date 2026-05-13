import { intentRequestRaw } from '../../../api/intents';
import { decodeContractV2Snapshot } from './schema';
import { createContractV2Store } from './store';
import type { ContractV2Dictionary, ContractV2NormalizedStore, ContractV2Snapshot } from './types';

export interface ContractV2LoadOptions {
  recordId?: number;
  viewType?: string;
  renderProfile?: 'create' | 'edit' | 'readonly';
  surface?: 'user' | 'native' | 'hud';
  sourceMode?: string;
  context?: ContractV2Dictionary;
  contextRaw?: string;
}

export interface ContractV2LoadResult {
  snapshot: ContractV2Snapshot;
  store: ContractV2NormalizedStore;
  traceId: string;
  rawBody?: unknown;
}

function normalizedRecordId(value: unknown): number {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : 0;
}

function applyCommonOptions(params: ContractV2Dictionary, options: ContractV2LoadOptions = {}): ContractV2Dictionary {
  const recordId = normalizedRecordId(options.recordId);
  if (recordId) params.record_id = recordId;
  if (options.viewType) params.view_type = options.viewType;
  if (options.renderProfile) params.render_profile = options.renderProfile;
  if (options.surface) params.contract_surface = options.surface;
  if (options.sourceMode) params.source_mode = options.sourceMode;
  if (options.context && typeof options.context === 'object' && !Array.isArray(options.context)) {
    params.context = options.context;
  }
  if (options.contextRaw) params.context_raw = options.contextRaw;
  params.contractVersion = '2.0.0';
  params.clientType = 'web_pc';
  params.accepted_contract_versions = ['2.0.x'];
  params.client_contract_capabilities = [
    'container_tree.v2',
    'data_source.v2',
    'action_rule.v2',
    'relation_entry.v2',
    'status_contract.v2',
  ];
  return params;
}

async function loadContractV2(params: ContractV2Dictionary): Promise<ContractV2LoadResult> {
  const response = await intentRequestRaw<ContractV2Dictionary>({
    intent: 'load_contract',
    params,
  });
  const snapshot = decodeContractV2Snapshot({
    data: response.data,
    rawBody: response.rawBody,
  });
  return {
    snapshot,
    store: createContractV2Store(snapshot),
    traceId: response.traceId,
    rawBody: response.rawBody,
  };
}

export function loadActionContractV2(actionId: number, options: ContractV2LoadOptions = {}): Promise<ContractV2LoadResult> {
  return loadContractV2(applyCommonOptions({
    op: 'action_open',
    action_id: normalizedRecordId(actionId),
  }, options));
}

export function loadModelContractV2(model: string, options: ContractV2LoadOptions = {}): Promise<ContractV2LoadResult> {
  return loadContractV2(applyCommonOptions({
    op: 'model',
    model: String(model || '').trim(),
    view_type: options.viewType || 'form',
  }, options));
}
