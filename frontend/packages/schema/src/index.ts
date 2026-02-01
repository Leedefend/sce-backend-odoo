export interface IntentEnvelope<T> {
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
  label: string;
  menu_id?: number;
  icon?: string | null;
  meta?: NavMeta;
  children?: NavNode[];
}

export interface NavMeta {
  menu_id?: number;
  menu_xmlid?: string;
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

export interface ApiDataReadResult {
  records: Array<Record<string, unknown>>;
}

export interface ViewContract {
  model: string;
  view_type: string;
  view_id?: number;
  fields: Record<string, FieldDescriptor>;
  layout: FormLayout;
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
}

export interface FormLayout {
  titleField?: string | null;
  headerButtons?: unknown[];
  statButtons?: unknown[];
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
