export type SceneValidationRecoveryContext = {
  modelName: string;
  recordId: number | null;
  actionId: number | null;
  sceneKey: string;
  roleCode: string;
};

export type SceneValidationRecoveryStrategy = {
  preferredRecordModels: string[];
  actionPreferredRoleTokens: string[];
};

export type SceneValidationRecoveryStrategyRuntimePayload = {
  default?: Partial<SceneValidationRecoveryStrategy>;
  by_role?: Record<string, Partial<SceneValidationRecoveryStrategy>>;
  by_company?: Record<string, Partial<SceneValidationRecoveryStrategy>>;
  by_company_role?: Record<string, Partial<SceneValidationRecoveryStrategy>>;
};

export type SceneValidationRecoveryRuntimeContext = {
  roleCode?: string;
  companyId?: number | null;
};

const DEFAULT_STRATEGY: SceneValidationRecoveryStrategy = {
  preferredRecordModels: ['project.project', 'project.task', 'purchase.order', 'account.move'],
  actionPreferredRoleTokens: ['operator', 'staff', 'clerk'],
};

let runtimeStrategy: SceneValidationRecoveryStrategy = { ...DEFAULT_STRATEGY };

export function setSceneValidationRecoveryStrategy(overrides?: Partial<SceneValidationRecoveryStrategy>) {
  runtimeStrategy = {
    preferredRecordModels: Array.isArray(overrides?.preferredRecordModels)
      ? overrides?.preferredRecordModels.map((item) => String(item || '').trim()).filter(Boolean)
      : [...DEFAULT_STRATEGY.preferredRecordModels],
    actionPreferredRoleTokens: Array.isArray(overrides?.actionPreferredRoleTokens)
      ? overrides?.actionPreferredRoleTokens.map((item) => String(item || '').trim().toLowerCase()).filter(Boolean)
      : [...DEFAULT_STRATEGY.actionPreferredRoleTokens],
  };
}

function _mergeStrategy(base: SceneValidationRecoveryStrategy, ext?: Partial<SceneValidationRecoveryStrategy>) {
  return {
    preferredRecordModels: Array.isArray(ext?.preferredRecordModels)
      ? ext?.preferredRecordModels.map((item) => String(item || '').trim()).filter(Boolean)
      : [...base.preferredRecordModels],
    actionPreferredRoleTokens: Array.isArray(ext?.actionPreferredRoleTokens)
      ? ext?.actionPreferredRoleTokens.map((item) => String(item || '').trim().toLowerCase()).filter(Boolean)
      : [...base.actionPreferredRoleTokens],
  };
}

export function applySceneValidationRecoveryStrategyRuntime(
  payload?: SceneValidationRecoveryStrategyRuntimePayload,
  context: SceneValidationRecoveryRuntimeContext = {},
) {
  const roleCode = String(context.roleCode || '').trim().toLowerCase();
  const companyKey = Number.isFinite(Number(context.companyId || 0)) && Number(context.companyId || 0) > 0
    ? String(Number(context.companyId || 0))
    : '';
  const base = _mergeStrategy(DEFAULT_STRATEGY, payload?.default);
  let resolved = { ...base };

  if (companyKey && payload?.by_company?.[companyKey]) {
    resolved = _mergeStrategy(resolved, payload.by_company[companyKey]);
  }
  if (roleCode && payload?.by_role?.[roleCode]) {
    resolved = _mergeStrategy(resolved, payload.by_role[roleCode]);
  }
  if (companyKey && roleCode) {
    const key = `${companyKey}:${roleCode}`;
    if (payload?.by_company_role?.[key]) {
      resolved = _mergeStrategy(resolved, payload.by_company_role[key]);
    }
  }
  runtimeStrategy = resolved;
}

export function resolveSceneValidationSuggestedAction(ctx: SceneValidationRecoveryContext): string {
  const modelName = String(ctx.modelName || '').trim();
  const roleCode = String(ctx.roleCode || '').trim().toLowerCase();
  const sceneKey = String(ctx.sceneKey || '').trim();
  const recordId = Number(ctx.recordId || 0);
  const actionId = Number(ctx.actionId || 0);

  if (recordId > 0 && modelName && runtimeStrategy.preferredRecordModels.includes(modelName)) {
    return `open_record:${modelName}:${recordId}`;
  }
  if (actionId > 0 && runtimeStrategy.actionPreferredRoleTokens.some((token) => roleCode.includes(token))) {
    return `open_action:${actionId}`;
  }
  if (sceneKey) {
    return `open_scene:${sceneKey}`;
  }
  if (actionId > 0) {
    return `open_action:${actionId}`;
  }
  return 'copy_reason';
}
