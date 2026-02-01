import { useSessionStore } from '../stores/session';

export async function bootstrapApp() {
  const session = useSessionStore();
  if (!session.token) {
    return;
  }
  await session.loadAppInit();
}
