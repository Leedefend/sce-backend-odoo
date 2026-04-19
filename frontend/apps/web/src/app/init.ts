import { useSessionStore } from '../stores/session';
import { ApiError } from '../api/client';

const EXTENSION_NOISE_PATTERNS = [
  'chrome-extension://',
  'moz-extension://',
  'safari-extension://',
  'extension://',
  'inpage.js',
];

let extensionNoiseGuardInstalled = false;
const STARTUP_STATUS_EVENT = 'sc:startup-status';

function emitStartupStatus(status: 'bootstrapping' | 'ready' | 'auth_redirect' | 'error', detail?: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(STARTUP_STATUS_EVENT, {
    detail: {
      status,
      ...(detail || {}),
    },
  }));
}

function looksLikeExtensionNoise(input: unknown): boolean {
  const text = String(input || '').trim().toLowerCase();
  if (!text) return false;
  return EXTENSION_NOISE_PATTERNS.some((marker) => text.includes(marker));
}

function installExtensionNoiseGuard() {
  if (extensionNoiseGuardInstalled || typeof window === 'undefined') {
    return;
  }
  extensionNoiseGuardInstalled = true;
  window.addEventListener('error', (event) => {
    const filename = String(event.filename || '').trim();
    const message = String(event.message || '').trim();
    if (!looksLikeExtensionNoise(filename) && !looksLikeExtensionNoise(message)) {
      return;
    }
    event.preventDefault();
    // eslint-disable-next-line no-console
    console.info('[noise-guard] ignored browser extension error', { filename, message });
  });
  window.addEventListener('unhandledrejection', (event) => {
    const reason = (event as PromiseRejectionEvent).reason;
    const message = reason instanceof Error ? reason.message : String(reason || '');
    if (!looksLikeExtensionNoise(message)) {
      return;
    }
    event.preventDefault();
    // eslint-disable-next-line no-console
    console.info('[noise-guard] ignored browser extension rejection', { message });
  });
}

export async function bootstrapApp() {
  installExtensionNoiseGuard();
  const session = useSessionStore();
  session.restore();
  if (!session.token) {
    emitStartupStatus('ready', { reason: 'anonymous' });
    return;
  }
  emitStartupStatus('bootstrapping', { hasToken: true });
  try {
    await session.loadAppInit();
    emitStartupStatus('ready', { initStatus: session.initStatus });
  } catch (error) {
    if (
      error instanceof ApiError &&
      (error.status === 401
        || String(error.reasonCode || '').trim().toUpperCase() === 'AUTH_REQUIRED'
        || String(error.reasonCode || '').trim().toUpperCase() === 'AUTH_401')
    ) {
      emitStartupStatus('auth_redirect', { reasonCode: error.reasonCode || 'AUTH_401' });
      session.clearSession();
      const redirect = encodeURIComponent(`${window.location.pathname}${window.location.search}`);
      if (!window.location.pathname.startsWith('/login')) {
        window.location.replace(`/login?redirect=${redirect}`);
      }
      return;
    }
    emitStartupStatus('error', {
      message: error instanceof Error ? error.message : 'bootstrap failed',
      initStatus: session.initStatus,
    });
    // initStatus handled in store; avoid unhandled promise
  }
}

export { STARTUP_STATUS_EVENT };
