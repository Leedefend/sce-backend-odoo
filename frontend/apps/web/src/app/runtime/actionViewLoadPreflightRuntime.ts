import { resolveActionViewContractLimit, resolveActionViewSortSeed } from './actionViewLoadRequestRuntime';

export function resolveLoadPreflightContractFlags(options: {
  contractReadAllowedRaw: unknown;
  warningsRaw: unknown;
  degradedRaw: unknown;
}): {
  contractReadAllowed: boolean;
  contractWarningCount: number;
  contractDegraded: boolean;
} {
  return {
    contractReadAllowed: Boolean(options.contractReadAllowedRaw),
    contractWarningCount: Array.isArray(options.warningsRaw) ? options.warningsRaw.length : 0,
    contractDegraded: Boolean(options.degradedRaw),
  };
}

export function resolveLoadPreflightSortValue(options: {
  currentSortRaw: unknown;
  sceneReadyDefaultSortRaw: unknown;
  sceneDefaultSortRaw: unknown;
  searchDefaultOrderRaw: unknown;
  viewOrderRaw: unknown;
  metaOrderRaw: unknown;
  fallbackSortRaw: unknown;
}): string {
  return resolveActionViewSortSeed({
    currentSortRaw: options.currentSortRaw,
    sceneReadyDefaultSortRaw: options.sceneReadyDefaultSortRaw,
    sceneDefaultSortRaw: options.sceneDefaultSortRaw,
    searchDefaultOrderRaw: options.searchDefaultOrderRaw,
    viewOrderRaw: options.viewOrderRaw,
    metaOrderRaw: options.metaOrderRaw,
    fallbackSortRaw: options.fallbackSortRaw,
  });
}

export function resolveLoadPreflightContractLimit(options: {
  searchDefaultLimitRaw: unknown;
}): number {
  return resolveActionViewContractLimit(options.searchDefaultLimitRaw);
}

export function resolveLoadPreflightFieldFlags(options: {
  listProfileRaw?: unknown;
}): {
  hasActiveField: boolean;
  hasAssigneeField: boolean;
} {
  const profile = options.listProfileRaw && typeof options.listProfileRaw === 'object'
    ? (options.listProfileRaw as Record<string, unknown>)
    : {};
  const batchPolicy = profile.batch_policy && typeof profile.batch_policy === 'object'
    ? (profile.batch_policy as Record<string, unknown>)
    : {};
  const activeField = String(batchPolicy.active_field || '').trim();
  const assigneeField = String(batchPolicy.assignee_field || '').trim();
  return {
    hasActiveField: Boolean(activeField),
    hasAssigneeField: Boolean(assigneeField),
  };
}

export function resolveLoadPreflightMissingModelErrorCode(options: {
  guardCodeRaw: unknown;
  noModelCode: string;
  unsupportedCode: string;
}): string {
  return String(options.guardCodeRaw || '') === 'ACT_NO_MODEL'
    ? options.noModelCode
    : options.unsupportedCode;
}
