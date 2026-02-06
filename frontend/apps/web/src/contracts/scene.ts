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

export interface ScenePackageInfo {
  readonly package_name: string;
  readonly package_version: string;
  readonly schema_version: string;
  readonly scene_version: string;
  readonly scene_count: number;
  readonly checksum: string;
  readonly imported_at: string;
  readonly strategy: 'skip_existing' | 'override_existing' | 'rename_on_conflict' | string;
}

export interface ScenePackageListResult {
  readonly items: readonly ScenePackageInfo[];
  readonly count: number;
}

export interface ScenePackageExportResult {
  readonly action: 'package_export' | string;
  readonly package_name: string;
  readonly package_version: string;
  readonly scene_channel: SceneChannel;
  readonly scene_count: number;
  readonly checksum: string;
  readonly trace_id: string;
  readonly package: Record<string, unknown>;
}

export interface ScenePackageDryRunResult {
  readonly dry_run: true;
  readonly package_name: string;
  readonly package_version: string;
  readonly checksum: string;
  readonly summary: {
    readonly scene_count: number;
    readonly additions_count: number;
    readonly conflicts_count: number;
  };
  readonly report: {
    readonly additions: readonly { readonly scene_key: string }[];
    readonly conflicts: readonly { readonly scene_key: string; readonly existing: boolean; readonly changed_fields: readonly string[] }[];
    readonly overwrite_fields: readonly string[];
  };
}

export interface ScenePackageImportResult {
  readonly action: 'package_import' | string;
  readonly package_name: string;
  readonly package_version: string;
  readonly strategy: 'skip_existing' | 'override_existing' | 'rename_on_conflict' | string;
  readonly imported_scene_keys: readonly string[];
  readonly skipped_scene_keys: readonly string[];
  readonly renamed: readonly { readonly from: string; readonly to: string }[];
  readonly trace_id: string;
  readonly summary: {
    readonly imported_count: number;
    readonly skipped_count: number;
    readonly renamed_count: number;
  };
}
