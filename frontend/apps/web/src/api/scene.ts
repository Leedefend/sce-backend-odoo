import { intentRequestRaw } from './intents';
import type {
  GovernanceActionResult,
  SceneHealthContract,
  SceneHealthQuery,
  SceneChannel,
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
