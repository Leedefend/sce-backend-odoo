export const BUSINESS_CONFIG_MODELS = {
  approvalPolicy: 'sc.approval.policy',
  approvalStep: 'sc.approval.step',
  approvalScope: 'sc.approval.scope',
  approvalScopeUserWizard: 'sc.approval.scope.user.wizard',
  contract: 'ui.business.config.contract',
  formFieldPolicy: 'ui.form.field.policy',
  formCustomFieldWizard: 'ui.form.custom.field.wizard',
  menuConfigPolicy: 'ui.menu.config.policy',
} as const;

const BUSINESS_CONFIG_RUNTIME_MODELS = new Set<string>(Object.values(BUSINESS_CONFIG_MODELS));

export const BUSINESS_CONFIG_MODES = {
  formFieldConfiguration: 'form_field_configuration',
  lowCode: 'business_config_lowcode',
} as const;

export const BUSINESS_CONFIG_ACTION_KEYS = {
  currentFormFieldSettings: 'current_form_field_settings',
  currentFormAddCustomField: 'current_form_add_custom_field',
  currentFormFieldOrderSave: 'current_form_field_order_save',
  currentFormFieldConfiguration: 'current_form_field_configuration',
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
  snapshotSummary: 'ui.business_config.snapshot.summary',
  snapshotCompare: 'ui.business_config.snapshot.compare',
  snapshotExport: 'ui.business_config.snapshot.export',
  coverageScan: 'ui.business_config.coverage.scan',
  coverageBootstrapListSearch: 'ui.business_config.coverage.bootstrap_list_search',
  coverageBootstrapMissing: 'ui.business_config.coverage.bootstrap_missing',
} as const;

export const FORM_FIELD_CONFIG_INTENTS = {
  policySet: 'ui.form_field_policy.set',
  customFieldCreate: 'ui.form_custom_field.create',
  orderSet: 'ui.form_field_order.set',
  batchSet: 'ui.form_field_config.batch_set',
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

export const MENU_CONFIG_POLICY_MODEL = 'ui.menu.config.policy';

export const MENU_CONFIG_RUNTIME_SOURCES = {
  policy: MENU_CONFIG_POLICY_MODEL,
  contract: 'ui.business.config.contract.menu_orchestration',
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
