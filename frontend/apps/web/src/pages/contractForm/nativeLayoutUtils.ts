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

export function normalizeNativeLayoutColumns(value: unknown): 1 | 2 | 3 | null {
  const columns = Number(value);
  return columns === 1 || columns === 2 || columns === 3 ? columns : null;
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
