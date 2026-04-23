import { resolveMissingModelGuardPayload } from './actionViewLoadGuardRuntime';
import { resolveContractReadGuardPayload, resolveCapabilityGuardPayload } from './actionViewLoadGuardRuntime';
import { resolveLoadPreflightMissingModelErrorCode } from './actionViewLoadPreflightRuntime';

type Dict = Record<string, unknown>;

export function resolveLoadContractReadRedirectPayload(options: {
  contractReadAllowed: boolean;
  reasonCodeRaw: unknown;
  accessModeRaw: unknown;
}): Dict | null {
  return resolveContractReadGuardPayload({
    contractReadAllowed: options.contractReadAllowed,
    reasonCode: options.reasonCodeRaw,
    accessMode: options.accessModeRaw,
  });
}

export function resolveLoadCapabilityRedirectPayload(options: {
  stateRaw: unknown;
  missingRaw: unknown[];
}): Dict | null {
  return resolveCapabilityGuardPayload({
    state: options.stateRaw,
    missing: options.missingRaw,
  });
}

export function resolveLoadMissingModelRedirectDecision(options: {
  resolvedModel: string;
  isClientAction: boolean;
  isWindowAction: boolean;
  actionTypeRaw: unknown;
  contractDataTypeRaw: unknown;
  contractUrlRaw: unknown;
  metaUrlRaw: unknown;
  noModelCode: string;
  unsupportedCode: string;
}): { code: string; payload?: Dict } | null {
  const guard = resolveMissingModelGuardPayload({
    resolvedModel: options.resolvedModel,
    isClientAction: options.isClientAction,
    isWindowAction: options.isWindowAction,
    actionTypeRaw: options.actionTypeRaw,
    contractDataTypeRaw: options.contractDataTypeRaw,
    contractUrlRaw: options.contractUrlRaw,
    metaUrlRaw: options.metaUrlRaw,
  });
  if (!guard) return null;
  return {
    code: resolveLoadPreflightMissingModelErrorCode({
      guardCodeRaw: guard.code,
      noModelCode: options.noModelCode,
      unsupportedCode: options.unsupportedCode,
    }),
    payload: guard.payload,
  };
}

export function resolveLoadMissingResolvedModelErrorState(): {
  message: string;
  statusError: string;
  statusRecordsLength: number;
} {
  return {
    message: 'Action has no model',
    statusError: 'Action has no model',
    statusRecordsLength: 0,
  };
}

export function resolveLoadFormActionResId(options: {
  contractRaw: unknown;
  routeQueryMapRaw: unknown;
  extractActionResIdFn: (contractRaw: unknown, routeQueryMapRaw: unknown) => number | null;
}): number | null {
  return options.extractActionResIdFn(options.contractRaw, options.routeQueryMapRaw);
}
