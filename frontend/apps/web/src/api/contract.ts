import { intentRequestRaw, type IntentRawResult } from './intents';
import { ApiError } from './client';
import type { ActionContract } from '@sc/schema';
import { extractLiteContractFromIntentBody } from '../app/runtime/unifiedPageContractLitePilot';
import type { UnifiedPageContractLite } from '../app/contracts/unifiedPageContractLite';
import type { UnifiedPageContractV2 } from '../app/contracts/unifiedPageContractV2';

type LoadActionContractOptions = {
  recordId?: number | null;
  renderProfile?: 'create' | 'edit' | 'readonly' | null;
  surface?: 'user' | 'native' | 'hud' | null;
  sourceMode?: string | null;
};

type LoadModelContractOptions = LoadActionContractOptions & {
  viewType?: 'form' | 'tree' | 'kanban';
};

type Dict = Record<string, unknown>;
type LegacyContractRawResult = IntentRawResult<ActionContract & Dict>;

function asDict(value: unknown): Dict {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Dict : {};
}

function resolveCompatSource(v2Contract: unknown): Dict {
  const root = asDict(v2Contract);
  const meta = asDict(root.meta);
  const compat = asDict(meta.compat);
  return asDict(compat.ui_contract);
}

function adaptUnifiedPageContractV2Raw(result: IntentRawResult<Dict>): LegacyContractRawResult {
  const v2Contract = asDict(result.data);
  const source = resolveCompatSource(v2Contract);
  const legacy = asDict(source.ui_contract);
  const sourceMeta = asDict(source.source_meta);
  const adaptedData = {
    ...legacy,
    __unified_page_contract_v2: v2Contract,
  } as ActionContract & Dict;
  return {
    ...result,
    data: adaptedData,
    meta: {
      ...result.meta,
      ...sourceMeta,
      unified_page_contract_version: asDict(v2Contract.pageInfo).contractVersion,
      unified_page_contract_source: 'ui.contract.v2',
    },
    rawBody: {
      ...(asDict(result.rawBody)),
      data: adaptedData,
      unified_page_contract_v2: v2Contract,
    },
  };
}

async function requestUnifiedPageContractV2Raw(params: Record<string, unknown>) {
  const result = await intentRequestRaw<Dict>({
    intent: 'ui.contract.v2',
    params: {
      client_type: 'web_pc',
      delivery_profile: 'full',
      ...params,
    },
  });
  const adapted = adaptUnifiedPageContractV2Raw(result);
  if (!Object.keys(adapted.data || {}).length) {
    throw new ApiError('ui.contract.v2 missing legacy compatibility payload', 500, result.traceId, {
      reasonCode: 'UNIFIED_PAGE_CONTRACT_V2_COMPAT_MISSING',
      kind: 'contract',
      retryable: false,
    });
  }
  return adapted;
}

export async function loadActionUnifiedPageContractV2(actionId: number, options?: LoadActionContractOptions): Promise<UnifiedPageContractV2> {
  const result = await requestUnifiedPageContractV2Raw(buildActionContractParams(actionId, options));
  return asDict(result.data.__unified_page_contract_v2) as UnifiedPageContractV2;
}

function rethrowContractError(err: unknown, context: { op: 'action_open' | 'model'; model?: string; actionId?: number }): never {
  if (!(err instanceof ApiError)) {
    throw err;
  }
  const message = String(err.message || '').trim();
  const isNativeBlocked = err.status === 410 && message.includes('native ui.contract op is disabled');
  if (!isNativeBlocked) {
    throw err;
  }
  const subject = context.op === 'action_open'
    ? `action_id=${Number(context.actionId || 0)}`
    : `model=${String(context.model || '').trim() || '-'}`;
  throw new ApiError(
    `ui.contract blocked by delivery policy (${subject}); switch to scene-ready scene route (/s/:sceneKey)`,
    err.status,
    err.traceId,
    {
      reasonCode: 'UI_CONTRACT_NATIVE_BLOCKED',
      kind: 'contract',
      hint: 'Prefer Scene-ready contract path: system.init -> scene registry -> /s/:sceneKey',
      errorCategory: err.errorCategory,
      retryable: false,
      suggestedAction: 'open_scene_route',
      details: {
        blocked_op: context.op,
        blocked_subject: subject,
      },
    },
  );
}

