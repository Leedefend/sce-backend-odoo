import type { ContractV2ActionRule, ContractV2Dictionary, ContractV2NormalizedStore } from './types';

export interface ContractV2RuntimeActionPlan {
  action: ContractV2ActionRule;
  params: ContractV2Dictionary;
}

export interface ContractV2RuntimeDataSourcePlan {
  dataKey: string;
  source: ContractV2Dictionary;
  params: ContractV2Dictionary;
}

export function resolveContractV2ActionPlan(
  store: ContractV2NormalizedStore,
  actionId: string,
  params: ContractV2Dictionary = {},
): ContractV2RuntimeActionPlan | null {
  const action = store.actionsById.get(actionId);
  if (!action) return null;
  return { action, params };
}

export function resolveContractV2DataSourcePlan(
  store: ContractV2NormalizedStore,
  dataKey: string,
  params: ContractV2Dictionary = {},
): ContractV2RuntimeDataSourcePlan | null {
  const source = store.snapshot.dataContract.dataSource[dataKey];
  if (!source) return null;
  return { dataKey, source, params };
}
