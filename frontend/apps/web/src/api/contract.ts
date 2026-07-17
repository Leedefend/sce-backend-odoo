import { intentRequestRaw } from './intents';
import { ApiError } from './client';
import { extractLiteContractFromIntentBody } from '../app/runtime/unifiedPageContractLitePilot';
import type { UnifiedPageContractLite } from '../app/contracts/unifiedPageContractLite';
import { LITE_PREVIEW_LEGACY_FALLBACK_MODE } from '../app/contracts/unifiedPageContractLiteCompat';
import type { UnifiedPageContractV2 } from '../app/contracts/unifiedPageContractV2';
import { adaptUnifiedPageContractV2Raw } from '../app/runtime/unifiedPageContractV2CompatProjection';

type LoadActionContractOptions = {
  viewId?: number | null;
  menuId?: number | null;
  viewType?: 'form' | 'tree' | 'list' | 'kanban' | 'pivot' | 'graph' | 'calendar' | 'gantt' | 'activity' | 'dashboard' | null;
  recordId?: number | null;
  renderProfile?: 'create' | 'edit' | 'readonly' | null;
  surface?: 'user' | 'native' | 'hud' | null;
  sourceMode?: string | null;
  context?: Record<string, unknown> | null;
  contextRaw?: string | null;
  previewToken?: string | null;
  previewRoleKey?: string | null;
};

type LoadModelContractOptions = LoadActionContractOptions & {
  viewType?: 'form' | 'tree' | 'kanban';
};

type Dict = Record<string, unknown>;

function asDict(value: unknown): Dict {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Dict : {};
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
  const adapted = adaptUnifiedPageContractV2Raw(result, params);
  if (!Object.keys(adapted.data || {}).length) {
    throw new ApiError('ui.contract.v2 missing projection payload', 500, result.traceId, {
      reasonCode: 'UNIFIED_PAGE_CONTRACT_V2_PROJECTION_MISSING',
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
  const menuId = Number(options?.menuId || 0);
  if (Number.isFinite(menuId) && menuId > 0) {
    params.menu_id = menuId;
  }
  const viewType = String(options?.viewType || '').trim().toLowerCase();
  if (viewType) {
    params.view_type = viewType === 'list' ? 'tree' : viewType;
  }
  const viewId = Number(options?.viewId || 0);
  if (Number.isFinite(viewId) && viewId > 0) {
    params.view_id = viewId;
  }
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
  if (options?.context && typeof options.context === 'object' && !Array.isArray(options.context)) {
    params.context = options.context;
  }
  const contextRaw = String(options?.contextRaw || '').trim();
  if (contextRaw) {
    params.context_raw = contextRaw;
  }
  const previewToken = String(options?.previewToken || '').trim();
  if (previewToken) params.preview_token = previewToken;
  const previewRoleKey = String(options?.previewRoleKey || '').trim();
  if (previewRoleKey) params.preview_role_key = previewRoleKey;
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
  const viewId = Number(options?.viewId || 0);
  if (Number.isFinite(viewId) && viewId > 0) {
    params.view_id = viewId;
  }
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
  if (options?.context && typeof options.context === 'object' && !Array.isArray(options.context)) {
    params.context = options.context;
  }
  const contextRaw = String(options?.contextRaw || '').trim();
  if (contextRaw) {
    params.context_raw = contextRaw;
  }
  const previewToken = String(options?.previewToken || '').trim();
  if (previewToken) params.preview_token = previewToken;
  const previewRoleKey = String(options?.previewRoleKey || '').trim();
  if (previewRoleKey) params.preview_role_key = previewRoleKey;
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
      fallbackMode: LITE_PREVIEW_LEGACY_FALLBACK_MODE,
      traceId: `lite-frontend-pilot-${String(model || '').trim() || 'model'}-${viewType}`,
    },
  });
  return extractLiteContractFromIntentBody(result.rawBody);
}
