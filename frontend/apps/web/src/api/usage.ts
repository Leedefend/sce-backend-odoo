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
