import { intentRequest } from './intents';

export async function trackTelemetryEvent(eventType: string, extra: Record<string, unknown> = {}) {
  const normalizedType = String(eventType || '').trim();
  if (!normalizedType) return;
  const safeExtra = (extra && typeof extra === 'object') ? extra : {};
  try {
    await intentRequest<{ event_type?: string }>({
      intent: 'telemetry.track',
      params: { ...safeExtra, event_type: normalizedType },
      silentErrors: true,
    });
  } catch (err) {
    // Telemetry is best-effort only and must never block product flows.
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.warn('[telemetry.track] ignored:', err);
    }
  }
}
