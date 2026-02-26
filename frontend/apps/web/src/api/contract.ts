import { intentRequest, intentRequestRaw } from './intents';
import type { ActionContract } from '@sc/schema';

type LoadActionContractOptions = {
  recordId?: number | null;
  renderProfile?: 'create' | 'edit' | 'readonly' | null;
};

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
  return params;
}

export async function loadActionContract(actionId: number, options?: LoadActionContractOptions) {
  return intentRequest<ActionContract>({
    intent: 'ui.contract',
    params: buildActionContractParams(actionId, options),
  });
}

export async function loadActionContractRaw(actionId: number, options?: LoadActionContractOptions) {
  return intentRequestRaw<ActionContract & Record<string, unknown>>({
    intent: 'ui.contract',
    params: buildActionContractParams(actionId, options),
  });
}
