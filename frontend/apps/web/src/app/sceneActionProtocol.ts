export interface MutationContract {
  type: string;
  model: string;
  operation: string;
  execute_intent?: string;
  payload_schema?: Record<string, unknown>;
}

export interface ProjectionRefreshPolicy {
  on_success: string[];
  on_failure?: string[];
  mode?: string;
  scope?: string;
  debounce_ms?: number;
}

export interface SceneActionProtocol {
  id: string;
  label: string;
  intent: string;
  target_scene?: string;
  mutation?: MutationContract;
  refresh_policy?: ProjectionRefreshPolicy;
  visibility?: Record<string, unknown>;
  raw: Record<string, unknown>;
}

function asDict(value: unknown): Record<string, unknown> {
  return (value && typeof value === 'object' && !Array.isArray(value))
    ? (value as Record<string, unknown>)
    : {};
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function asTextArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => asText(item)).filter(Boolean);
}

export function normalizeSceneActionProtocol(row: unknown): SceneActionProtocol | null {
  const payload = asDict(row);
  const id = asText(payload.id || payload.key || payload.name);
  if (!id) return null;

  const target = asDict(payload.target);
  const mutationRaw = asDict(payload.mutation || target.mutation);
  const refreshRaw = asDict(payload.refresh_policy || target.refresh_policy);

  const mutation = (asText(mutationRaw.type) && asText(mutationRaw.model) && asText(mutationRaw.operation))
    ? {
        type: asText(mutationRaw.type),
        model: asText(mutationRaw.model),
        operation: asText(mutationRaw.operation),
        execute_intent: asText(mutationRaw.execute_intent || mutationRaw.payload_schema?.execute_intent) || undefined,
        payload_schema: asDict(mutationRaw.payload_schema),
      }
    : undefined;

  const onSuccess = asTextArray(refreshRaw.on_success);
  const refreshPolicy = onSuccess.length
    ? {
        on_success: onSuccess,
        on_failure: asTextArray(refreshRaw.on_failure),
        mode: asText(refreshRaw.mode) || undefined,
        scope: asText(refreshRaw.scope) || undefined,
        debounce_ms: Number(refreshRaw.debounce_ms || 0) || undefined,
      }
    : undefined;

  return {
    id,
    label: asText(payload.label || id),
    intent: asText(payload.intent),
    target_scene: asText(payload.target_scene || target.scene_key),
    mutation,
    refresh_policy: refreshPolicy,
    visibility: asDict(payload.visibility),
    raw: payload,
  };
}
