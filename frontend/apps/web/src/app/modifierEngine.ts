export type FieldRuntimeState = {
  invisible: boolean;
  readonly: boolean;
  required: boolean;
};

type DomainLeaf = [string, string, unknown];

function isTruthyValue(value: unknown): boolean {
  const scalar = toScalar(value);
  if (scalar === null || scalar === undefined) return false;
  if (typeof scalar === 'boolean') return scalar;
  if (typeof scalar === 'number') return scalar !== 0;
  if (typeof scalar === 'string') {
    const normalized = scalar.trim().toLowerCase();
    if (!normalized) return false;
    if (['0', 'false', 'no', 'n', 'off', 'none', 'null'].includes(normalized)) return false;
    return true;
  }
  if (Array.isArray(scalar)) return scalar.length > 0;
  if (typeof scalar === 'object') return Object.keys(scalar as Record<string, unknown>).length > 0;
  return Boolean(scalar);
}

function coerceModifierBoolean(value: unknown): boolean | undefined {
  const scalar = toScalar(value);
  if (typeof scalar === 'boolean') return scalar;
  if (typeof scalar === 'number') return scalar !== 0;
  if (typeof scalar === 'string') {
    const normalized = scalar.trim().toLowerCase();
    if (!normalized) return false;
    if (['1', 'true', 'yes', 'y', 'on'].includes(normalized)) return true;
    if (['0', 'false', 'no', 'n', 'off', 'none', 'null'].includes(normalized)) return false;
  }
  return undefined;
}

function evalModifierExpression(expr: string, values: Record<string, unknown>): boolean | undefined {
  const normalized = expr.trim().replace(/\s+/g, ' ');
  if (!normalized) return false;
  const primitive = coerceModifierBoolean(normalized);
  if (primitive !== undefined) return primitive;

  const lower = normalized.toLowerCase();
  if (lower.startsWith('not ')) {
    const field = normalized.slice(4).trim();
    if (!field || /\s/.test(field)) return undefined;
    return !isTruthyValue(values[field]);
  }

  if (/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(normalized)) {
    return isTruthyValue(values[normalized]);
  }

  return undefined;
}

function looksLikeDomainExpr(expr: unknown): boolean {
  if (!Array.isArray(expr) || !expr.length) return false;
  const head = expr[0];
  if (head === '|' || head === '&' || head === '!') return true;
  if (Array.isArray(head)) return true;
  return expr.length >= 3 && typeof expr[0] === 'string' && typeof expr[1] === 'string';
}

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
  const primitive = coerceModifierBoolean(bucket);
  if (primitive !== undefined) return primitive;
  if (typeof bucket === 'string') {
    const expression = evalModifierExpression(bucket, values);
    if (expression !== undefined) return expression;
  }
  if (!bucket) return false;

  if (!Array.isArray(bucket)) {
    if (typeof bucket !== 'object') return false;
    const row = bucket as Record<string, unknown>;
    if (row.parsed !== undefined) return evalModifierBucket(row.parsed, values);
    if (row.raw !== undefined) return evalModifierBucket(row.raw, values);
    if (row.value !== undefined) return evalModifierBucket(row.value, values);
    return false;
  }

  if (!bucket.length) return false;
  if (looksLikeDomainExpr(bucket)) return evalDomain(bucket, values);

  return bucket.some((entry) => {
    const entryPrimitive = coerceModifierBoolean(entry);
    if (entryPrimitive !== undefined) return entryPrimitive;
    if (!entry || typeof entry !== 'object') return evalDomain(entry, values);
    const row = entry as Record<string, unknown>;
    if (row.parsed !== undefined) return evalModifierBucket(row.parsed, values);
    if (row.raw !== undefined) return evalModifierBucket(row.raw, values);
    if (row.value !== undefined) return evalModifierBucket(row.value, values);
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
