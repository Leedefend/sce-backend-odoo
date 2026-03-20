import { intentRequest, intentRequestRaw } from './intents';
import { ApiError } from './client';
import type { ActionContract } from '@sc/schema';

type LoadActionContractOptions = {
  recordId?: number | null;
  renderProfile?: 'create' | 'edit' | 'readonly' | null;
  surface?: 'user' | 'native' | 'hud' | null;
  sourceMode?: string | null;
};

type LoadModelContractOptions = LoadActionContractOptions & {
  viewType?: 'form' | 'tree' | 'kanban';
};

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
    return await intentRequest<ActionContract>({
      intent: 'ui.contract',
      params: buildActionContractParams(actionId, options),
    });
  } catch (err) {
    rethrowContractError(err, { op: 'action_open', actionId });
  }
}

export async function loadActionContractRaw(actionId: number, options?: LoadActionContractOptions) {
  try {
    return await intentRequestRaw<ActionContract & Record<string, unknown>>({
      intent: 'ui.contract',
      params: buildActionContractParams(actionId, options),
    });
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
    return await intentRequestRaw<ActionContract & Record<string, unknown>>({
      intent: 'ui.contract',
      params: buildModelContractParams(model, options),
    });
  } catch (err) {
    rethrowContractError(err, { op: 'model', model });
  }
}
