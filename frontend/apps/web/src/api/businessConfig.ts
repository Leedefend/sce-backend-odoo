import { intentRequest } from './intents';
import { APPROVAL_POLICY_INTENTS, BUSINESS_CONFIG_INTENTS } from '../app/businessConfigBoundaries';

export type BusinessConfigChangeSetState = 'draft' | 'validating' | 'ready' | 'publishing' | 'published' | 'failed' | 'discarded' | 'superseded';

export interface BusinessConfigChangeSetItem {
  id: number;
  config_type: 'form' | 'list' | 'search' | 'analysis' | 'menu';
  target_key: string;
  model: string;
  view_type: string;
  action_id: number;
  view_id: number;
  role_key: string;
  current_contract_id: number;
  current_version: number;
  current_payload_hash: string;
  draft_payload?: Record<string, unknown>;
  diff_summary: Record<string, unknown>;
  reversible: boolean;
  risk_level: 'low' | 'medium' | 'high';
  validation_result: { ok?: boolean; errors?: string[] };
  publish_result: Record<string, unknown>;
}

export interface BusinessConfigChangeSet {
  id: number;
  token: string;
  state: BusinessConfigChangeSetState;
  name: string;
  user_id: number;
  company_id: number;
  role_key: string;
  database_name: string;
  expires_at: string;
  published_at: string;
  failure_message: string;
  item_count: number;
  items: BusinessConfigChangeSetItem[];
  publish_result: Record<string, unknown>;
  preview?: {
    token: string;
    expires_at: string;
    creator_only: boolean;
    company_id: number;
    role_key: string;
    device: 'desktop' | 'tablet' | 'mobile';
    formal_contract_write_count: number;
    formal_version_write_count: number;
    formal_config_mutation_count: number;
    mutation_trace_id: string;
    items: BusinessConfigChangeSetItem[];
  };
}

export interface StageBusinessConfigChangeSetItemParams {
  change_set_token: string;
  config_type: BusinessConfigChangeSetItem['config_type'];
  target_key: string;
  model: string;
  view_type?: string;
  action_id?: number;
  view_id?: number;
  role_key?: string;
  current_contract_id?: number;
  current_payload_hash?: string;
  draft_payload: Record<string, unknown>;
  diff_summary: Record<string, unknown>;
  risk_level?: BusinessConfigChangeSetItem['risk_level'];
}

export function openBusinessConfigChangeSet(params: { role_key?: string; name?: string } = {}) {
  return intentRequest<BusinessConfigChangeSet>({ intent: BUSINESS_CONFIG_INTENTS.changeSetOpen, params });
}

export function loadBusinessConfigChangeSet(params: { change_set_token: string; role_key?: string }) {
  return intentRequest<BusinessConfigChangeSet>({ intent: BUSINESS_CONFIG_INTENTS.changeSetGet, params });
}

export function stageBusinessConfigChangeSetItem(params: StageBusinessConfigChangeSetItemParams) {
  return intentRequest<BusinessConfigChangeSet>({ intent: BUSINESS_CONFIG_INTENTS.changeSetStage, params });
}

export function validateBusinessConfigChangeSet(params: { change_set_token: string; role_key?: string }) {
  return intentRequest<BusinessConfigChangeSet>({ intent: BUSINESS_CONFIG_INTENTS.changeSetValidate, params });
}

export function previewBusinessConfigChangeSet(params: { change_set_token: string; role_key?: string; device?: string }) {
  return intentRequest<BusinessConfigChangeSet>({ intent: BUSINESS_CONFIG_INTENTS.changeSetPreview, params });
}

export function publishBusinessConfigChangeSet(params: { change_set_token: string; role_key?: string; request_id: string }) {
  return intentRequest<BusinessConfigChangeSet>({ intent: BUSINESS_CONFIG_INTENTS.changeSetPublish, params });
}

export function rollbackBusinessConfigChangeSet(params: { change_set_token: string; role_key?: string; request_id: string }) {
  return intentRequest<BusinessConfigChangeSet>({ intent: BUSINESS_CONFIG_INTENTS.changeSetRollback, params });
}

export function discardBusinessConfigChangeSet(params: { change_set_token: string; role_key?: string }) {
  return intentRequest<BusinessConfigChangeSet>({ intent: BUSINESS_CONFIG_INTENTS.changeSetDiscard, params });
}

