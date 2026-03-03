export type FieldRuntimeState = {
  invisible: boolean;
  readonly: boolean;
  required: boolean;
};

type DomainLeaf = [string, string, unknown];

function toScalar(value: unknown) {
  if (Array.isArray(value) && value.length && typeof value[0] === 'number') {
    return value[0];
  }
  return value;
}

function compare(actual: unknown, op: string, expected: unknown): boolean {
  const left = toScalar(actual);
  const right = toScalar(expected);
  const key = String(op || '').trim().toLowerCase();

  if (key === '=' || key === '==') return String(left ?? '') === String(right ?? '');
  if (key === '!=' || key === '<>') return String(left ?? '') !== String(right ?? '');
  if (key === 'in') return Array.isArray(expected) && expected.map((x) => String(x ?? '')).includes(String(left ?? ''));
  if (key === 'not in') return Array.isArray(expected) && !expected.map((x) => String(x ?? '')).includes(String(left ?? ''));
  if (key === '>') return Number(left) > Number(right);
  if (key === '>=') return Number(left) >= Number(right);
  if (key === '<') return Number(left) < Number(right);
  if (key === '<=') return Number(left) <= Number(right);
  if (key === 'like' || key === 'ilike') return String(left ?? '').toLowerCase().includes(String(right ?? '').toLowerCase());
  return false;
}

function evalLeaf(expr: unknown, values: Record<string, unknown>): boolean {
  if (!Array.isArray(expr) || expr.length < 3) return false;
  const leaf = expr as DomainLeaf;
  const field = String(leaf[0] || '').trim();
  if (!field) return false;
  return compare(values[field], String(leaf[1] || ''), leaf[2]);
}

function evalDomain(expr: unknown, values: Record<string, unknown>): boolean {
  if (typeof expr === 'boolean') return expr;
  if (!Array.isArray(expr)) return false;
  if (!expr.length) return false;

  const head = expr[0];
  if (head === '|') {
    return evalDomain(expr[1], values) || evalDomain(expr[2], values);
  }
  if (head === '&') {
    return evalDomain(expr[1], values) && evalDomain(expr[2], values);
  }
  if (head === '!') {
    return !evalDomain(expr[1], values);
  }

  if (Array.isArray(head) && head.length >= 3) {
    return (expr as unknown[]).every((item) => evalLeaf(item, values));
  }

  return evalLeaf(expr, values);
}

function evalModifierBucket(bucket: unknown, values: Record<string, unknown>): boolean {
  if (typeof bucket === 'boolean') return bucket;
  if (!Array.isArray(bucket)) return false;
  if (!bucket.length) return false;

  return bucket.some((entry) => {
    if (typeof entry === 'boolean') return entry;
    if (!entry || typeof entry !== 'object') return evalDomain(entry, values);
    const row = entry as Record<string, unknown>;
    if (typeof row.parsed === 'boolean') return row.parsed;
    if (row.parsed !== undefined) return evalDomain(row.parsed, values);
    if (row.raw !== undefined) return evalDomain(row.raw, values);
    return evalDomain(entry, values);
  });
}

export function buildRuntimeFieldStates(params: {
  fieldNames: string[];
  fieldModifiers?: Record<string, Record<string, unknown>>;
  modifierPatch?: Record<string, Record<string, unknown>>;
  values: Record<string, unknown>;
}) {
  const modifiers = params.fieldModifiers || {};
  const patch = params.modifierPatch || {};
  const values = params.values || {};
  const states: Record<string, FieldRuntimeState> = {};

  for (const name of params.fieldNames) {
    const base = modifiers[name] || {};
    const extra = patch[name] || {};
    const merged = { ...base, ...extra };
    states[name] = {
      invisible: evalModifierBucket(merged.invisible, values),
      readonly: evalModifierBucket(merged.readonly, values),
      required: evalModifierBucket(merged.required, values),
    };
  }

  return states;
}
