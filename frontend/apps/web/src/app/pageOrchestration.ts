export type SemanticTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral';
export type SemanticProgress = 'overdue' | 'blocked' | 'pending' | 'running' | 'completed';

export interface PageOrchestrationAction {
  key: string;
  label?: string;
  intent?: string;
  target?: Record<string, unknown>;
}

export interface PageOrchestrationBlock {
  key: string;
  block_type: string;
  title?: string;
  subtitle?: string;
  priority?: number;
  importance?: string;
  tone?: SemanticTone | string;
  progress?: SemanticProgress | string;
  data_source?: string;
  payload?: Record<string, unknown>;
  actions?: PageOrchestrationAction[];
}

export interface PageOrchestrationZone {
  key: string;
  title?: string;
  description?: string;
  zone_type?: string;
  display_mode?: string;
  priority?: number;
  blocks?: PageOrchestrationBlock[];
}

export interface PageOrchestrationPage {
  key?: string;
  title?: string;
  subtitle?: string;
  page_type?: string;
  layout_mode?: string;
  audience?: string[];
  priority_model?: string;
  status?: string;
  header?: {
    badges?: Array<{ label?: string; tone?: SemanticTone | string }>;
  };
  global_actions?: PageOrchestrationAction[];
  context?: Record<string, unknown>;
}

export interface PageOrchestrationContract {
  schema_version?: string;
  contract_version?: string;
  scene_key?: string;
  page?: PageOrchestrationPage;
  zones?: PageOrchestrationZone[];
  data_sources?: Record<string, unknown>;
  state_schema?: Record<string, unknown>;
  action_schema?: Record<string, unknown>;
  render_hints?: Record<string, unknown>;
  meta?: Record<string, unknown>;
}

export interface PageBlockActionEvent {
  actionKey: string;
  blockKey: string;
  zoneKey: string;
  item?: Record<string, unknown>;
  intent?: string;
  target?: Record<string, unknown>;
}
