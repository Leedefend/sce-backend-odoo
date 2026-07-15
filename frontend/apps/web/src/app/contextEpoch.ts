let activeContextEpoch = 0;
let activeContextController = new AbortController();

function rotateContext(): number {
  activeContextController.abort('context_changed');
  activeContextController = new AbortController();
  activeContextEpoch += 1;
  return activeContextEpoch;
}

export function beginContextTransition(): number {
  return rotateContext();
}

export function currentContextEpoch(): number {
  return activeContextEpoch;
}

export function isCurrentContextEpoch(epoch: number): boolean {
  return epoch === activeContextEpoch;
}

export function currentContextSignal(): AbortSignal {
  return activeContextController.signal;
}

export function invalidateContextRequests(): void {
  rotateContext();
}
