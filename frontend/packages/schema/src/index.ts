export interface IntentEnvelope<T> {
  ok?: boolean;
  data?: T;
  meta?: Record<string, unknown>;
  status?: string;
  code?: number;
}

export interface IntentRequest<T = Record<string, unknown>> {
  intent: string;
  params?: T;
  context?: Record<string, unknown>;
  meta?: Record<string, unknown>;
}

export interface IntentResponse<T> {
  ok?: boolean;
  data?: T;
  meta?: Record<string, unknown>;
  status?: string;
  code?: number;
}

export interface LoginResponse {
  token?: string;
  token_type?: string;
  expires_at?: number;
  session?: {
    token?: string;
    token_type?: string;
    expires_at?: number;
  };
  user: {
    id: number;
    name: string;
    login: string;
    lang?: string;
    tz?: string;
    company_id?: number | null;
    allowed_company_ids?: number[];
  };
  entitlement?: {
    role_code?: string;
    is_internal_user?: boolean;
    can_switch_company?: boolean;
  };
  bootstrap?: {
    next_intent?: string;
    mode?: string;
  };
  contract?: {
    response_mode?: string;
    mode?: string;
  };
  debug?: {
    groups?: string[];
    intents?: Array<{ name: string; description?: string }>;
  };
}

export interface NavNode {
  key: string;
  label?: string;  // 改为可选，因为 Odoo 返回的是 name
  name?: string;   // Odoo 返回的 name 字段
  title?: string;  // Odoo 返回的 title 字段
  menu_id?: number;
  id?: number;     // Odoo 返回的 id 字段
  sequence?: number;
  parent_id?: number;
  xml_id?: string;
  xmlid?: string;
  module?: string;
  web_icon?: boolean | string;
  groups?: number[];
  action?: any;
  icon?: string | null;
  meta?: NavMeta;
  children?: NavNode[];
}

export interface NavMeta {
  name?: string;
  scene_key?: string;
  menu_id?: number;
  menu_xmlid?: string;
  sequence?: number;
  action_id?: number;
  action_type?: string;
  action_xmlid?: string;
  model?: string;
  view_modes?: string[];
  views?: Array<[number, string]>;
  domain?: unknown[] | string;
  context?: Record<string, unknown> | string;
  groups_xmlids?: string[];
}

export interface AppInitResponse {
  capabilities?: Array<string | {
    key?: string;
    label?: string;
    state?: string;
    capability_state?: string;
    reason?: string;
    reason_code?: string;
    group_key?: string;
    group_label?: string;
  }>;
  capability_groups?: Array<{
    key?: string;
    label?: string;
    icon?: string;
    sequence?: number;
    capability_count?: number;
    state_counts?: Record<string, number>;
    capability_state_counts?: Record<string, number>;
    capabilities?: Array<Record<string, unknown>>;
  }>;
  ext_facts?: {
    product?: {
      license?: {
        level?: string;
        tiers?: string[];
      };
      bundle?: {
        name?: string;
        scenes?: string[];
        capabilities?: string[];
        recommended_roles?: string[];
        default_dashboard?: string;
      };
    };
    [key: string]: unknown;
  };
  role_surface?: {
    role_code?: string;
    role_label?: string;
    landing_scene_key?: string;
    landing_menu_id?: number | null;
    landing_menu_xmlid?: string;
    landing_path?: string;
    scene_candidates?: string[];
    menu_xmlids?: string[];
  };
  role_surface_map?: Record<string, {
    role_code?: string;
    role_label?: string;
    scene_candidates?: string[];
    menu_xmlids?: string[];
  }>;
  user: {
    id: number;
    name: string;
    groups_xmlids?: string[];
    lang?: string;
    tz?: string;
    company_id?: number | null;
  };
  nav: NavNode[];
  default_route?: { menu_id?: number } | string;
  intents?: string[];
  feature_flags?: Record<string, unknown>;
  meta?: Record<string, unknown>;
}

