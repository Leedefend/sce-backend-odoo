import { intentRequest } from './intents';
import { MENU_CONFIG_INTENTS } from '../app/businessConfigBoundaries';
import type { NavNode } from '@sc/schema';

export interface MenuConfigMenu {
  id: number;
  menu_id: number;
  name: string;
  display_name: string;
  complete_name: string;
  parent_id: number;
  parent_name: string;
  sequence: number;
  action: string;
  web_icon: string;
  xmlid: string;
  group_ids: number[];
  group_names: string[];
  children?: MenuConfigMenu[];
}

export interface MenuConfigPolicy {
  id: number;
  menu_id: number;
  company_id: number;
  target_parent_menu_id: number;
  custom_label: string;
  sequence_override: number;
  visible: boolean;
  active: boolean;
  role_group_ids: number[];
  note: string;
  effect_summary?: string;
  scope_summary?: string;
  preview_summary?: string;
}

export interface MenuConfigGroup {
  id: number;
  name: string;
  display_name: string;
  category: string;
}

export interface MenuConfigRuntimeState {
  menu_id: number;
  runtime_visible: boolean;
  configured_visible?: boolean | null;
  runtime_visibility_reason?: string;
  runtime_state?: string;
  runtime_path?: string;
}

export interface MenuConfigRuntimePayload {
  visible_menu_ids?: number[];
  carrier_menu_ids?: number[];
  states?: Record<string, MenuConfigRuntimeState>;
  tree?: NavNode[];
  summary?: {
    runtime_visible_count?: number;
    runtime_carrier_count?: number;
    configured_hidden_runtime_visible_count?: number;
  };
  source?: string;
  navigation_meta?: Record<string, unknown>;
  error?: string;
}

export interface MenuConfigPayload {
  company?: { id: number; name: string } | null;
  menus: MenuConfigMenu[];
  tree: MenuConfigMenu[];
  policies: Record<string, MenuConfigPolicy>;
  runtime?: MenuConfigRuntimePayload;
  groups: MenuConfigGroup[];
}

export interface MenuConfigAuditPolicy extends MenuConfigPolicy {
  menu_label: string;
  menu_complete_name: string;
  target_parent_label: string;
  role_group_names: string[];
  applicable: boolean;
  flags: {
    hidden: boolean;
    renamed: boolean;
    reordered: boolean;
    moved: boolean;
  };
}

export interface MenuConfigAuditPayload {
  company?: { id: number; name: string } | null;
  summary: {
    runtime_source?: string;
    configured_policy_count: number;
    applicable_policy_count: number;
    hidden_count: number;
    runtime_hidden_count?: number;
    runtime_visible_count?: number;
    runtime_carrier_count?: number;
    renamed_count: number;
    reordered_count: number;
    moved_count: number;
    inactive_policy_count: number;
    not_applicable_policy_ids: number[];
  };
  policies: MenuConfigAuditPolicy[];
  applicable_policies: MenuConfigAuditPolicy[];
  runtime?: MenuConfigRuntimePayload;
}

export interface MenuConfigRollbackPayload {
  company?: { id: number; name: string } | null;
  contract: {
    id: number;
    name: string;
    model: string;
    status: string;
    version_no: number;
  };
  rolled_back_to_version: number;
  restored_count: number;
  restored: MenuConfigPolicy[];
}

export interface MenuConfigVersionSummary {
  policy_count: number;
  hidden_count: number;
  renamed_count: number;
  reordered_count: number;
  moved_count: number;
  active_count: number;
}

export interface MenuConfigVersionItem {
  id: number;
  version_no: number;
  status: string;
  created_by?: { id: number; name: string } | null;
  summary: MenuConfigVersionSummary;
}

export interface MenuConfigVersionsPayload {
  company?: { id: number; name: string } | null;
  contract?: {
    id: number;
    name: string;
    model: string;
    status: string;
    version_no: number;
    summary: MenuConfigVersionSummary;
  } | null;
  versions: MenuConfigVersionItem[];
}

export interface MenuConfigSaveRow {
  policy_id?: number;
  menu_id: number;
  target_parent_menu_id?: number;
  custom_label?: string;
  sequence_override?: number;
  visible?: boolean;
  active?: boolean;
  role_group_ids?: number[];
  note?: string;
}

export interface MenuConfigSavePayload {
  saved: MenuConfigPolicy[];
  saved_count: number;
  contract?: {
    id: number;
    name: string;
    model: string;
    status: string;
    version_no: number;
  } | null;
}

export interface MenuConfigCreatePayload {
  menu: MenuConfigMenu;
  policy: MenuConfigPolicy;
  contract?: {
    id: number;
    name: string;
    model: string;
    status: string;
    version_no: number;
  } | null;
}

export interface MenuConfigDeletePayload {
  deleted: Array<{ id: number; name: string }>;
  deleted_count: number;
  deleted_menu_ids: number[];
  deactivated_policy_count: number;
  contract?: {
    id: number;
    name: string;
    model: string;
    status: string;
    version_no: number;
  } | null;
}

export async function loadMenuConfigurationPanel(params: {
  company_id?: number;
  menu_ids?: number[];
  root_menu_id?: number;
  root_menu_xmlid?: string;
} = {}) {
  return intentRequest<MenuConfigPayload>({
    intent: MENU_CONFIG_INTENTS.panelGet,
    params,
  });
}

export async function saveMenuConfigurationPanel(params: { company_id?: number; rows: MenuConfigSaveRow[] }) {
  return intentRequest<MenuConfigSavePayload>({
    intent: MENU_CONFIG_INTENTS.panelSet,
    params,
  });
}

export async function createMenuConfigurationEntry(params: {
  company_id?: number;
  name: string;
  parent_menu_id?: number;
  source_menu_id?: number;
  sequence?: number;
  visible?: boolean;
  role_group_ids?: number[];
  note?: string;
}) {
  return intentRequest<MenuConfigCreatePayload>({
    intent: MENU_CONFIG_INTENTS.menuCreate,
    params,
  });
}

export async function deleteMenuConfigurationEntry(params: {
  company_id?: number;
  menu_id: number;
  recursive?: boolean;
}) {
  return intentRequest<MenuConfigDeletePayload>({
    intent: MENU_CONFIG_INTENTS.menuDelete,
    params,
  });
}

export async function loadMenuConfigurationAudit(params: { company_id?: number; include_inactive?: boolean } = {}) {
  return intentRequest<MenuConfigAuditPayload>({
    intent: MENU_CONFIG_INTENTS.audit,
    params,
  });
}

export async function rollbackMenuConfiguration(params: { company_id?: number; version_no?: number } = {}) {
  return intentRequest<MenuConfigRollbackPayload>({
    intent: MENU_CONFIG_INTENTS.rollback,
    params,
  });
}

export async function loadMenuConfigurationVersions(params: { company_id?: number } = {}) {
  return intentRequest<MenuConfigVersionsPayload>({
    intent: MENU_CONFIG_INTENTS.versions,
    params,
  });
}
