export type SuggestedActionKind =
  | 'refresh'
  | 'retry'
  | 'go_back'
  | 'open_login'
  | 'relogin'
  | 'check_permission'
  | 'open_home'
  | 'open_my_work_todo'
  | 'open_my_work_done'
  | 'open_my_work_failed'
  | 'open_my_work_section'
  | 'open_my_work'
  | 'open_usage_analytics'
  | 'open_locked'
  | 'open_preview'
  | 'open_ready'
  | 'open_hidden'
  | 'open_scene_health'
  | 'open_scene_packages'
  | 'open_projects_list'
  | 'open_projects_board'
  | 'open_project'
  | 'open_dashboard'
  | 'open_record'
  | 'open_scene'
  | 'open_url'
  | 'open_route'
  | 'open_menu'
  | 'open_action'
  | 'copy_trace'
  | 'copy_reason'
  | 'copy_message'
  | 'copy_error_line'
  | 'copy_action'
  | 'copy_json_error'
  | 'copy_full_error'
  | '';

export type SuggestedActionParsed = {
  kind: SuggestedActionKind;
  raw: string;
  model?: string;
  recordId?: number;
  sceneKey?: string;
  url?: string;
  menuId?: number;
  actionId?: number;
  projectId?: number;
  query?: string;
  hash?: string;
  section?: string;
};

export type SuggestedActionCapabilityOptions = {
  hasRetryHandler?: boolean;
  hasActionHandler?: boolean;
  traceId?: string;
  reasonCode?: string;
  message?: string;
};

export type SuggestedActionExecuteOptions = {
  onRetry?: () => void;
  onSuggestedAction?: (action: string) => boolean | void;
  onExecuted?: (result: { kind: SuggestedActionKind; raw: string; success: boolean }) => void;
  traceId?: string;
  reasonCode?: string;
  message?: string;
};
