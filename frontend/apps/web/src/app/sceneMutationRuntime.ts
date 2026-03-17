import { intentRequestRaw } from '../api/intents';
import type { MutationContract } from './sceneActionProtocol';

export interface SceneMutationExecuteInput {
  mutation: MutationContract;
  actionKey: string;
  recordId?: number | null;
  model?: string;
  context?: Record<string, unknown>;
}

export interface SceneMutationExecuteResult {
  intent: string;
  traceId: string;
  data: Record<string, unknown>;
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function asInt(value: unknown): number {
  const num = Number(value || 0);
  return Number.isFinite(num) && num > 0 ? Math.trunc(num) : 0;
}

function resolveIntentByMutation(mutation: MutationContract): string {
  const model = asText(mutation.model).toLowerCase();
  if (model === 'finance.payment.request' || model === 'payment.request') {
    return 'payment.request.execute';
  }
  if (model === 'project.risk.action') {
    return 'risk.action.execute';
  }
  return '';
}

function buildParams(input: SceneMutationExecuteInput): Record<string, unknown> {
  const mutation = input.mutation;
  const operation = asText(mutation.operation).toLowerCase();
  const model = asText(mutation.model).toLowerCase();
  const context = (input.context && typeof input.context === 'object')
    ? (input.context as Record<string, unknown>)
    : {};
  const recordId = asInt(input.recordId);

  if (model === 'finance.payment.request' || model === 'payment.request') {
    return {
      id: asInt(context.id) || asInt(context.record_id) || recordId,
      action: operation,
      reason: asText(context.reason),
    };
  }

  if (model === 'project.risk.action') {
    return {
      action: operation,
      risk_action_id: asInt(context.risk_action_id) || recordId,
      project_id: asInt(context.project_id),
      name: asText(context.name),
      risk_level: asText(context.risk_level),
      note: asText(context.note),
      owner_id: asInt(context.owner_id),
    };
  }

  return {
    action: operation,
    id: asInt(context.id) || asInt(context.record_id) || recordId,
  };
}

export async function executeSceneMutation(input: SceneMutationExecuteInput): Promise<SceneMutationExecuteResult> {
  const intent = resolveIntentByMutation(input.mutation);
  if (!intent) {
    throw new Error(`unsupported mutation model: ${input.mutation.model}`);
  }
  const params = buildParams(input);
  const response = await intentRequestRaw<Record<string, unknown>>({
    intent,
    params,
  });
  return {
    intent,
    traceId: response.traceId,
    data: response.data,
  };
}