export interface ApiDataListResult {
  records: Array<Record<string, unknown>>;
  next_offset?: number;
  total?: number;
  group_summary?: Array<{
    group_key?: string;
    field?: string;
    value?: unknown;
    label?: string;
    count?: number;
    domain?: unknown[];
  }>;
  group_paging?: {
    group_by_field?: string | null;
    group_limit?: number;
    group_offset?: number;
    group_count?: number;
    group_total?: number;
    has_more?: boolean;
    next_group_offset?: number;
    prev_group_offset?: number;
    window_start?: number;
    window_end?: number;
    window_id?: string;
    query_fingerprint?: string;
    window_digest?: string;
    window_key?: string;
    window_identity?: {
      model?: string;
      group_by_field?: string | null;
      window_id?: string;
      query_fingerprint?: string;
      window_digest?: string;
      version?: string;
      algo?: string;
      key?: string;
      window_empty?: boolean;
      window_start?: number;
      window_end?: number;
      window_span?: number;
      prev_group_offset?: number;
      next_group_offset?: number;
      has_more?: boolean;
      group_offset?: number;
      group_limit?: number;
      group_count?: number;
      group_total?: number;
      page_size?: number;
      has_group_page_offsets?: boolean;
    };
    page_size?: number;
    has_group_page_offsets?: boolean;
  };
  grouped_rows?: Array<{
    group_key?: string;
    field?: string;
    value?: unknown;
    label?: string;
    count?: number;
    domain?: unknown[];
    sample_rows?: Array<Record<string, unknown>>;
    page_requested_size?: number;
    page_applied_size?: number;
    page_requested_offset?: number;
    page_applied_offset?: number;
    page_max_offset?: number;
    page_clamped?: boolean;
    page_offset?: number;
    page_limit?: number;
    page_size?: number;
    page_current?: number;
    page_total?: number;
    page_range_start?: number;
    page_range_end?: number;
    page_window?: {
      start?: number;
      end?: number;
    };
    page_has_prev?: boolean;
    page_has_next?: boolean;
  }>;
}

export interface ApiDataListRequest {
  op: 'list';
  model: string;
  fields?: string[] | '*';
  domain?: unknown[] | string;
  domain_raw?: string;
  need_total?: boolean;
  group_by?: string | string[];
  group_offset?: number;
  need_group_total?: boolean;
  group_sample_limit?: number;
  group_limit?: number;
  group_page_size?: number;
  group_page_offsets?: Record<string, number>;
  search_term?: string;
  limit?: number;
  offset?: number;
  order?: string;
  context?: Record<string, unknown>;
  context_raw?: string;
}

export interface ApiDataReadResult {
  records: Array<Record<string, unknown>>;
}

export interface ApiDataReadRequest {
  op: 'read';
  model: string;
  ids: number[];
  fields?: string[] | '*';
  context?: Record<string, unknown>;
}

export interface ApiDataCreateRequest {
  op: 'create';
  model: string;
  vals: Record<string, unknown>;
  context?: Record<string, unknown>;
}

export interface ApiDataWriteRequest {
  op: 'write';
  model: string;
  ids: number[];
  vals: Record<string, unknown>;
  context?: Record<string, unknown>;
}

export interface ExecuteButtonRequest {
  model: string;
  res_id: number;
  button: {
    name: string;
    type?: string;
  };
  context?: Record<string, unknown>;
  meta?: Record<string, unknown>;
}

export interface ExecuteButtonResult {
  type: 'refresh' | 'action' | 'noop' | 'dry_run';
  status?: 'success' | 'failure' | string;
  success?: boolean;
  reason_code?: string;
  res_model?: string;
  res_id?: number;
  action_id?: number;
  raw_action?: Record<string, unknown>;
  message?: string;
}

export interface ButtonEffectTarget {
  kind: 'record' | 'action' | 'url';
  model?: string;
  id?: number;
  action_id?: number;
  url?: string;
}

export interface ButtonEffect {
  type: 'reload_record' | 'reload_action' | 'navigate' | 'toast';
  target?: ButtonEffectTarget;
  message?: string;
}

export interface ExecuteButtonResponse {
  result: ExecuteButtonResult;
  effect?: ButtonEffect;
}

export interface FileUploadRequest {
  model: string;
  res_id: number;
  name: string;
  mimetype: string;
  data: string;
}

export interface FileUploadResponse {
  id: number;
  name: string;
  model: string;
  res_id: number;
}

export interface FileDownloadRequest {
  id: number;
}

export interface FileDownloadResponse {
  id: number;
  name: string;
  mimetype: string;
  datas: string;
  res_model: string;
  res_id: number;
}

export interface LoadViewRequest {
  model: string;
  view_type: string;
  view_id?: number;
}

