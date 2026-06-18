const BUSINESS_CONFIG_RUNTIME_MODELS = new Set([
  'sc.approval.policy',
  'sc.approval.step',
  'sc.approval.scope',
  'sc.approval.scope.user.wizard',
  'ui.business.config.contract',
  'ui.form.field.policy',
  'ui.form.custom.field.wizard',
  'ui.menu.config.policy',
]);

export function isBusinessConfigRuntimeModel(model: unknown): boolean {
  return BUSINESS_CONFIG_RUNTIME_MODELS.has(String(model || '').trim());
}

