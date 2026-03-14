export type HomeActionEntry = {
  id: string;
  key: string;
  sceneKey: string;
  state: string;
};

function toText(value: unknown): string {
  const text = String(value ?? '').trim();
  if (!text || text.toLowerCase() === 'undefined' || text.toLowerCase() === 'null') return '';
  return text;
}

export function resolveHomeActionIntent(
  actionMap: Record<string, unknown>,
  actionKey: string,
  fallback = 'ui.contract',
): string {
  const row = actionMap[actionKey];
  if (!row || typeof row !== 'object') return fallback;
  const intent = toText((row as Record<string, unknown>).intent);
  return intent || fallback;
}

export function resolveHomeActionTarget(
  actionMap: Record<string, unknown>,
  actionKey: string,
): Record<string, unknown> {
  const row = actionMap[actionKey];
  if (!row || typeof row !== 'object') return {};
  const target = (row as Record<string, unknown>).target;
  return target && typeof target === 'object' ? target as Record<string, unknown> : {};
}

export function findEntryForHomeActionItem(
  item: Record<string, unknown>,
  entries: HomeActionEntry[],
): HomeActionEntry | null {
  const entryId = toText(item.entry_id || item.entryId);
  if (entryId) {
    const entryById = entries.find((entry) => entry.id === entryId);
    if (entryById) return entryById;
  }

  const entryKey = toText(item.entry_key || item.entryKey || item.key);
  if (entryKey) {
    const entryByKey = entries.find((entry) => entry.key === entryKey && entry.state === 'READY');
    if (entryByKey) return entryByKey;
  }

  const sceneKey = toText(item.scene_key || item.sceneKey);
  if (sceneKey) {
    const entryByScene = entries.find((entry) => entry.sceneKey === sceneKey && entry.state === 'READY');
    if (entryByScene) return entryByScene;
  }
  return null;
}