export interface BusinessConfigListSearchAuditPayload {
  model: string;
  action_id: number;
  view_id: number;
  role_key: string;
  business_config_list_contracts: Array<{
    id: number;
    name: string;
    version_no: number;
    columns: string[];
  }>;
  business_config_search_contracts: Array<{
    id: number;
    name: string;
    version_no: number;
    filters: string[];
    group_by: string[];
  }>;
  business_config_list_columns: string[];
  business_config_list_column_labels?: Record<string, string>;
  business_config_search_filters: string[];
  business_config_search_group_by: string[];
  suggested_list_columns?: string[];
  suggested_search_filters?: string[];
  suggested_search_group_by?: string[];
  available_model_fields?: Array<{
    name: string;
    label: string;
    type: string;
  }>;
  user_preference_count: number;
  user_preferences: Array<{
    id: number;
    user_id: number;
    user_name: string;
    scope_key: string;
    action_id: number;
    model: string;
    view_type: string;
    preference_key: string;
    column_count: number;
  }>;
  user_preference_boundary: 'ui_only' | string;
  has_business_list_config: boolean;
  has_business_search_config: boolean;
}

export interface BusinessConfigAnalysisAuditPayload {
  model: string;
  action_id: number;
  view_id: number;
  role_key: string;
  business_config_analysis_contracts: Array<{
    id: number;
    name: string;
    view_type: 'pivot' | 'graph' | string;
    version_no: number;
    measures: string[];
    dimensions: string[];
    type?: string;
  }>;
  pivot_measures: string[];
  pivot_dimensions: string[];
  graph_measures: string[];
  graph_dimensions: string[];
  graph_type: string;
  suggested_pivot_measures?: string[];
  suggested_pivot_dimensions?: string[];
  suggested_graph_measures?: string[];
  suggested_graph_dimensions?: string[];
  suggested_graph_type?: string;
  available_model_fields?: Array<{
    name: string;
    label: string;
    type: string;
  }>;
  business_config_boundary: 'business_contract' | string;
  user_preference_boundary: 'not_a_source' | string;
  has_business_pivot_config: boolean;
  has_business_graph_config: boolean;
  has_business_analysis_config: boolean;
}

export interface BusinessConfigListSearchSetPayload {
  model: string;
  action_id: number;
  view_id: number;
  role_key: string;
  saved_count: number;
  saved: Array<{
    id: number;
    name: string;
    view_type: 'tree' | 'search' | string;
    status: string;
    version_no: number;
    columns?: string[];
    filters?: string[];
    group_by?: string[];
    contract_reload?: Record<string, unknown>;
  }>;
}

export interface BusinessConfigAnalysisSetPayload {
  model: string;
  action_id: number;
  view_id: number;
  role_key: string;
  saved_count: number;
  saved: Array<{
    id: number;
    name: string;
    view_type: 'pivot' | 'graph' | string;
    status: string;
    version_no: number;
    measures?: string[];
    dimensions?: string[];
    type?: string;
    contract_reload?: Record<string, unknown>;
  }>;
  business_config_boundary: 'business_contract' | string;
  user_preference_boundary: 'not_a_source' | string;
}

export interface ApprovalPolicyConfigPayload {
  model: string;
  policy: {
    id: number;
    name: string;
    target_model: string;
    target_model_label: string;
    approval_required: boolean;
    mode: string;
    trigger: string;
    runtime_state: string;
    manager_scope_key: string;
    step_count: number;
    steps: Array<{
      id: number;
      name: string;
      approval_scope_key: string;
      approval_scope_label: string;
      sequence: number;
      active: boolean;
      amount_min: number | false;
      amount_max: number | false;
      condition_note: string;
      note: string;
    }>;
    active: boolean;
    exists: boolean;
  };
  runtime_approval_required: boolean;
  mode_options: Array<{ value: string; label: string }>;
  trigger_options: Array<{ value: string; label: string }>;
  scope_options: Array<{ value: string; label: string }>;
  boundary: string;
}

export interface BusinessConfigListSearchBootstrapPayload extends BusinessConfigListSearchSetPayload {
  bootstrapped_from: string;
  personal_preference_boundary: string;
  list_columns: string[];
  search_filters: string[];
  search_group_by: string[];
}

export interface BusinessConfigAnalysisBootstrapPayload extends BusinessConfigAnalysisSetPayload {
  bootstrapped_from: string;
  personal_preference_boundary: string;
  pivot_measures: string[];
  pivot_dimensions: string[];
  graph_measures: string[];
  graph_dimensions: string[];
  graph_type: string;
}

