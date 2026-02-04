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
  token: string;
  token_type?: string;
  expires_at?: number;
  user: {
    id: number;
    name: string;
    login: string;
    lang?: string;
    tz?: string;
    company_id?: number | null;
    allowed_company_ids?: number[];
    groups?: string[];
  };
  system?: {
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
  module?: string;
  web_icon?: boolean | string;
  groups?: number[];
  action?: any;
  icon?: string | null;
  meta?: NavMeta;
  children?: NavNode[];
}

export interface NavMeta {
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
}

export interface ApiDataListResult {
  records: Array<Record<string, unknown>>;
  next_offset?: number;
  total?: number;
}

export interface ApiDataListRequest {
  op: 'list';
  model: string;
  fields?: string[] | '*';
  domain?: unknown[] | string;
  limit?: number;
  offset?: number;
  order?: string;
  context?: Record<string, unknown>;
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
  res_model?: string;
  res_id?: number;
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

export interface LoadViewRequest {
  model: string;
  view_type: string;
  view_id?: number;
}

export interface ActionContract {
  model?: string;
  view_type?: string;
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
