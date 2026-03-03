import { intentRequest } from './intents';

export type OnchangeResponse = {
  schema_version?: string;
  patch?: Record<string, unknown>;
  modifiers_patch?: Record<string, Record<string, unknown>>;
  line_patches?: Array<Record<string, unknown>>;
  warnings?: Array<{ title?: string; message?: string }>;
  applied_fields?: string[];
};

export async function triggerOnchange(params: {
  model: string;
  res_id?: number | null;
  values: Record<string, unknown>;
  changed_fields: string[];
  context?: Record<string, unknown>;
}) {
  return intentRequest<OnchangeResponse>({
    intent: 'api.onchange',
    params: {
      model: params.model,
      res_id: params.res_id || undefined,
      values: params.values,
      changed_fields: params.changed_fields,
      context: params.context || {},
    },
  });
}
