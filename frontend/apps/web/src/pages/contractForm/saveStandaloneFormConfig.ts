import { intentRequest } from '../../api/intents';
import { BUSINESS_CONFIG_INTENTS } from '../../app/businessConfigBoundaries';

/** Compatibility path for a form designer opened outside the unified workbench. */
export function saveStandaloneFormConfig(params: {
  baseParams: Record<string, unknown>;
  name: string;
  model: string;
  contractPayload: Record<string, unknown>;
}) {
  return intentRequest<{ precheck?: { warnings?: string[]; errors?: string[] } }>({
    intent: BUSINESS_CONFIG_INTENTS.contractSave,
    params: {
      ...params.baseParams,
      name: params.name,
      model: params.model,
      view_type: 'form',
      publish: true,
      contract_json: params.contractPayload,
    },
  });
}