function buildActionContractParams(actionId: number, options?: LoadActionContractOptions) {
  const params: Record<string, unknown> = { op: 'action_open', action_id: actionId };
  const recordId = Number(options?.recordId || 0);
  if (Number.isFinite(recordId) && recordId > 0) {
    params.record_id = recordId;
  }
  const profile = String(options?.renderProfile || '').trim().toLowerCase();
  if (profile === 'create' || profile === 'edit' || profile === 'readonly') {
    params.render_profile = profile;
  }
  const surface = String(options?.surface || '').trim().toLowerCase();
  if (surface === 'user' || surface === 'native' || surface === 'hud') {
    params.contract_surface = surface;
    if (surface === 'hud') {
      params.contract_mode = 'hud';
      params.hud = 1;
    }
  }
  const sourceMode = String(options?.sourceMode || '').trim();
  if (sourceMode) {
    params.source_mode = sourceMode;
  }
  return params;
}

export async function loadActionContract(actionId: number, options?: LoadActionContractOptions) {
  try {
    const result = await requestUnifiedPageContractV2Raw(buildActionContractParams(actionId, options));
    return result.data;
  } catch (err) {
    rethrowContractError(err, { op: 'action_open', actionId });
  }
}

export async function loadActionContractRaw(actionId: number, options?: LoadActionContractOptions) {
  try {
    return await requestUnifiedPageContractV2Raw(buildActionContractParams(actionId, options));
  } catch (err) {
    rethrowContractError(err, { op: 'action_open', actionId });
  }
}

function buildModelContractParams(model: string, options?: LoadModelContractOptions) {
  const params: Record<string, unknown> = {
    op: 'model',
    model: String(model || '').trim(),
    view_type: options?.viewType || 'form',
  };
  const recordId = Number(options?.recordId || 0);
  if (Number.isFinite(recordId) && recordId > 0) {
    params.record_id = recordId;
  }
  const profile = String(options?.renderProfile || '').trim().toLowerCase();
  if (profile === 'create' || profile === 'edit' || profile === 'readonly') {
    params.render_profile = profile;
  }
  const surface = String(options?.surface || '').trim().toLowerCase();
  if (surface === 'user' || surface === 'native' || surface === 'hud') {
    params.contract_surface = surface;
    if (surface === 'hud') {
      params.contract_mode = 'hud';
      params.hud = 1;
    }
  }
  const sourceMode = String(options?.sourceMode || '').trim();
  if (sourceMode) {
    params.source_mode = sourceMode;
  }
  return params;
}

export async function loadModelContractRaw(model: string, options?: LoadModelContractOptions) {
  try {
    return await requestUnifiedPageContractV2Raw(buildModelContractParams(model, options));
  } catch (err) {
    rethrowContractError(err, { op: 'model', model });
  }
}

export async function loadModelUnifiedPageContractV2(model: string, options?: LoadModelContractOptions): Promise<UnifiedPageContractV2> {
  const result = await requestUnifiedPageContractV2Raw(buildModelContractParams(model, options));
  return asDict(result.data.__unified_page_contract_v2) as UnifiedPageContractV2;
}

export async function loadModelLitePreviewContract(model: string, options?: LoadModelContractOptions): Promise<UnifiedPageContractLite | null> {
  const viewType = options?.viewType || 'tree';
  const result = await intentRequestRaw<Record<string, unknown>>({
    intent: 'load_contract',
    params: {
      model: String(model || '').trim(),
      view_type: viewType,
      include: 'all',
      contractMode: 'lite_preview',
      contractVersion: '2.0.0',
      entryPoint: 'load_contract',
      clientType: 'web_pc',
      fallbackMode: 'legacy_default',
      traceId: `lite-frontend-pilot-${String(model || '').trim() || 'model'}-${viewType}`,
    },
  });
  return extractLiteContractFromIntentBody(result.rawBody);
}
