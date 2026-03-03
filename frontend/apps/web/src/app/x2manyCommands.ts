export type X2ManyCommand = [number, number, unknown?];

type X2ManyKind = 'many2many' | 'one2many';

function toPositiveInt(value: unknown): number | null {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) return null;
  return Math.trunc(parsed);
}

function pushId(out: Set<number>, value: unknown) {
  const parsed = toPositiveInt(value);
  if (parsed) out.add(parsed);
}

export function extractX2ManyIds(value: unknown): number[] {
  const out = new Set<number>();
  if (value === null || value === undefined || value === false) return [];

  if (typeof value === 'number' || typeof value === 'string') {
    pushId(out, value);
    return Array.from(out);
  }

  if (!Array.isArray(value)) return [];

  value.forEach((item) => {
    if (typeof item === 'number' || typeof item === 'string') {
      pushId(out, item);
      return;
    }
    if (!Array.isArray(item) || item.length < 2) return;
    const op = Number(item[0]);
    if (op === 6 && Array.isArray(item[2])) {
      (item[2] as unknown[]).forEach((id) => pushId(out, id));
      return;
    }
    if (op === 4 || op === 1) {
      pushId(out, item[1]);
      return;
    }
    if (typeof item[0] === 'number' && typeof item[1] === 'string') {
      pushId(out, item[0]);
    }
  });

  return Array.from(out);
}

export function hasExplicitX2ManyCommands(value: unknown): boolean {
  if (!Array.isArray(value)) return false;
  return value.some((item) => Array.isArray(item) && typeof item[0] === 'number');
}

function sanitizeExplicitCommands(value: unknown): X2ManyCommand[] {
  if (!Array.isArray(value)) return [];
  const out: X2ManyCommand[] = [];
  value.forEach((item) => {
    if (!Array.isArray(item) || item.length < 2) return;
    const op = Number(item[0]);
    if (!Number.isFinite(op)) return;
    const id = Number(item[1] || 0);
    const payload = item.length > 2 ? item[2] : undefined;
    out.push([Math.trunc(op), Number.isFinite(id) ? Math.trunc(id) : 0, payload]);
  });
  return out;
}

function diffCommands(kind: X2ManyKind, currentIds: number[], originalIds: number[]): X2ManyCommand[] {
  const current = new Set(currentIds);
  const original = new Set(originalIds);
  const commands: X2ManyCommand[] = [];

  currentIds.forEach((id) => {
    if (!original.has(id)) commands.push([4, id]);
  });

  originalIds.forEach((id) => {
    if (current.has(id)) return;
    commands.push([kind === 'one2many' ? 2 : 3, id]);
  });

  return commands;
}

export function buildX2ManyCommands(params: {
  kind: X2ManyKind;
  current: unknown;
  original?: unknown;
  mode: 'onchange' | 'write';
}): X2ManyCommand[] {
  const { kind, current, original, mode } = params;

  if (hasExplicitX2ManyCommands(current)) {
    return sanitizeExplicitCommands(current);
  }

  const currentIds = extractX2ManyIds(current);
  const originalIds = extractX2ManyIds(original);

  if (mode === 'onchange') {
    // Keep onchange payload deterministic and compact.
    return [[6, 0, currentIds]];
  }

  if (!originalIds.length) {
    if (kind === 'many2many') return [[6, 0, currentIds]];
    return currentIds.map((id) => [4, id]);
  }

  return diffCommands(kind, currentIds, originalIds);
}