export interface BusinessConfigFormBootstrapPayload {
  id: number;
  name: string;
  model: string;
  status: string;
  version_no: number;
  bootstrapped_from: string;
  personal_preference_boundary: string;
  form_fields: string[];
  field_count: number;
  contract_reload?: Record<string, unknown>;
}

export interface BusinessConfigSurfacePayload {
  model: string;
  action_id: number;
  view_id: number;
  role_key: string;
  snapshot_summary?: BusinessConfigSnapshotSummaryPayload;
  delivery_readiness?: BusinessConfigDeliveryReadinessPayload;
  sections: Array<{
    key: 'form' | 'list_search' | 'menu' | string;
    label: string;
    contract_count: number;
    intent: string;
    boundary: string;
    route?: {
      path?: string;
      query?: Record<string, string>;
    };
  }>;
}

export interface BusinessConfigDeliveryReadinessPayload {
  schema_version: 'low_code_delivery_readiness.v1' | string;
  overall_status: 'ready' | 'attention' | string;
  ready_count: number;
  total_count: number;
  blocker_count: number;
  items: Array<{
    id: string;
    label: string;
    section_key: string;
    status: 'ready' | 'pending' | string;
    contract_count: number;
    boundary: string;
    action: string;
  }>;
}

export interface BusinessConfigSnapshotSummaryPayload {
  database: string;
  contract_count: number;
  status_counts: Record<string, number>;
  view_type_counts: Record<string, number>;
  role_scope_count: number;
  action_scope_count: number;
}

export interface BusinessConfigSnapshotComparePayload {
  current_database: string;
  baseline_database: string;
  current_contract_count: number;
  baseline_contract_count: number;
  added_count: number;
  removed_count: number;
  changed_count: number;
  added: BusinessConfigSnapshotContractRow[];
  removed: BusinessConfigSnapshotContractRow[];
  changed: Array<{
    key: string;
    name: string;
    model: string;
    view_type: string;
    previous_status: string;
    current_status: string;
    previous_version_no: number;
    current_version_no: number;
  }>;
}

export interface BusinessConfigSnapshotContractRow {
  id?: number;
  name: string;
  model: string;
  view_type: string;
  action_id: number;
  view_id: number;
  role_key: string;
  status: string;
  version_no: number;
  payload_hash?: string;
}

export interface BusinessConfigContractVersionsPayload {
  model: string;
  contract_count: number;
  version_count: number;
  contracts: Array<{
    id: number;
    name: string;
    model: string;
    view_type: string;
    action_id: number;
    view_id: number;
    role_key: string;
    status: string;
    version_no: number;
    summary: BusinessConfigContractVersionSummary;
    versions: Array<{
      id: number;
      version_no: number;
      status: string;
      created_by: string;
      summary: BusinessConfigContractVersionSummary;
    }>;
  }>;
}

export interface BusinessConfigContractRollbackPayload {
  id: number;
  name: string;
  model: string;
  status: string;
  version_no: number;
  rolled_back_to_version: number;
  contract_reload?: Record<string, unknown>;
}

export interface BusinessConfigContractVersionSummary {
  view_types: string[];
  form_field_count: number;
  list_column_count: number;
  search_filter_count: number;
  search_group_by_count: number;
  analysis_item_count: number;
  form_fields: string[];
  form_field_labels: string[];
  list_columns: string[];
  search_filters: string[];
  search_group_by: string[];
  analysis_items: string[];
}

export interface BusinessConfigCoverageScanPayload {
  model: string;
  view_id: number;
  role_key: string;
  limit: number;
  include_unreachable_actions: boolean;
  include_all_root_menu_actions: boolean;
  root_menu_xmlid: string;
  runtime_evidence_source: string;
  summary: {
    action_count: number;
    complete_count: number;
    missing_count: number;
    runtime_complete_count: number;
    runtime_missing_count: number;
    missing_form_count: number;
    missing_list_count: number;
    missing_search_count: number;
    missing_analysis_count?: number;
    runtime_missing_form_count: number;
    runtime_missing_list_count: number;
    runtime_missing_search_count: number;
    runtime_missing_analysis_count?: number;
    not_published_gap_count: number;
    not_runtime_applicable_gap_count: number;
    no_menu_count: number;
    user_preference_count: number;
    remediation_action_counts: Record<string, number>;
    severity_counts: Record<string, number>;
    overall_status: 'blocked' | 'warning' | 'notice' | 'pass' | string;
  };
  items: BusinessConfigCoverageScanItem[];
}

