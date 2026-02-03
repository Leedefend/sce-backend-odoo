import { useSessionStore } from '../stores/session';

export async function bootstrapApp() {
  const session = useSessionStore();
  session.restore();
  if (!session.token) {
    return;
  }
  try {
    await session.loadAppInit();
  } catch {
    // initStatus handled in store; avoid unhandled promise
  }
}
