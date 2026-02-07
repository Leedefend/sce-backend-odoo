import { intentRequest } from './intents';

export async function trackSceneOpen(sceneKey: string) {
  if (!sceneKey) return;
  await intentRequest<{ tracked?: string[] }>({
    intent: 'usage.track',
    params: { event_type: 'scene_open', scene_key: sceneKey },
  });
}

export async function trackCapabilityOpen(capabilityKey: string) {
  if (!capabilityKey) return;
  await intentRequest<{ tracked?: string[] }>({
    intent: 'usage.track',
    params: { event_type: 'capability_open', capability_key: capabilityKey },
  });
}

export type UsageTopItem = {
  key: string;
  count: number;
};

export type UsageReport = {
  generated_at: string;
  totals: {
    scene_open_total: number;
    capability_open_total: number;
  };
  daily: {
    scene_open: Array<{ day: string; count: number }>;
    capability_open: Array<{ day: string; count: number }>;
  };
  scene_top: UsageTopItem[];
  capability_top: UsageTopItem[];
};

export async function fetchUsageReport(top = 10) {
  return intentRequest<UsageReport>({
    intent: 'usage.report',
    params: { top },
  });
}

export type CapabilityVisibilityReport = {
  user: { id?: number; name?: string; login?: string };
  role_codes: string[];
  summary: {
    total: number;
    visible: number;
    hidden: number;
    ready: number;
    preview: number;
    locked: number;
  };
  reason_counts: Array<{ reason_code: string; count: number }>;
  hidden_samples: Array<{ key: string; name: string; reason_code: string; reason: string }>;
};

export async function fetchCapabilityVisibilityReport() {
  return intentRequest<CapabilityVisibilityReport>({
    intent: 'capability.visibility.report',
    params: {},
  });
}
