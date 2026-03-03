import { intentRequest } from './intents';

export async function trackTelemetryEvent(eventType: string, extra: Record<string, unknown> = {}) {
  if (!eventType) return;
  try {
    await intentRequest<{ event_type?: string }>({
      intent: 'telemetry.track',
      params: { event_type: eventType, ...extra },
    });
  } catch (err) {
    // Telemetry is best-effort only and must never block product flows.
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.warn('[telemetry.track] ignored:', err);
    }
  }
}
