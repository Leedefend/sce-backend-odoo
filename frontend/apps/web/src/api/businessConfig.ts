import { intentRequest } from './intents';

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
  business_config_search_filters: string[];
  business_config_search_group_by: string[];
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

export interface BusinessConfigListSearchBootstrapPayload extends BusinessConfigListSearchSetPayload {
  bootstrapped_from: string;
  personal_preference_boundary: string;
  list_columns: string[];
  search_filters: string[];
  search_group_by: string[];
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
  sections: Array<{
    key: 'form' | 'list_search' | 'menu' | string;
    label: string;
    contract_count: number;
    intent: string;
    boundary: string;
  }>;
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
  form_fields: string[];
  list_columns: string[];
  search_filters: string[];
  search_group_by: string[];
}

export interface BusinessConfigCoverageScanPayload {
  model: string;
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
    runtime_missing_form_count: number;
    runtime_missing_list_count: number;
    runtime_missing_search_count: number;
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
    intent: 'ui.business_config.list_search.audit',
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
    intent: 'ui.business_config.list_search.set',
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
    intent: 'ui.business_config.list_search.bootstrap',
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
    intent: 'ui.business_config.form.bootstrap',
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
    intent: 'ui.business_config.surface.get',
    params,
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
    intent: 'ui.business_config.contract.versions',
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
    intent: 'ui.business_config.contract.rollback',
    params,
  });
}

export async function scanBusinessConfigCoverage(params: {
  model?: string;
  role_key?: string;
  limit?: number;
  include_unreachable_actions?: boolean;
  include_all_root_menu_actions?: boolean;
  root_menu_xmlid?: string;
} = {}) {
  return intentRequest<BusinessConfigCoverageScanPayload>({
    intent: 'ui.business_config.coverage.scan',
    params,
  });
}

export async function bootstrapCoverageListSearchConfig(params: {
  model?: string;
  role_key?: string;
  limit?: number;
  batch_limit?: number;
  include_unreachable_actions?: boolean;
  include_all_root_menu_actions?: boolean;
  root_menu_xmlid?: string;
} = {}) {
  return intentRequest<BusinessConfigCoverageBootstrapListSearchPayload>({
    intent: 'ui.business_config.coverage.bootstrap_list_search',
    params,
  });
}

export async function bootstrapCoverageMissingConfig(params: {
  model?: string;
  role_key?: string;
  limit?: number;
  batch_limit?: number;
  include_unreachable_actions?: boolean;
  include_all_root_menu_actions?: boolean;
  root_menu_xmlid?: string;
} = {}) {
  return intentRequest<BusinessConfigCoverageBootstrapMissingPayload>({
    intent: 'ui.business_config.coverage.bootstrap_missing',
    params,
  });
}
