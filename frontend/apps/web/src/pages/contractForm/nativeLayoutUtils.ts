export type NativeLayoutLikeNode = Record<string, unknown> & {
  children?: unknown;
  pages?: unknown;
  tabs?: unknown;
  nodes?: unknown;
  items?: unknown;
};

const CHILD_KEYS = ['children', 'pages', 'tabs', 'nodes', 'items'] as const;

export function nativeLayoutNodeType(node: NativeLayoutLikeNode) {
  return String(node?.type || (node as { containerType?: string })?.containerType || '').trim().toLowerCase();
}

export function isNativeFieldLayoutNode(node: NativeLayoutLikeNode) {
  return nativeLayoutNodeType(node) === 'field' && Boolean(String(node?.name || '').trim());
}

export function nativeNodeFieldInfo(node?: NativeLayoutLikeNode | null): Record<string, unknown> {
  const fieldInfo = node?.fieldInfo && typeof node.fieldInfo === 'object' && !Array.isArray(node.fieldInfo)
    ? node.fieldInfo as Record<string, unknown>
    : {};
  if (Object.keys(fieldInfo).length) return fieldInfo;
  return node?.field_info && typeof node.field_info === 'object' && !Array.isArray(node.field_info)
    ? node.field_info as Record<string, unknown>
    : {};
}

export function normalizeNativeLayoutColumns(value: unknown): 1 | 2 | 3 | null {
  const columns = Number(value);
  return columns === 1 || columns === 2 || columns === 3 ? columns : null;
}

export function nativeModifierValue(nodeRaw: NativeLayoutLikeNode, key: 'invisible' | 'readonly' | 'required') {
  const node = nodeRaw as Record<string, unknown>;
  const attributes = node.attributes && typeof node.attributes === 'object'
    ? node.attributes as Record<string, unknown>
    : {};
  const action = node.action && typeof node.action === 'object' && !Array.isArray(node.action)
    ? node.action as Record<string, unknown>
    : {};
  const actionVisible = action.visible && typeof action.visible === 'object' && !Array.isArray(action.visible)
    ? action.visible as Record<string, unknown>
    : {};
  const actionVisibleAttrs = actionVisible.attrs && typeof actionVisible.attrs === 'object' && !Array.isArray(actionVisible.attrs)
    ? actionVisible.attrs as Record<string, unknown>
    : {};
  const fieldInfo = nativeNodeFieldInfo(node);
  const attributeModifiers = attributes.modifiers && typeof attributes.modifiers === 'object'
    ? attributes.modifiers as Record<string, unknown>
    : {};
  const fieldInfoModifiers = fieldInfo.modifiers && typeof fieldInfo.modifiers === 'object'
    ? fieldInfo.modifiers as Record<string, unknown>
    : {};
  const modifiers = node.modifiers && typeof node.modifiers === 'object'
    ? node.modifiers as Record<string, unknown>
    : {};
  if (key in modifiers) return modifiers[key];
  if (key in attributeModifiers) return attributeModifiers[key];
  if (key in actionVisibleAttrs) return actionVisibleAttrs[key];
  if (key in fieldInfoModifiers) return fieldInfoModifiers[key];
  if (key in fieldInfo) return fieldInfo[key];
  if (key in attributes) return attributes[key];
  if (key in node) return node[key];
  return undefined;
}

export function compareNativeModifierValue(actual: unknown, operator: string, expected: unknown) {
  const left = Array.isArray(actual) && typeof actual[0] === 'number' ? actual[0] : actual;
  const key = String(operator || '').trim();
  if (key === '=' || key === '==') return String(left ?? '') === String(expected ?? '');
  if (key === '!=' || key === '<>') return String(left ?? '') !== String(expected ?? '');
  if (key === 'in') return Array.isArray(expected) && expected.map((item) => String(item)).includes(String(left ?? ''));
  if (key === 'not in') return Array.isArray(expected) && !expected.map((item) => String(item)).includes(String(left ?? ''));
  if (key === '>') return Number(left) > Number(expected);
  if (key === '>=') return Number(left) >= Number(expected);
  if (key === '<') return Number(left) < Number(expected);
  if (key === '<=') return Number(left) <= Number(expected);
  return false;
}

export function isStaticTruthyModifier(value: unknown) {
  if (value === true || value === 1) return true;
  if (typeof value !== 'string') return false;
  return ['1', 'true', 'True'].includes(value.trim());
}

export function evaluateNativeModifierValue(value: unknown, resolveFieldValue: (field: string) => unknown): boolean {
  if (typeof value === 'boolean') return value;
  if (!value || typeof value !== 'object' || Array.isArray(value)) return isStaticTruthyModifier(value);
  const row = value as Record<string, unknown>;
  const kind = String(row.kind || '').trim();
  if (kind === 'static') return Boolean(row.value);
  if (kind === 'not') return !evaluateNativeModifierValue(row.expr, resolveFieldValue);
  if (kind === 'all') {
    const exprs = Array.isArray(row.exprs) ? row.exprs : [];
    return exprs.every((expr) => evaluateNativeModifierValue(expr, resolveFieldValue));
  }
  if (kind === 'any') {
    const exprs = Array.isArray(row.exprs) ? row.exprs : [];
    return exprs.some((expr) => evaluateNativeModifierValue(expr, resolveFieldValue));
  }
  const field = String(row.field || '').trim();
  if (!field) return false;
  if (kind === 'field_truthy') return Boolean(resolveFieldValue(field));
  if (kind === 'field_compare') return compareNativeModifierValue(resolveFieldValue(field), String(row.operator || ''), row.value);
  return false;
}

export function countNativeNodesByType(nodes: NativeLayoutLikeNode[], targetType: string): number {
  const target = String(targetType || '').trim().toLowerCase();
  let count = 0;
  nodes.forEach((node) => {
    if (nativeLayoutNodeType(node) === target) count += 1;
    CHILD_KEYS.forEach((key) => {
      const children = node?.[key];
      if (Array.isArray(children)) count += countNativeNodesByType(children as NativeLayoutLikeNode[], target);
    });
  });
  return count;
}

export function collectNativeLayoutBadgeCountFieldNames(nodes: NativeLayoutLikeNode[], out: Set<string>) {
  nodes.forEach((node) => {
    if (nativeLayoutNodeType(node) === 'button') {
      const action = node?.action && typeof node.action === 'object' && !Array.isArray(node.action)
        ? node.action as Record<string, unknown>
        : {};
      const badge = action.badge && typeof action.badge === 'object' && !Array.isArray(action.badge)
        ? action.badge as Record<string, unknown>
        : {};
      const fieldName = String(badge.count_field || badge.field || '').trim();
      if (fieldName) out.add(fieldName);
    }
    CHILD_KEYS.forEach((key) => {
      const children = node?.[key];
      if (Array.isArray(children)) collectNativeLayoutBadgeCountFieldNames(children as NativeLayoutLikeNode[], out);
    });
  });
}

export function collectContractActionBadgeCountFieldNames(actions: unknown, out: Set<string>) {
  if (!Array.isArray(actions)) return;
  actions.forEach((row) => {
    if (!row || typeof row !== 'object' || Array.isArray(row)) return;
    const action = row as Record<string, unknown>;
    const badge = action.badge && typeof action.badge === 'object' && !Array.isArray(action.badge)
      ? action.badge as Record<string, unknown>
      : {};
    const fieldName = String(badge.count_field || badge.field || '').trim();
    if (fieldName) out.add(fieldName);
  });
}
