export function createRecordViewLoadRuntime(
  routeIdentity: () => string,
  loadIdentity: () => string,
  isSettled: () => boolean,
) {
  let boundRouteIdentity = '';
  let inFlightKey = '';
  let inFlight: Promise<void> | null = null;
  let lastLoadedKey = '';
  let lastLoadedAt = 0;

  function acceptsRoute() {
    const current = routeIdentity();
    if (boundRouteIdentity && boundRouteIdentity !== current) return false;
    if (!boundRouteIdentity) boundRouteIdentity = current;
    return true;
  }

  function load(run: () => Promise<void>): Promise<void> {
    const key = loadIdentity();
    if (inFlight && inFlightKey === key) return inFlight;
    if (lastLoadedKey === key && Date.now() - lastLoadedAt < 1500 && isSettled()) return Promise.resolve();
    const request = run();
    inFlightKey = key;
    inFlight = request;
    void request.finally(() => {
      if (inFlight !== request) return;
      if (isSettled()) {
        lastLoadedKey = key;
        lastLoadedAt = Date.now();
      }
      inFlight = null;
      inFlightKey = '';
    });
    return request;
  }

  return { acceptsRoute, load };
}