export interface BusinessConfigCoverageBootstrapListSearchPayload {
  model: string;
  view_id: number;
  role_key: string;
  limit: number;
  batch_limit: number;
  candidate_count: number;
  saved_count: number;
  failed_count: number;
  skipped_count: number;
  personal_preference_boundary: string;
  source_scan_summary: BusinessConfigCoverageScanPayload['summary'];
  results: Array<{
    ok: boolean;
    action_id: number;
    name: string;
    model: string;
    view_types: string[];
    saved_count: number;
    skipped?: boolean;
    error?: Record<string, unknown>;
  }>;
}

export type BusinessConfigCoverageBootstrapMissingPayload = BusinessConfigCoverageBootstrapListSearchPayload;

export interface BusinessConfigCoverageScanItem {
  action_id: number;
  name: string;
  model: string;
  view_id: number;
  view_mode: string;
  severity: 'error' | 'warning' | 'notice' | 'ok' | string;
  sort_priority: number;
  target_view_types: string[];
  menu_count: number;
  menu_ids: number[];
  has_menu: boolean;
  runtime_route: {
    path?: string;
    query?: Record<string, string>;
  };
  user_preference_count: number;
  user_preference_boundary: 'ui_only' | string;
  coverage: Record<string, number>;
  published_coverage: Record<string, number>;
  runtime_coverage: Record<string, number>;
  runtime_evidence: Record<string, {
    source: string;
    configured_count: number;
    published_count: number;
    runtime_count: number;
  }>;
  runtime_gap_reasons: Record<string, string>;
  remediation_actions: BusinessConfigRemediationAction[];
  missing_view_types: string[];
  runtime_missing_view_types: string[];
  is_complete: boolean;
  is_runtime_complete: boolean;
}

export interface BusinessConfigRemediationAction {
  code: string;
  label: string;
  target: string;
  priority: number;
}

export async function auditBusinessListSearchConfig(params: {
  model: string;
  action_id?: number;
  view_id?: number;
  role_key?: string;
}) {
  return intentRequest<BusinessConfigListSearchAuditPayload>({
    intent: BUSINESS_CONFIG_INTENTS.listSearchAudit,
    params,
  });
}

export async function auditBusinessAnalysisConfig(params: {
  model: string;
  action_id?: number;
  view_id?: number;
  role_key?: string;
}) {
  return intentRequest<BusinessConfigAnalysisAuditPayload>({
    intent: BUSINESS_CONFIG_INTENTS.analysisAudit,
    params,
  });
}

export async function loadApprovalPolicyConfig(params: {
  model: string;
}) {
  return intentRequest<ApprovalPolicyConfigPayload>({
    intent: APPROVAL_POLICY_INTENTS.configGet,
    params,
  });
}

export async function saveApprovalPolicyConfig(params: {
  model: string;
  approval_required: boolean;
  mode?: string;
  trigger?: string;
  manager_scope_key?: string;
}) {
  return intentRequest<ApprovalPolicyConfigPayload>({
    intent: APPROVAL_POLICY_INTENTS.configSet,
    params,
  });
}

export async function saveApprovalPolicySteps(params: {
  model: string;
  steps: Array<{
    id?: number;
    name: string;
    approval_scope_key: string;
    active?: boolean;
    amount_min?: number | string | false;
    amount_max?: number | string | false;
    condition_note?: string;
    note?: string;
  }>;
}) {
  return intentRequest<ApprovalPolicyConfigPayload>({
    intent: APPROVAL_POLICY_INTENTS.stepsSet,
    params,
  });
}

export async function saveBusinessListSearchConfig(params: {
  model: string;
  action_id?: number;
  view_id?: number;
  role_key?: string;
  list_columns?: string[];
  search_filters?: string[];
  search_group_by?: string[];
  publish?: boolean;
}) {
  return intentRequest<BusinessConfigListSearchSetPayload>({
    intent: BUSINESS_CONFIG_INTENTS.listSearchSet,
    params,
  });
}

export async function saveBusinessAnalysisConfig(params: {
  model: string;
  action_id?: number;
  view_id?: number;
  role_key?: string;
  pivot_measures?: string[];
  pivot_dimensions?: string[];
  graph_measures?: string[];
  graph_dimensions?: string[];
  graph_type?: string;
  publish?: boolean;
}) {
  return intentRequest<BusinessConfigAnalysisSetPayload>({
    intent: BUSINESS_CONFIG_INTENTS.analysisSet,
    params,
  });
}

