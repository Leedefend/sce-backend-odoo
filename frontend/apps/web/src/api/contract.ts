import { intentRequest } from './intents';
import type { ActionContract } from '@sc/schema';

export async function loadActionContract(actionId: number) {
  return intentRequest<ActionContract>({
    intent: 'ui.contract',
    params: { op: 'action_open', action_id: actionId },
  });
}
