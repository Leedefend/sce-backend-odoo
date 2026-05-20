import { intentRequest } from './intents';

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

export interface MenuConfigPayload {
  company?: { id: number; name: string } | null;
  menus: MenuConfigMenu[];
  tree: MenuConfigMenu[];
  policies: Record<string, MenuConfigPolicy>;
  groups: MenuConfigGroup[];
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

export async function loadMenuConfigurationPanel(params: { company_id?: number; menu_ids?: number[] } = {}) {
  return intentRequest<MenuConfigPayload>({
    intent: 'ui.menu_config.panel.get',
    params,
  });
}

export async function saveMenuConfigurationPanel(params: { company_id?: number; rows: MenuConfigSaveRow[] }) {
  return intentRequest<{ saved: MenuConfigPolicy[]; saved_count: number }>({
    intent: 'ui.menu_config.panel.set',
    params,
  });
}