export async function bootstrapBusinessListSearchConfig(params: {
  model: string;
  action_id?: number;
  view_id?: number;
  role_key?: string;
  view_types?: string[];
  publish?: boolean;
}) {
  return intentRequest<BusinessConfigListSearchBootstrapPayload>({
    intent: BUSINESS_CONFIG_INTENTS.listSearchBootstrap,
    params,
  });
}

export async function bootstrapBusinessAnalysisConfig(params: {
  model: string;
  action_id?: number;
  view_id?: number;
  role_key?: string;
  view_types?: string[];
  publish?: boolean;
}) {
  return intentRequest<BusinessConfigAnalysisBootstrapPayload>({
    intent: BUSINESS_CONFIG_INTENTS.analysisBootstrap,
    params,
  });
}

export async function bootstrapBusinessFormConfig(params: {
  model: string;
  action_id?: number;
  view_id?: number;
  role_key?: string;
  publish?: boolean;
}) {
  return intentRequest<BusinessConfigFormBootstrapPayload>({
    intent: BUSINESS_CONFIG_INTENTS.formBootstrap,
    params,
  });
}

export async function loadBusinessConfigSurface(params: {
  model?: string;
  action_id?: number;
  view_id?: number;
  role_key?: string;
} = {}) {
  return intentRequest<BusinessConfigSurfacePayload>({
    intent: BUSINESS_CONFIG_INTENTS.surfaceGet,
    params,
  });
}

export async function compareBusinessConfigSnapshot(params: {
  snapshot: Record<string, unknown>;
}) {
  return intentRequest<BusinessConfigSnapshotComparePayload>({
    intent: BUSINESS_CONFIG_INTENTS.snapshotCompare,
    params,
  });
}

export async function exportBusinessConfigSnapshot() {
  return intentRequest<Record<string, unknown>>({
    intent: BUSINESS_CONFIG_INTENTS.snapshotExport,
    params: {},
  });
}

export async function loadBusinessConfigContractVersions(params: {
  name?: string;
  model?: string;
  view_type?: string;
  action_id?: number;
  view_id?: number;
  role_key?: string;
  status?: string;
} = {}) {
  return intentRequest<BusinessConfigContractVersionsPayload>({
    intent: BUSINESS_CONFIG_INTENTS.contractVersions,
    params,
  });
}

export async function rollbackBusinessConfigContract(params: {
  name?: string;
  model?: string;
  view_type?: string;
  action_id?: number;
  view_id?: number;
  role_key?: string;
  version_no?: number;
}) {
  return intentRequest<BusinessConfigContractRollbackPayload>({
    intent: BUSINESS_CONFIG_INTENTS.contractRollback,
    params,
  });
}

export async function scanBusinessConfigCoverage(params: {
  model?: string;
  view_id?: number;
  role_key?: string;
  limit?: number;
  include_unreachable_actions?: boolean;
  include_all_root_menu_actions?: boolean;
  root_menu_xmlid?: string;
} = {}) {
  return intentRequest<BusinessConfigCoverageScanPayload>({
    intent: BUSINESS_CONFIG_INTENTS.coverageScan,
    params,
  });
}

export async function bootstrapCoverageListSearchConfig(params: {
  model?: string;
  view_id?: number;
  role_key?: string;
  limit?: number;
  batch_limit?: number;
  include_unreachable_actions?: boolean;
  include_all_root_menu_actions?: boolean;
  root_menu_xmlid?: string;
} = {}) {
  return intentRequest<BusinessConfigCoverageBootstrapListSearchPayload>({
    intent: BUSINESS_CONFIG_INTENTS.coverageBootstrapListSearch,
    params,
  });
}

export async function bootstrapCoverageMissingConfig(params: {
  model?: string;
  view_id?: number;
  role_key?: string;
  limit?: number;
  batch_limit?: number;
  include_unreachable_actions?: boolean;
  include_all_root_menu_actions?: boolean;
  root_menu_xmlid?: string;
} = {}) {
  return intentRequest<BusinessConfigCoverageBootstrapMissingPayload>({
    intent: BUSINESS_CONFIG_INTENTS.coverageBootstrapMissing,
    params,
  });
}
