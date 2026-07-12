import type { FieldDescriptor } from '@sc/schema';

export type NativeLayoutLikeNode = Record<string, unknown> & {
  children?: unknown;
  pages?: unknown;
  tabs?: unknown;
  nodes?: unknown;
  items?: unknown;
};

export type SemanticFieldGroup = {
  name: string;
  label: string;
  collapsible: boolean;
  fields: string[];
};

export type FieldSemanticMeta = {
  semantic_type?: string;
  surface_role?: string;
  technical?: boolean;
};

export type NativeFormDesignFields = {
  keys: string[];
  labels: Record<string, string>;
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

export function resolveNativeFormRootColumns(nodes: NativeLayoutLikeNode[], fallback: 1 | 2 | 3 = 3): 1 | 2 | 3 {
  const walk = (items: NativeLayoutLikeNode[]): 1 | 2 | 3 | null => {
    for (const node of items) {
      const attrs = node && typeof node.attributes === 'object' && node.attributes
        ? node.attributes as Record<string, unknown>
        : {};
      const direct = normalizeNativeLayoutColumns(
        attrs.col
        ?? attrs.columns
        ?? (node as { cols?: unknown; columns?: unknown }).cols
        ?? (node as { cols?: unknown; columns?: unknown }).columns,
      );
      if (direct) return direct;
      for (const key of CHILD_KEYS) {
        const children = node?.[key];
        if (!Array.isArray(children)) continue;
        const nested = walk(children as NativeLayoutLikeNode[]);
        if (nested) return nested;
      }
    }
    return null;
  };
  return walk(nodes) || fallback;
}

export function collectNativeFormDesignFields(nodes: NativeLayoutLikeNode[]): NativeFormDesignFields {
  const keys: string[] = [];
  const seen = new Set<string>();
  const labels: Record<string, string> = {};
  const walk = (items: NativeLayoutLikeNode[]) => {
    items.forEach((node) => {
      const name = String(node?.name || '').trim();
      if (nativeLayoutNodeType(node) === 'field' && name && !seen.has(name)) {
        seen.add(name);
        keys.push(name);
        labels[name] = String(node?.string || node?.label || name).trim() || name;
      }
      CHILD_KEYS.forEach((key) => {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeLayoutLikeNode[]);
      });
    });
  };
  walk(nodes);
  return { keys, labels };
}

export function collectNativeVisibleFieldNames(
  nodes: NativeLayoutLikeNode[],
  isVisible: (name: string, node: NativeLayoutLikeNode) => boolean,
): Set<string> {
  const names = new Set<string>();
  const walk = (items: NativeLayoutLikeNode[]) => {
    items.forEach((node) => {
      const name = String(node?.name || '').trim();
      if (name && isVisible(name, node)) names.add(name);
      CHILD_KEYS.forEach((key) => {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeLayoutLikeNode[]);
      });
    });
  };
  walk(nodes);
  return names;
}

export function collectNativeVisibleFieldOrder(
  nodes: NativeLayoutLikeNode[],
  isVisible: (name: string, node: NativeLayoutLikeNode) => boolean,
): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  const walk = (items: NativeLayoutLikeNode[]) => {
    items.forEach((node) => {
      const name = String(node?.name || '').trim();
      if (isNativeFieldLayoutNode(node) && name && !seen.has(name) && isVisible(name, node)) {
        seen.add(name);
        out.push(name);
      }
      CHILD_KEYS.forEach((key) => {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeLayoutLikeNode[]);
      });
    });
  };
  walk(nodes);
  return out;
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item || '').trim()).filter(Boolean) : [];
}

export function normalizeSemanticFieldGroups(
  rawGroups: unknown,
  fallbackProfile: unknown,
): Record<string, SemanticFieldGroup> {
  const out: Record<string, SemanticFieldGroup> = {};
  const rows = Array.isArray(rawGroups) ? rawGroups : [];
  for (const item of rows) {
    if (!item || typeof item !== 'object' || Array.isArray(item)) continue;
    const row = item as Record<string, unknown>;
    const key = String(row.name || '').trim().toLowerCase();
    if (!key) continue;
    out[key] = {
      name: key,
      label: String(row.label || (key === 'core' ? '核心信息' : '高级信息')).trim(),
      collapsible: Boolean(row.collapsible),
      fields: stringList(row.fields),
    };
  }
  if (Object.keys(out).length) return out;

  const profile = fallbackProfile && typeof fallbackProfile === 'object' && !Array.isArray(fallbackProfile)
    ? fallbackProfile as Record<string, unknown>
    : {};
  const core = stringList(profile.core_fields);
  const advanced = stringList(profile.advanced_fields);
  if (!core.length && !advanced.length) return out;
  out.core = {
    name: 'core',
    label: '核心信息',
    collapsible: false,
    fields: core,
  };
  out.advanced = {
    name: 'advanced',
    label: '高级信息',
    collapsible: true,
    fields: advanced,
  };
  return out;
}

