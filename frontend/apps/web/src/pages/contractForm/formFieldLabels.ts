import { resolveUnifiedPageContractV2BusinessOperationProfile, resolveUnifiedPageContractV2FormStructureContract } from '../../app/contracts/unifiedPageContractV2';
import { dictOrEmpty, mergeFieldLabelsFromSource } from './recordUtils';

export function resolveContractFormFieldLabels(contractSource: unknown, snapshotSource: unknown) {
  const labels: Record<string, string> = {};
  const snapshot = dictOrEmpty(snapshotSource);
  const source = Object.keys(snapshot).length ? snapshot : contractSource;
  const businessProfile = resolveUnifiedPageContractV2BusinessOperationProfile(source);
  Object.entries(dictOrEmpty(businessProfile.field_labels)).forEach(([name, value]) => {
    const label = String(value || '').trim();
    if (name && label) labels[name] = label;
  });
  mergeFieldLabelsFromSource(resolveUnifiedPageContractV2FormStructureContract(source), labels);
  mergeFieldLabelsFromSource(snapshot.formStructureContract, labels);
  mergeFieldLabelsFromSource(dictOrEmpty(contractSource).formStructureContract, labels);
  return labels;
}