export interface ActionContract {
  contract_surface?: 'user' | 'native' | 'hud';
  render_mode?: 'governed' | 'native' | string;
  source_mode?: string;
  governed_from_native?: boolean;
  surface_mapping?: Record<string, unknown>;
  visible_fields?: string[];
  render_profile?: 'create' | 'edit' | 'readonly';
  hide_filters_on_create?: boolean;
  field_groups?: Array<{
    name?: string;
    label?: string;
    priority?: number;
    collapsible?: boolean;
    collapsed_by_default?: boolean;
    fields?: string[];
  }>;
  field_policies?: Record<
    string,
    {
      visible_profiles?: string[];
      required_profiles?: string[];
      readonly_profiles?: string[];
      source_required?: boolean;
      source_readonly?: boolean;
      group?: string;
    }
  >;
  action_policies?: Record<
    string,
    {
      visible_profiles?: string[];
      enabled_when?: {
        profiles?: string[];
        required_fields?: string[];
        required_capabilities?: string[];
        required_groups?: string[];
        required_roles?: string[];
        conditions?: Array<{
          source?: string;
          field?: string;
          op?: string;
          value?: unknown;
        }>;
        condition_expr?: {
          op?: string;
          source?: string;
          field?: string;
          value?: unknown;
          items?: Array<Record<string, unknown>>;
          item?: Record<string, unknown>;
        };
        lifecycle?: {
          field?: string;
          disallow_states?: string[];
        };
      };
      disabled_reason?: string;
      semantic?: string;
    }
  >;
  validation_rules?: Array<Record<string, unknown>>;
  meta?: Record<string, unknown>;
  head?: {
    title?: string;
    model?: string;
    view_type?: string;
    action_id?: number;
    context?: Record<string, unknown> | null;
    permissions?: {
      read?: boolean;
      write?: boolean;
      create?: boolean;
      unlink?: boolean;
    };
    res_id?: number | string;
  };
  model?: string;
  view_type?: string;
  fields?: Record<string, FieldDescriptor>;
  views?: Record<
    string,
    {
      model?: string;
      view_type?: string;
      layout?: Array<{ type?: string; name?: string }>;
      fields?: string[];
      order?: string;
      chatter?: unknown;
    }
  >;
  toolbar?: {
    header?: Array<Record<string, unknown>>;
    sidebar?: Array<Record<string, unknown>>;
    footer?: Array<Record<string, unknown>>;
  };
  buttons?: Array<Record<string, unknown>>;
  action_groups?: Array<{
    key?: string;
    label?: string;
    actions?: Array<Record<string, unknown>>;
    overflow_actions?: Array<Record<string, unknown>>;
    overflow_count?: number;
  }>;
  permissions?: {
    rules?: Record<string, { mode?: string; clauses?: Array<Record<string, unknown>> }>;
    perms_by_group?: Record<string, { read?: boolean; write?: boolean; create?: boolean; unlink?: boolean }>;
    effective?: {
      rights?: {
        read?: boolean;
        write?: boolean;
        create?: boolean;
        unlink?: boolean;
      };
    };
    field_groups?: Record<string, { groups_xmlids?: string[] }>;
    order_default?: string;
    domain_default?: unknown[];
  };
  search?: {
    filters?: Array<{
      key?: string;
      label?: string;
      domain?: unknown[];
      domain_raw?: string | null;
      context_raw?: string | null;
    }>;
    defaults?: {
      limit?: number;
      order?: string;
    };
    group_by?: Array<{
      field?: string;
      label?: string;
      type?: string;
      default?: boolean;
    }>;
    saved_filters?: Array<Record<string, unknown>>;
  };
  workflow?: {
    states?: Array<Record<string, unknown>>;
    activities?: Array<Record<string, unknown>>;
    transitions?: Array<{
      trigger?: { label?: string; name?: string; kind?: string };
      notes?: string;
    }>;
  };
  reports?: Array<Record<string, unknown>>;
  validator?: Record<string, unknown>;
  warnings?: Array<string | Record<string, unknown>>;
  degraded?: boolean;
  access_policy?: {
    mode?: 'allow' | 'degrade' | 'block' | string;
    reason_code?: string;
    message?: string;
    policy_source?: string;
    blocked_fields?: Array<{
      field?: string;
      model?: string;
      reason_code?: string;
    }>;
    degraded_fields?: Array<{
      field?: string;
      model?: string;
      reason_code?: string;
    }>;
  };
  missing_models?: string[];
  ui_contract_raw?: {
    fields?: Record<string, FieldDescriptor>;
  };
  ui_contract?: {
    columns?: string[];
    columnsSchema?: Array<{ name: string; string?: string }>;
  };
}

export interface ViewContract {
  model: string;
  view_type: string;
  view_id?: number;
  fields: Record<string, FieldDescriptor>;
  layout: FormLayout;
}

export interface ViewButton {
  name?: string;
  string?: string;
  type?: string;
  class?: string;
  context?: Record<string, unknown>;
  invisible?: unknown;
  icon?: string;
  groups?: string[];
  hotkey?: string;
  visible?: boolean;
  level?: string;
  field?: string;
}

export interface FieldDescriptor {
  name?: string;
  string?: string;
  type?: string;
  ttype?: string;
  required?: boolean;
  readonly?: boolean;
  selection?: Array<[string, string]>;
  relation?: string;
  relation_field?: string;
  editable?: boolean;
}

export interface FormLayout {
  titleField?: string | null;
  headerButtons?: ViewButton[];
  statButtons?: ViewButton[];
  ribbon?: unknown;
  groups?: Array<FormGroup>;
  notebooks?: Array<FormNotebook>;
  chatter?: Record<string, unknown>;
}

export interface FormGroup {
  fields: Array<FormField>;
  sub_groups?: Array<FormGroup>;
}

export interface FormNotebook {
  pages: Array<FormPage>;
}

export interface FormPage {
  title?: string | null;
  groups?: Array<FormGroup>;
}

export interface FormField {
  name?: string;
  string?: string;
  widget?: string;
  invisible?: unknown;
  required?: unknown;
  readonly?: unknown;
}
