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

export const BUSINESS_CONFIG_MODES = {
  formFieldConfiguration: 'form_field_configuration',
  lowCode: 'business_config_lowcode',
} as const;

export const BUSINESS_CONFIG_ROUTE_FLAGS = {
  returnToBusinessConfig: 'return_to_business_config',
  openPages: 'open_pages',
} as const;

export const BUSINESS_CONFIG_INTENTS = {
  formAudit: 'ui.business_config.form.audit',
  lowCodeApply: 'ui.business_config.lowcode.apply',
  contractList: 'ui.business_config.contract.list',
  contractGet: 'ui.business_config.contract.get',
  contractSave: 'ui.business_config.contract.save',
  contractPublish: 'ui.business_config.contract.publish',
  contractRollback: 'ui.business_config.contract.rollback',
  contractVersions: 'ui.business_config.contract.versions',
  listSearchAudit: 'ui.business_config.list_search.audit',
  listSearchSet: 'ui.business_config.list_search.set',
  listSearchBootstrap: 'ui.business_config.list_search.bootstrap',
  analysisAudit: 'ui.business_config.analysis.audit',
  analysisSet: 'ui.business_config.analysis.set',
  analysisBootstrap: 'ui.business_config.analysis.bootstrap',
  formBootstrap: 'ui.business_config.form.bootstrap',
  surfaceGet: 'ui.business_config.surface.get',
  snapshotCompare: 'ui.business_config.snapshot.compare',
  snapshotExport: 'ui.business_config.snapshot.export',
  coverageScan: 'ui.business_config.coverage.scan',
  coverageBootstrapListSearch: 'ui.business_config.coverage.bootstrap_list_search',
  coverageBootstrapMissing: 'ui.business_config.coverage.bootstrap_missing',
} as const;

export const MENU_CONFIG_INTENTS = {
  panelGet: 'ui.menu_config.panel.get',
  panelSet: 'ui.menu_config.panel.set',
  menuCreate: 'ui.menu_config.menu.create',
  menuDelete: 'ui.menu_config.menu.delete',
  audit: 'ui.menu_config.audit',
  rollback: 'ui.menu_config.rollback',
  versions: 'ui.menu_config.versions',
} as const;

export const APPROVAL_POLICY_INTENTS = {
  configGet: 'sc.approval_policy.config.get',
  configSet: 'sc.approval_policy.config.set',
  stepsSet: 'sc.approval_policy.steps.set',
} as const;

export function isBusinessConfigRuntimeModel(model: unknown): boolean {
  return BUSINESS_CONFIG_RUNTIME_MODELS.has(String(model || '').trim());
}

export function isBusinessConfigMode(mode: unknown): boolean {
  const value = String(mode || '').trim();
  return value === BUSINESS_CONFIG_MODES.formFieldConfiguration || value === BUSINESS_CONFIG_MODES.lowCode;
}
