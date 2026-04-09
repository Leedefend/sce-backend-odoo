export type ExplainedTargetType = 'directory' | 'scene' | 'action' | 'native' | 'url' | 'unavailable';

export type ExplainedDeliveryMode = 'custom_scene' | 'custom_action' | 'native_bridge' | 'external_url' | 'none';

export interface ExplainedActiveMatch {
  menu_id?: number | null;
  scene_key?: string | null;
  action_id?: number | null;
  route_prefix?: string | null;
}

export interface ExplainedMenuNode {
  menu_id?: number;
  key: string;
  name: string;
  icon?: string | null;
  is_visible?: boolean;
  is_clickable?: boolean;
  target_type: ExplainedTargetType;
  delivery_mode: ExplainedDeliveryMode;
  route?: string | null;
  target?: Record<string, unknown>;
  active_match?: ExplainedActiveMatch;
  availability_status?: string;
  reason_code?: string;
  children?: ExplainedMenuNode[];
}

export interface NavigationExplainedPayload {
  nav_fact?: {
    flat?: Array<Record<string, unknown>>;
    tree?: Array<Record<string, unknown>>;
  };
  nav_explained?: {
    flat?: ExplainedMenuNode[];
    tree?: ExplainedMenuNode[];
  };
  meta?: Record<string, unknown>;
}