export function normalizeContractFieldSemantics(raw: unknown): Record<string, FieldSemanticMeta> {
  const out: Record<string, FieldSemanticMeta> = {};
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return out;
  Object.entries(raw as Record<string, unknown>).forEach(([name, value]) => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return;
    const row = value as Record<string, unknown>;
    out[name] = {
      semantic_type: String(row.semantic_type || '').trim().toLowerCase(),
      surface_role: String(row.surface_role || '').trim().toLowerCase(),
      technical: Boolean(row.technical),
    };
  });
  return out;
}

export function resolveFieldSemanticMeta(
  fieldName: string,
  fieldSemantics: Record<string, FieldSemanticMeta>,
  descriptor?: FieldDescriptor,
): FieldSemanticMeta {
  const name = String(fieldName || '').trim();
  const fromMap = fieldSemantics[name];
  if (fromMap) return fromMap;
  const source = descriptor as Record<string, unknown> | undefined;
  return {
    semantic_type: String(source?.semantic_type || '').trim().toLowerCase(),
    surface_role: String(source?.surface_role || '').trim().toLowerCase(),
    technical: Boolean(source?.technical),
  };
}

export function semanticFieldNamesBySurfaceRole(
  fields: Record<string, FieldDescriptor> | undefined,
  fieldSemantics: Record<string, FieldSemanticMeta>,
  groups: Record<string, SemanticFieldGroup>,
  role: 'core' | 'advanced',
): string[] {
  const fromSemantic = Object.keys(fields || {}).filter((name) => (
    resolveFieldSemanticMeta(name, fieldSemantics, fields?.[name]).surface_role === role
  ));
  if (fromSemantic.length) return fromSemantic;
  return groups[role]?.fields || [];
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

export function nativeNodeWidget(node?: NativeLayoutLikeNode | null) {
  const fieldInfo = nativeNodeFieldInfo(node);
  return String(node?.widget || fieldInfo.widget || '').trim().toLowerCase();
}

export function nativeNodeWidgetSemantics(node?: NativeLayoutLikeNode | null) {
  const fieldInfo = nativeNodeFieldInfo(node);
  const semantics = fieldInfo.widget_semantics && typeof fieldInfo.widget_semantics === 'object'
    ? fieldInfo.widget_semantics as Record<string, unknown>
    : {};
  return semantics;
}

export function nativeNodeFieldDescriptor(
  nodeRaw: NativeLayoutLikeNode,
  fallback: FieldDescriptor | undefined,
  resolveFieldLabel: (name: string) => string,
): FieldDescriptor | undefined {
  const node = nodeRaw as Record<string, unknown>;
  const fieldInfo = nativeNodeFieldInfo(node);
  if (!Object.keys(fieldInfo).length && !fallback) return undefined;
  const name = String(nodeRaw?.name || fieldInfo.name || fallback?.name || '').trim();
  const label = String(resolveFieldLabel(name) || fallback?.string || node.string || node.label || fieldInfo.string || fieldInfo.label || name || '').trim();
  const type = String(fieldInfo.type || fieldInfo.ttype || fallback?.type || fallback?.ttype || '').trim();
  const relation = String(fieldInfo.relation || fallback?.relation || '').trim();
  const relationField = String(fieldInfo.relation_field || fallback?.relation_field || '').trim();
  const widget = String(node.widget || fieldInfo.widget || (fallback as Record<string, unknown> | undefined)?.widget || '').trim();
  const selection = Array.isArray(fieldInfo.selection)
    ? fieldInfo.selection as FieldDescriptor['selection']
    : fallback?.selection;
  const domain = fieldInfo.domain !== undefined
    ? fieldInfo.domain
    : (fallback as Record<string, unknown> | undefined)?.domain;
  const context = fieldInfo.context !== undefined
    ? fieldInfo.context
    : (fallback as Record<string, unknown> | undefined)?.context;
  const relationEntry = fieldInfo.relation_entry !== undefined
    ? fieldInfo.relation_entry
    : (fallback as Record<string, unknown> | undefined)?.relation_entry;
  const widgetOptions = fieldInfo.widget_options !== undefined
    ? fieldInfo.widget_options
    : (fieldInfo.options !== undefined
      ? fieldInfo.options
      : ((fallback as Record<string, unknown> | undefined)?.widget_options
        ?? (fallback as Record<string, unknown> | undefined)?.options));
  return {
    ...(fallback || {}),
    ...(name ? { name } : {}),
    ...(label ? { string: label } : {}),
    ...(type ? { type, ttype: type } : {}),
    ...(typeof fieldInfo.required === 'boolean' ? { required: fieldInfo.required } : {}),
    ...(typeof fieldInfo.readonly === 'boolean' ? { readonly: fieldInfo.readonly } : {}),
    ...(selection ? { selection } : {}),
    ...(relation ? { relation } : {}),
    ...(relationField ? { relation_field: relationField } : {}),
    ...(widget ? { widget } : {}),
    ...(domain !== undefined ? { domain } : {}),
    ...(context !== undefined ? { context } : {}),
    ...(relationEntry !== undefined ? { relation_entry: relationEntry } : {}),
    ...(widgetOptions !== undefined ? { widget_options: widgetOptions } : {}),
  } as FieldDescriptor;
}

export function findNativeFieldNode(nodes: NativeLayoutLikeNode[], name: string): NativeLayoutLikeNode | null {
  const target = String(name || '').trim();
  if (!target) return null;
  for (const node of nodes) {
    if (nativeLayoutNodeType(node) === 'field' && String(node?.name || '').trim() === target) return node;
    for (const key of CHILD_KEYS) {
      const children = node?.[key];
      if (!Array.isArray(children)) continue;
      const found = findNativeFieldNode(children as NativeLayoutLikeNode[], target);
      if (found) return found;
    }
  }
  return null;
}

export function nativeFieldSubview(nodes: NativeLayoutLikeNode[], name: string): Record<string, unknown> | null {
  const node = findNativeFieldNode(nodes, name);
  if (!node) return null;
  const fieldInfo = nativeNodeFieldInfo(node);
  const subview = fieldInfo?.subview;
  if (subview && typeof subview === 'object' && !Array.isArray(subview)) {
    return subview as Record<string, unknown>;
  }
  return null;
}

export function resolveNativeButtonLabel(node: NativeLayoutLikeNode, resolveFieldValue: (field: string) => unknown) {
  const action = node?.action && typeof node.action === 'object' && !Array.isArray(node.action)
    ? node.action as Record<string, unknown>
    : {};
  const badge = action.badge && typeof action.badge === 'object' && !Array.isArray(action.badge)
    ? action.badge as Record<string, unknown>
    : {};
  const countField = String(badge.count_field || badge.field || '').trim();
  const sourceField = String(badge.source_field || '').trim();
  const badgeLabel = String(badge.label || node.displayLabel || node.label || node.string || node.name || '').trim();
  const fallbackLabel = String(node.displayLabel || action.displayLabel || node.label || node.string || node.name || '操作').trim();
  if (!badgeLabel) {
    return fallbackLabel;
  }
  const countValue = countField ? resolveFieldValue(countField) : undefined;
  const count = Array.isArray(countValue) ? countValue.length : (typeof countValue === 'number' ? countValue : null);
  if (count !== null) {
    return `${count}${badgeLabel}`;
  }
  const sourceValue = sourceField ? resolveFieldValue(sourceField) : undefined;
  const sourceCount = Array.isArray(sourceValue) ? sourceValue.length : (typeof sourceValue === 'number' ? sourceValue : null);
  if (sourceCount === null) {
    return fallbackLabel;
  }
  return `${sourceCount}${badgeLabel}`;
}

export function collectNativeVisibleSectionTitles(nodes: NativeLayoutLikeNode[]): string[] {
  const titles: string[] = [];
  const titledContainerTypes = new Set(['group', 'page']);
  nodes.forEach((node) => {
    const type = nativeLayoutNodeType(node);
    const raw = String(node?.string || node?.label || '').trim();
    if (raw && titledContainerTypes.has(type) && raw.toLowerCase() !== type) {
      titles.push(raw);
    }
    CHILD_KEYS.forEach((key) => {
      const children = node?.[key];
      if (Array.isArray(children)) titles.push(...collectNativeVisibleSectionTitles(children as NativeLayoutLikeNode[]));
    });
  });
  return Array.from(new Set(titles));
}

export function collectNativeLayoutFieldNames(
  nodes: NativeLayoutLikeNode[],
  out: Set<string>,
  isKnownField: (name: string) => boolean,
) {
  nodes.forEach((node) => {
    const type = nativeLayoutNodeType(node);
    const name = String(node?.name || '').trim();
    if (type === 'field' && name && isKnownField(name)) {
      out.add(name);
    }
    CHILD_KEYS.forEach((key) => {
      const children = node?.[key];
      if (Array.isArray(children)) collectNativeLayoutFieldNames(children as NativeLayoutLikeNode[], out, isKnownField);
    });
  });
}

export function collectNativeFavoriteFieldNames(nodes: NativeLayoutLikeNode[], out: Set<string>) {
  for (const node of nodes) {
    const name = String(node?.name || '').trim();
    const label = String(node?.label || node?.string || '').trim();
    if (
      name
      && (
        nativeNodeWidget(node) === 'boolean_favorite'
        || name === 'is_favorite'
        || (nativeNodeWidget(node) === 'checkbox' && label.includes('仪表板'))
      )
    ) {
      out.add(name);
    }
    CHILD_KEYS.forEach((key) => {
      const children = node?.[key];
      if (Array.isArray(children)) collectNativeFavoriteFieldNames(children as NativeLayoutLikeNode[], out);
    });
  }
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
