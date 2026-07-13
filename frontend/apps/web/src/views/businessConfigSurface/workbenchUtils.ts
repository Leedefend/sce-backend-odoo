export function withSurfaceLoadTimeout<T>(request: Promise<T>, timeoutMs: number) {
  let timer: number | undefined;
  const timeout = new Promise<T>((_, reject) => {
    timer = window.setTimeout(() => {
      reject(new Error('配置能力读取超时，请检查网络或稍后点击“读取配置对象”重试。'));
    }, timeoutMs);
  });
  return Promise.race([request, timeout]).finally(() => {
    if (timer) {
      window.clearTimeout(timer);
    }
  });
}

export async function clearConsumedOpenIntent(keys: string[]) {
  const params = new URLSearchParams(window.location.search);
  let changed = false;
  keys.forEach((key) => {
    if (params.has(key)) {
      params.delete(key);
      changed = true;
    }
  });
  if (!changed) return;
  const query = params.toString();
  window.history.replaceState(window.history.state, '', `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`);
}

export function replaceWorkbenchQuerySilently(nextValues: Record<string, string | number | undefined>) {
  const params = new URLSearchParams(window.location.search);
  Object.entries(nextValues).forEach(([key, value]) => {
    const text = String(value ?? '').trim();
    if (text) {
      params.set(key, text);
    } else {
      params.delete(key);
    }
  });
  const query = params.toString();
  window.history.replaceState(window.history.state, '', `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`);
}
