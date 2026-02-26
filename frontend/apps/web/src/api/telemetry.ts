import { intentRequest } from './intents';

export async function trackTelemetryEvent(eventType: string, extra: Record<string, unknown> = {}) {
  if (!eventType) return;
  await intentRequest<{ event_type?: string }>({
    intent: 'telemetry.track',
    params: { event_type: eventType, ...extra },
  });
}
