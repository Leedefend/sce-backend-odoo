import type { ActionContract } from '@sc/schema';
import {
  resolveUnifiedPageContractV2MainData,
  resolveUnifiedPageContractV2SourceContext,
} from '../../app/contracts/unifiedPageContractV2';
import type { ContractV2NormalizedStore } from '../../app/contracts/v2/types';
import { normalizeRelationIds } from './fieldUtils';
import { normalizeRouteDefault } from './valueUtils';

export function formCreateContext(params: {
  contract: ActionContract | null;
  v2ContractStore: ContractV2NormalizedStore | null;
}) {
  const storeContext = resolveUnifiedPageContractV2SourceContext(params.v2ContractStore);
  return (Object.keys(storeContext).length ? storeContext : resolveUnifiedPageContractV2SourceContext(params.contract)).context || {};
}

export function resolveCreateDefaults(params: {
  contract: ActionContract | null;
  routeQuery: Record<string, unknown>;
  selectedProject?: Record<string, unknown> | null;
  v2ContractStore: ContractV2NormalizedStore | null;
}) {
  const storeMainData = resolveUnifiedPageContractV2MainData(params.v2ContractStore);
  const defaults: Record<string, unknown> = {
    ...(Object.keys(storeMainData).length ? storeMainData : resolveUnifiedPageContractV2MainData(params.contract)),
  };
  Object.entries(params.routeQuery).forEach(([key, value]) => {
    if (key.startsWith('default_')) {
      defaults[key.replace(/^default_/, '')] = normalizeRouteDefault(value);
    }
  });
  const context = formCreateContext(params);
  Object.entries(context).forEach(([key, value]) => {
    if (key.startsWith('default_') && !(key.replace(/^default_/, '') in defaults)) {
      defaults[key.replace(/^default_/, '')] = value;
    }
  });
  const validator = params.contract?.validator as Record<string, unknown> | undefined;
  const defaultsSample = validator?.defaults_sample;
  if (defaultsSample && typeof defaultsSample === 'object' && !Array.isArray(defaultsSample)) {
    Object.entries(defaultsSample as Record<string, unknown>).forEach(([key, value]) => {
      if (!(key in defaults)) {
        defaults[key] = value === 'dynamic' ? '' : value;
      }
    });
  }
  const selectedProject = params.selectedProject;
  const selectedProjectId = Number(selectedProject?.id || 0);
  if (
    selectedProjectId > 0
    && params.contract?.fields?.project_id
    && normalizeRelationIds(defaults.project_id).length === 0
  ) {
    defaults.project_id = [
      selectedProjectId,
      selectedProject?.display_name || selectedProject?.name || `项目 ${selectedProjectId}`,
    ];
  }
  const selectedStrategy = String(selectedProject?.operation_strategy || '').trim();
  if (
    selectedStrategy
    && params.contract?.fields?.operation_strategy
    && !String(defaults.operation_strategy || '').trim()
  ) {
    defaults.operation_strategy = selectedStrategy;
  }
  const selectedOwnerId = Number(selectedProject?.owner_id || 0);
  if (
    selectedOwnerId > 0
    && params.contract?.fields?.owner_id
    && normalizeRelationIds(defaults.owner_id).length === 0
  ) {
    defaults.owner_id = [
      selectedOwnerId,
      selectedProject?.owner_name || `业主 ${selectedOwnerId}`,
    ];
  }
  return defaults;
}
