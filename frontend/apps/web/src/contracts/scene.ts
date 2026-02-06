export type SceneChannel = 'stable' | 'beta' | 'dev';

export interface SceneHealthSummary {
  readonly critical_resolve_errors_count: number;
  readonly critical_drift_warn_count: number;
  readonly non_critical_debt_count: number;
}

export interface SceneDiagnosticsItem {
  readonly scene_key?: string;
  readonly code?: string;
  readonly severity?: string;
  readonly message?: string;
  readonly created_at?: string;
  readonly ts?: string;
  readonly [key: string]: unknown;
}

export interface SceneDiagnostics {
  readonly resolve_errors: readonly SceneDiagnosticsItem[];
  readonly drift: readonly SceneDiagnosticsItem[];
  readonly debt: readonly SceneDiagnosticsItem[];
}

export interface AutoDegradeInfo {
  readonly triggered?: boolean;
  readonly reason_codes?: readonly string[];
  readonly action_taken?: string;
  readonly notifications?: {
    readonly sent?: boolean;
    readonly channels?: readonly string[];
    readonly trace_id?: string;
  };
  readonly pre_counts?: {
    readonly critical_resolve_errors_count?: number;
    readonly critical_drift_warn_count?: number;
  };
}

export interface SceneHealthContract {
  readonly company_id: number | null;
  readonly scene_channel: string;
  readonly rollback_active: boolean;
  readonly scene_version: string;
  readonly schema_version: string;
  readonly contract_ref: string;
  readonly summary: SceneHealthSummary;
  readonly details?: SceneDiagnostics;
  readonly auto_degrade?: AutoDegradeInfo;
  readonly last_updated_at: string;
  readonly trace_id: string;
  readonly query?: {
    readonly mode?: 'summary' | 'full' | string;
    readonly limit?: number;
    readonly offset?: number;
    readonly since?: string;
  };
}

export interface GovernanceActionResult {
  readonly action: string;
  readonly company_id?: number;
  readonly from_channel?: string | null;
  readonly to_channel?: string | null;
  readonly trace_id: string;
}

export interface SceneHealthQuery {
  readonly company_id?: number;
  readonly mode?: 'summary' | 'full';
  readonly limit?: number;
  readonly offset?: number;
  readonly since?: string;
}
