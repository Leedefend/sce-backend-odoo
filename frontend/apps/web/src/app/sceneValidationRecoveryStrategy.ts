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
