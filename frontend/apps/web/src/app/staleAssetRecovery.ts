const RECOVERY_STORAGE_KEY = 'sc_stale_asset_recovery_at';
const RECOVERY_COOLDOWN_MS = 60_000;

type BrowserRuntime = Pick<Window, 'addEventListener' | 'location' | 'sessionStorage'>;

function recoveryAllowed(runtime: BrowserRuntime, now: number): boolean {
  const previous = Number(runtime.sessionStorage.getItem(RECOVERY_STORAGE_KEY) || 0);
  return !Number.isFinite(previous) || previous <= 0 || now - previous >= RECOVERY_COOLDOWN_MS;
}

/**
 * Vite emits `vite:preloadError` when an already-open page requests a hashed
 * lazy chunk that disappeared during a new deployment. Reload the document
 * once so it receives the current asset manifest instead of presenting the
 * failure as a backend/network outage.
 */
export function installStaleAssetRecovery(runtime: BrowserRuntime = window, now: () => number = Date.now): void {
  runtime.addEventListener('vite:preloadError', (event) => {
    event.preventDefault();
    const occurredAt = now();
    if (!recoveryAllowed(runtime, occurredAt)) return;
    runtime.sessionStorage.setItem(RECOVERY_STORAGE_KEY, String(occurredAt));
    runtime.location.reload();
  });
}

