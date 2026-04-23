type Dict = Record<string, unknown>;

export function resolveContractReadGuardPayload(options: {
  contractReadAllowed: boolean;
  reasonCode?: unknown;
  accessMode?: unknown;
}): Dict | null {
  if (options.contractReadAllowed) return null;
  return {
    diag: {
      diag: 'contract_read_forbidden',
      diag_reason_code: String(options.reasonCode || '').trim() || undefined,
      diag_access_mode: String(options.accessMode || '').trim() || undefined,
    },
  };
}

export function resolveCapabilityGuardPayload(options: {
  state?: unknown;
  missing?: unknown[];
}): Dict | null {
  const state = String(options.state || '').trim().toLowerCase();
  if (!state || state === 'enabled') return null;
  const missing = Array.isArray(options.missing)
    ? options.missing.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  return {
    public: {
      missing: missing.join(',') || undefined,
    },
  };
}

export function resolveActionViewResolvedModel(options: {
  metaModelRaw?: unknown;
  routeModelRaw?: unknown;
  contractModelRaw?: unknown;
}): string {
  return String(options.metaModelRaw || options.routeModelRaw || options.contractModelRaw || '').trim();
}

export function resolveMissingModelGuardPayload(options: {
  resolvedModel: string;
  isClientAction: boolean;
  isWindowAction: boolean;
  actionTypeRaw?: unknown;
  contractDataTypeRaw?: unknown;
  contractUrlRaw?: unknown;
  metaUrlRaw?: unknown;
}): { code: 'ACT_NO_MODEL' | 'ACT_UNSUPPORTED_TYPE'; payload?: Dict } | null {
  if (options.resolvedModel) return null;
  if (options.isClientAction) {
    return { code: 'ACT_NO_MODEL' };
  }
  if (!options.isWindowAction) {
    return {
      code: 'ACT_UNSUPPORTED_TYPE',
      payload: {
        diag: {
          diag: 'non_window_action',
          diag_action_type: String(options.actionTypeRaw || '').trim() || undefined,
          diag_contract_type: String(options.contractDataTypeRaw || '').trim().toLowerCase() || undefined,
          diag_contract_url: String(options.contractUrlRaw || '').trim() || undefined,
          diag_meta_url: String(options.metaUrlRaw || '').trim() || undefined,
        },
      },
    };
  }
  return null;
}

