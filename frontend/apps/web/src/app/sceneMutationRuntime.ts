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

function asDict(value: unknown): Record<string, unknown> {
  return (value && typeof value === 'object' && !Array.isArray(value))
    ? (value as Record<string, unknown>)
    : {};
}

function resolveIntentByMutation(mutation: MutationContract): string {
  const payloadSchema = asDict(mutation.payload_schema);
  const explicitIntent = asText(mutation.execute_intent || payloadSchema.execute_intent);
  if (explicitIntent) return explicitIntent;
  return '';
}

function buildParams(input: SceneMutationExecuteInput): Record<string, unknown> {
  const mutation = input.mutation;
  const operation = asText(mutation.operation).toLowerCase();
  const payloadSchema = asDict(mutation.payload_schema);
  const context = (input.context && typeof input.context === 'object')
    ? (input.context as Record<string, unknown>)
    : {};
  const recordId = asInt(input.recordId);
  const params: Record<string, unknown> = {
    ...context,
    action: operation,
  };
  const requiredKeys = Array.isArray(payloadSchema.required)
    ? payloadSchema.required.map((item) => asText(item).toLowerCase()).filter(Boolean)
    : [];
  const idLikeKey = requiredKeys.find((item) => item === 'id' || item === 'record_id' || item.endsWith('_id')) || 'id';
  const resolvedRecordId = asInt(context[idLikeKey]) || asInt(context.id) || asInt(context.record_id) || recordId;
  if (resolvedRecordId > 0 && !params[idLikeKey]) {
    params[idLikeKey] = resolvedRecordId;
  }
  return params;
}

export async function executeSceneMutation(input: SceneMutationExecuteInput): Promise<SceneMutationExecuteResult> {
  const intent = resolveIntentByMutation(input.mutation);
  if (!intent) {
    throw new Error('missing execute_intent in mutation contract');
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
