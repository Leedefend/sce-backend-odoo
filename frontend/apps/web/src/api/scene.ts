import { intentRequestRaw } from './intents';
import type {
  GovernanceActionResult,
  SceneHealthContract,
  SceneHealthQuery,
  SceneChannel,
  ScenePackageListResult,
  ScenePackageExportResult,
  ScenePackageDryRunResult,
  ScenePackageImportResult,
} from '../contracts/scene';

export async function fetchSceneHealth(query: SceneHealthQuery): Promise<{
  readonly data: SceneHealthContract;
  readonly traceId: string;
}> {
  const response = await intentRequestRaw<SceneHealthContract>({
    intent: 'scene.health',
    params: {
      mode: query.mode ?? 'summary',
      limit: query.limit,
      offset: query.offset,
      since: query.since,
      company_id: query.company_id,
    },
  });
  return { data: response.data, traceId: response.traceId };
}

export async function governanceSetChannel(input: {
  readonly reason: string;
  readonly channel: SceneChannel;
  readonly company_id?: number;
}): Promise<{ readonly data: GovernanceActionResult; readonly traceId: string }> {
  const response = await intentRequestRaw<GovernanceActionResult>({
    intent: 'scene.governance.set_channel',
    params: input,
  });
  return { data: response.data, traceId: response.traceId };
}

export async function governanceRollback(input: {
  readonly reason: string;
}): Promise<{ readonly data: GovernanceActionResult; readonly traceId: string }> {
  const response = await intentRequestRaw<GovernanceActionResult>({
    intent: 'scene.governance.rollback',
    params: input,
  });
  return { data: response.data, traceId: response.traceId };
}

export async function governancePinStable(input: {
  readonly reason: string;
}): Promise<{ readonly data: GovernanceActionResult; readonly traceId: string }> {
  const response = await intentRequestRaw<GovernanceActionResult>({
    intent: 'scene.governance.pin_stable',
    params: input,
  });
  return { data: response.data, traceId: response.traceId };
}

export async function governanceExportContract(input: {
  readonly reason: string;
  readonly channel: SceneChannel;
}): Promise<{ readonly data: GovernanceActionResult; readonly traceId: string }> {
  const response = await intentRequestRaw<GovernanceActionResult>({
    intent: 'scene.governance.export_contract',
    params: input,
  });
  return { data: response.data, traceId: response.traceId };
}

export async function scenePackageList(): Promise<{ readonly data: ScenePackageListResult; readonly traceId: string }> {
  const response = await intentRequestRaw<ScenePackageListResult>({
    intent: 'scene.package.list',
    params: {},
  });
  return { data: response.data, traceId: response.traceId };
}

export async function scenePackageExport(input: {
  readonly package_name: string;
  readonly package_version: string;
  readonly scene_channel: SceneChannel;
  readonly reason: string;
}): Promise<{ readonly data: ScenePackageExportResult; readonly traceId: string }> {
  const response = await intentRequestRaw<ScenePackageExportResult>({
    intent: 'scene.package.export',
    params: input,
  });
  return { data: response.data, traceId: response.traceId };
}

export async function scenePackageDryRunImport(input: {
  readonly package: Record<string, unknown>;
}): Promise<{ readonly data: ScenePackageDryRunResult; readonly traceId: string }> {
  const response = await intentRequestRaw<ScenePackageDryRunResult>({
    intent: 'scene.package.dry_run_import',
    params: input,
  });
  return { data: response.data, traceId: response.traceId };
}

export async function scenePackageImport(input: {
  readonly package: Record<string, unknown>;
  readonly strategy: 'skip_existing' | 'override_existing' | 'rename_on_conflict';
  readonly reason: string;
}): Promise<{ readonly data: ScenePackageImportResult; readonly traceId: string }> {
  const response = await intentRequestRaw<ScenePackageImportResult>({
    intent: 'scene.package.import',
    params: input,
  });
  return { data: response.data, traceId: response.traceId };
}
