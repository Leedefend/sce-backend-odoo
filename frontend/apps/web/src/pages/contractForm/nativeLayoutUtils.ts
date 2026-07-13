import type { FieldDescriptor } from '@sc/schema';
import type { FormSectionFieldSchema } from '../../components/template/formSection.types';
import {
  lowCodeFieldSizeClass,
  normalizeLowCodeFieldSize,
  normalizeRelationIds,
  toDateInputValue,
  toDatetimeInputValue,
} from './fieldUtils';
import type { LayoutNode, LowCodeFieldSize } from './types';

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

export type FormDataFieldNameInput = {
  contract: unknown;
  fields: Record<string, FieldDescriptor>;
  rawNativeLayoutNodes: NativeLayoutLikeNode[];
  layoutFieldNames: string[];
  visibleFields: string[];
  statusField?: string;
  mainData?: Record<string, unknown>;
};

export type NativeActionVisibilityInput = {
  row: Record<string, unknown>;
  currentState?: string;
  evaluateModifier: (value: unknown) => boolean;
  resolveAction: (row: Record<string, unknown>) => unknown;
};

export type VisibleNativeLayoutFilterInput<T extends NativeLayoutLikeNode> = {
  nodes: T[];
  isNodeVisible: (node: T) => boolean;
  groupVisibilityEditable: boolean;
  normalizeGroupTitle: (value: unknown) => string;
  isGroupVisible: (title: string) => boolean;
};

export type NativeFieldOrderPreviewInput<T extends NativeLayoutLikeNode> = {
  nodes: T[];
  fieldOrder: string[];
  movedGroups: Record<string, string>;
  moveTargetDraft: Record<string, string>;
  normalizeGroupTitle: (value: unknown) => string;
  isReadableGroupTitle: (value: unknown) => boolean;
  groupTitleMatches: (value: unknown, target: string) => boolean;
  baseGroupTitleForField: (fieldName: string) => string;
};

export type NativeFieldPresentationInput = {
  node: NativeLayoutLikeNode;
  descriptor?: FieldDescriptor;
  resolveFieldLabel?: (name: string) => string;
  editable: boolean;
  effectiveFieldSize: (name: string) => LowCodeFieldSize;
};

export type NativeFieldPresentation = {
  label: string;
  nodeClass: string;
  spanClass: string;
};

export type RuntimeFieldStateLike = {
  invisible?: boolean;
  readonly?: boolean;
  required?: boolean;
};

export type FieldPolicyLike = {
  visible: boolean;
  readonly?: boolean;
  required?: boolean;
};

export function filterVisibleNativeLayoutNodes<T extends NativeLayoutLikeNode>(
  params: VisibleNativeLayoutFilterInput<T>,
): T[] {
  return params.nodes
    .filter((node) => params.isNodeVisible(node))
    .map((node) => {
      const next = { ...node } as Record<string, unknown>;
      const nodeType = String(next.type || '').trim().toLowerCase();
      if (params.groupVisibilityEditable && nodeType === 'group') {
        const title = params.normalizeGroupTitle(next.string || next.label || next.title);
        if (title && !params.isGroupVisible(title)) next.visible = false;
      }
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const value = next[key];
        if (Array.isArray(value)) {
          next[key] = filterVisibleNativeLayoutNodes({
            ...params,
            nodes: value as T[],
          });
        }
      });
      return next as T;
    });
}

export function applyNativeFieldOrderPreview<T extends NativeLayoutLikeNode>(
  params: NativeFieldOrderPreviewInput<T>,
): T[] {
  if (!params.fieldOrder.length) return params.nodes;
  const rank = new Map(params.fieldOrder.map((fieldName, index) => [fieldName, index]));
  const movedNames = new Set(Object.keys(params.movedGroups));
  const movedNodes = new Map<string, T>();
  const sortDirectFields = (rows: T[]) => {
    const fields = rows.filter(isNativeFieldLayoutNode).sort((left, right) => {
      const leftRank = rank.get(String(left.name || '').trim()) ?? Number.MAX_SAFE_INTEGER;
      const rightRank = rank.get(String(right.name || '').trim()) ?? Number.MAX_SAFE_INTEGER;
      return leftRank - rightRank;
    });
    let index = 0;
    const sorted = rows.map((row) => (isNativeFieldLayoutNode(row) ? fields[index++] : row));
    return index < fields.length ? [...sorted, ...fields.slice(index)] : sorted;
  };
  const collectMoved = (rows: T[]) => {
    rows.forEach((node) => {
      const name = String(node?.name || '').trim();
      if (isNativeFieldLayoutNode(node) && movedNames.has(name)) movedNodes.set(name, node);
      CHILD_KEYS.forEach((key) => {
        const value = node?.[key];
        if (Array.isArray(value)) collectMoved(value as T[]);
      });
    });
  };
  collectMoved(params.nodes);

  const cloneWithoutMoved = (rows: T[]): T[] => rows.flatMap((node) => {
    const name = String(node?.name || '').trim();
    if (isNativeFieldLayoutNode(node) && movedNames.has(name)) return [];
    const next = { ...node } as Record<string, unknown>;
    CHILD_KEYS.forEach((key) => {
      const value = next[key];
      if (Array.isArray(value)) next[key] = cloneWithoutMoved(value as T[]);
    });
    return [next as T];
  });

  const withChildren = movedNodes.size
    ? cloneWithoutMoved(params.nodes)
    : params.nodes.map((node) => {
      const next = { ...node } as Record<string, unknown>;
      CHILD_KEYS.forEach((key) => {
        const value = next[key];
        if (Array.isArray(value)) {
          next[key] = applyNativeFieldOrderPreview({
            ...params,
            nodes: value as T[],
          });
        }
      });
      return next as T;
    });

  if (movedNodes.size) {
    const injected = new Set<string>();
    const injectIntoTarget = (rows: T[]): T[] => rows.map((node) => {
      const next = { ...node } as Record<string, unknown>;
      CHILD_KEYS.forEach((key) => {
        const value = next[key];
        if (Array.isArray(value)) next[key] = injectIntoTarget(value as T[]);
      });
      const children = Array.isArray(next.children) ? next.children as T[] : [];
      const directFieldGroupTitle = () => {
        for (const child of children) {
          const fieldName = String(child?.name || '').trim();
          if (!isNativeFieldLayoutNode(child) || !fieldName) continue;
          const title = params.normalizeGroupTitle(params.baseGroupTitleForField(fieldName) || params.movedGroups[fieldName]);
          if (title) return title;
        }
        return '';
      };
      const nodeTitle = params.isReadableGroupTitle(next.string || next.label)
        ? params.normalizeGroupTitle(next.string || next.label)
        : '';
      const title = directFieldGroupTitle() || nodeTitle;
      const directFieldNames = children
        .filter(isNativeFieldLayoutNode)
        .map((child) => String(child.name || '').trim())
        .filter(Boolean);
      const isFieldGroupContainer = nativeLayoutNodeType(next as NativeLayoutLikeNode) === 'group' && directFieldNames.length > 0;
      const toAppend = Array.from(movedNodes.entries())
        .filter(([name]) => (
          !injected.has(name)
          && isFieldGroupContainer
          && (
            params.groupTitleMatches(params.movedGroups[name], title)
            || directFieldNames.includes(String(params.moveTargetDraft[name] || '').trim())
          )
        ))
        .map(([name, nodeValue]) => {
          injected.add(name);
          return nodeValue;
        });
      if (toAppend.length) next.children = sortDirectFields([...children, ...toAppend]);
      return next as T;
    });
    const injectedTree = injectIntoTarget(withChildren);
    const fallback = Array.from(movedNodes.entries())
      .filter(([name]) => !injected.has(name))
      .map(([name, nodeValue]) => {
        injected.add(name);
        return nodeValue;
      });
    if (fallback.length) {
      let consumed = false;
      const injectFallback = (rows: T[]): T[] => rows.map((node) => {
        if (consumed) return node;
        const next = { ...node } as Record<string, unknown>;
        const children = Array.isArray(next.children) ? next.children as T[] : [];
        const directFieldNames = children
          .filter(isNativeFieldLayoutNode)
          .map((child) => String(child.name || '').trim())
          .filter(Boolean);
        if (directFieldNames.length) {
          next.children = sortDirectFields([...children, ...fallback]);
          consumed = true;
          return next as T;
        }
        CHILD_KEYS.forEach((key) => {
          const value = next[key];
          if (Array.isArray(value)) next[key] = injectFallback(value as T[]);
        });
        return next as T;
      });
      const withFallback = injectFallback(injectedTree);
      return consumed ? withFallback : [...injectedTree, ...sortDirectFields(fallback)];
    }
    return injectedTree;
  }

  const fieldNodes = withChildren.filter(isNativeFieldLayoutNode);
  if (fieldNodes.length <= 1) return withChildren;
  const sortedFields = [...fieldNodes].sort((left, right) => {
    const leftRank = rank.get(String(left.name || '').trim()) ?? Number.MAX_SAFE_INTEGER;
    const rightRank = rank.get(String(right.name || '').trim()) ?? Number.MAX_SAFE_INTEGER;
    return leftRank - rightRank;
  });
  let fieldIndex = 0;
  return withChildren.map((node) => (isNativeFieldLayoutNode(node) ? sortedFields[fieldIndex++] : node));
}

export type LegacyLayoutNodeInput = {
  fields: Record<string, FieldDescriptor>;
  order: unknown;
  containerStatus: Record<string, { visible?: boolean; disabled?: boolean }>;
  visibleFields: string[];
  fallbackFieldNames: string[];
  isCreate: boolean;
  readonly: boolean;
  resolveFieldLabel: (name: string) => string;
  evaluatePolicy: (name: string, descriptor: FieldDescriptor) => FieldPolicyLike;
  runtimeState: (name: string) => RuntimeFieldStateLike;
};

export type NativeFieldSchemasInput = {
  nodes: NativeLayoutLikeNode[];
  mapNode: (node: NativeLayoutLikeNode, index: number) => LayoutNode | null;
  buildSchemas: (fields: LayoutNode[]) => FormSectionFieldSchema[];
  applyReadonlyValues: (schemas: FormSectionFieldSchema[]) => FormSectionFieldSchema[];
  orderActive: boolean;
  fieldOrder: string[];
  favoriteActive: (fieldName: string) => boolean;
  favoriteReadonly: (field: LayoutNode) => boolean;
};

export type ReadonlyFieldValueResolver = (fieldName: string) => { found: boolean; value: unknown };

export type RequiredMarkInput = {
  node: LayoutNode;
  showHud: boolean;
  renderProfile: string;
  policyRequiredFields: Set<string>;
  validationRequiredFields: Set<string>;
  coreFieldNames: string[];
};

export type NativeFieldVisibilityInput = {
  name: string;
  node?: NativeLayoutLikeNode;
  statusField?: string;
  showHud: boolean;
  renderProfile: string;
  isCreate: boolean;
  isNodeVisible: (node: NativeLayoutLikeNode) => boolean;
  resolveDescriptor: (name: string, node?: NativeLayoutLikeNode) => FieldDescriptor | undefined;
  resolveFieldLabel: (name: string) => string;
  semantic: (name: string) => FieldSemanticMeta;
  runtimeState: (name: string) => RuntimeFieldStateLike;
  evaluatePolicy: (name: string, descriptor: FieldDescriptor) => FieldPolicyLike;
};

export type NativeLayoutNodeVisibilityInput = {
  node: NativeLayoutLikeNode;
  editable: boolean;
  evaluateModifier: (value: unknown) => boolean;
  normalizeGroupTitle: (value: unknown) => string;
  isGroupVisible: (title: string) => boolean;
  isFieldVisibleInDraft: (fieldName: string) => boolean | undefined;
  resolveAction: (row: Record<string, unknown>) => unknown;
};

const CHILD_KEYS = ['children', 'pages', 'tabs', 'nodes', 'items'] as const;
const CREATE_WORKFLOW_STATE_FIELD_NAMES = new Set([
  'state',
  'status',
  'lifecycle_state',
  'workflow_state',
  'approval_state',
  'tier_validation_state',
  'validation_state',
  'document_status',
  'document_state',
  'document_state_label',
  'legacy_document_state',
  'legacy_document_state_label',
  'legacy_visible_document_state',
]);

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

export function collectFormDataFieldNames(input: FormDataFieldNameInput): string[] {
  const contractRecord = input.contract && typeof input.contract === 'object' && !Array.isArray(input.contract)
    ? input.contract as Record<string, unknown>
    : {};
  const toolbar = contractRecord.toolbar && typeof contractRecord.toolbar === 'object' && !Array.isArray(contractRecord.toolbar)
    ? contractRecord.toolbar as Record<string, unknown>
    : {};
  const views = contractRecord.views && typeof contractRecord.views === 'object' && !Array.isArray(contractRecord.views)
    ? contractRecord.views as Record<string, unknown>
    : {};
  const formView = views.form && typeof views.form === 'object' && !Array.isArray(views.form)
    ? views.form as Record<string, unknown>
    : {};
  const names = new Set<string>();
  const fieldMap = input.fields || {};
  collectNativeLayoutFieldNames(input.rawNativeLayoutNodes, names, (name) => Boolean(fieldMap[name]));
  collectNativeLayoutBadgeCountFieldNames(input.rawNativeLayoutNodes, names);
  collectContractActionBadgeCountFieldNames(contractRecord.buttons, names);
  collectContractActionBadgeCountFieldNames(toolbar.header, names);
  collectContractActionBadgeCountFieldNames(toolbar.sidebar, names);
  collectContractActionBadgeCountFieldNames(toolbar.footer, names);
  collectContractActionBadgeCountFieldNames(formView.header_buttons, names);
  collectContractActionBadgeCountFieldNames(formView.button_box, names);
  collectContractActionBadgeCountFieldNames(formView.business_actions, names);
  input.layoutFieldNames.forEach((name) => {
    if (fieldMap[name]) names.add(name);
  });
  input.visibleFields.forEach((name) => {
    if (fieldMap[name]) names.add(name);
  });
  const statusField = String(input.statusField || '').trim();
  if (statusField && fieldMap[statusField]) names.add(statusField);
  ['can_review', 'validation_status'].forEach((name) => {
    if (fieldMap[name] || Object.prototype.hasOwnProperty.call(input.mainData || {}, name)) names.add(name);
  });
  if (fieldMap.active) names.add('active');
  if (!names.size) {
    Object.keys(fieldMap).slice(0, 40).forEach((name) => names.add(name));
  }
  return Array.from(names);
}

export function isNativeActionVisible(input: NativeActionVisibilityInput): boolean {
  const row = input.row;
  const nativeAction = row.action && typeof row.action === 'object' && !Array.isArray(row.action)
    ? row.action as Record<string, unknown>
    : {};
  const visibleRaw = nativeAction.visible || row.visible;
  const visible = visibleRaw && typeof visibleRaw === 'object' && !Array.isArray(visibleRaw)
    ? visibleRaw as Record<string, unknown>
    : {};
  const states = Array.isArray(visible.states)
    ? visible.states.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  const currentState = String(input.currentState || '').trim();
  if (states.length && currentState && !states.includes(currentState)) return false;
  const attrs = visible.attrs && typeof visible.attrs === 'object' && !Array.isArray(visible.attrs)
    ? visible.attrs as Record<string, unknown>
    : {};
  const modifiers = row.modifiers && typeof row.modifiers === 'object' && !Array.isArray(row.modifiers)
    ? row.modifiers as Record<string, unknown>
    : {};
  const invisible = attrs.invisible ?? modifiers.invisible ?? row.invisible;
  if (input.evaluateModifier(invisible)) return false;
  const nativeType = String(row.type || row.buttonType || '').trim().toLowerCase();
  const hasNativeActionShape = nativeType === 'button'
    || nativeType === 'object'
    || nativeType === 'server'
    || Boolean(row.action || row.payload || row.name || row.method);
  if (hasNativeActionShape && !input.resolveAction(row)) return false;
  return true;
}

export function nativeFieldLabel(
  nodeRaw: NativeLayoutLikeNode,
  descriptor?: FieldDescriptor,
  resolveFieldLabel?: (name: string) => string,
) {
  const node = nodeRaw as Record<string, unknown>;
  const fieldInfo = nativeNodeFieldInfo(node);
  const name = String(nodeRaw.name || '');
  return String(
    resolveFieldLabel?.(name)
    || descriptor?.string
    || node.string
    || node.label
    || fieldInfo.string
    || fieldInfo.label
    || nodeRaw.name
    || '',
  );
}

export function nativeFieldPresentation(input: NativeFieldPresentationInput): NativeFieldPresentation {
  const name = String(input.node.name || '').trim();
  const nodeClass = String((input.node as Record<string, unknown>).class || (input.node as Record<string, unknown>).className || '').trim();
  const fieldSize = input.editable
    ? input.effectiveFieldSize(name)
    : normalizeLowCodeFieldSize(
      (input.node as Record<string, unknown>).field_size
      || (input.node as Record<string, unknown>).fieldSize
      || (nodeClass.includes('field--large') ? 'large'
        : (nodeClass.includes('field--full') ? 'full'
          : (nodeClass.includes('field--wide') ? 'wide' : 'normal'))),
    );
  return {
    label: nativeFieldLabel(input.node, input.descriptor, input.resolveFieldLabel),
    nodeClass,
    spanClass: lowCodeFieldSizeClass(fieldSize) || nodeClass,
  };
}

export function isCreateWorkflowStateField(name: string, label = '', isCreate = false) {
  const normalized = String(name || '').trim();
  const normalizedLabel = String(label || '').replace(/\s+/g, '').trim();
  return isCreate && (
    CREATE_WORKFLOW_STATE_FIELD_NAMES.has(normalized)
    || normalizedLabel === '状态'
    || normalizedLabel.endsWith('状态')
  );
}

export function buildLegacyLayoutNodes(input: LegacyLayoutNodeInput): LayoutNode[] {
  const used = new Set<string>();
  const nodes: LayoutNode[] = [];

  function pushField(nameRaw: unknown) {
    const name = String(nameRaw || '').trim();
    if (!name || used.has(name)) return;
    const descriptor = input.fields[name];
    if (!descriptor) return;
    const label = String(input.resolveFieldLabel(name) || descriptor?.string || name);
    if (isCreateWorkflowStateField(name, label, input.isCreate)) return;
    const containerStatus = input.containerStatus[name];
    if (containerStatus?.visible === false) return;
    const resolved = input.evaluatePolicy(name, descriptor);
    if (!resolved.visible) return;
    used.add(name);
    const state = input.runtimeState(name);
    nodes.push({
      key: `field_${name}`,
      kind: 'field',
      name,
      label,
      readonly: Boolean(resolved.readonly || state.readonly || containerStatus?.disabled === true || input.readonly),
      required: Boolean(resolved.required || state.required),
      descriptor,
    });
  }

  function walkLayout(nodeRaw: unknown, parentKey: string) {
    if (!nodeRaw || typeof nodeRaw !== 'object') return;
    const node = nodeRaw as Record<string, unknown>;
    const kind = String(node.type || '').trim().toLowerCase();
    if (!kind) return;
    const label = String(node.string || node.label || '').trim();
    const nodeKey = `${parentKey}_${kind}_${String(node.name || label || nodes.length)}`;

    if (kind === 'header' || kind === 'sheet' || kind === 'group' || kind === 'notebook' || kind === 'page') {
      nodes.push({
        key: `layout_${nodeKey}`,
        kind: kind as LayoutNode['kind'],
        name: String(node.name || '').trim(),
        label,
        readonly: true,
        required: false,
      });
    }
    if (kind === 'field') {
      pushField(node.name);
      return;
    }
    CHILD_KEYS.forEach((key) => {
      const children = node[key];
      if (!Array.isArray(children)) return;
      children.forEach((child, index) => walkLayout(child, `${nodeKey}_${key}_${index}`));
    });
  }

  if (Array.isArray(input.order)) {
    input.order.forEach((item, index) => walkLayout(item, `root_${index}`));
  }
  if (!nodes.some((node) => node.kind === 'field')) {
    const fallback = input.visibleFields.length ? input.visibleFields : input.fallbackFieldNames;
    const fallbackFields = fallback.length ? fallback : Object.keys(input.fields).slice(0, 16);
    fallbackFields.forEach((name) => pushField(name));
  }
  return nodes;
}

export function buildNativeFieldSchemas(input: NativeFieldSchemasInput): FormSectionFieldSchema[] {
  const mappedNodes = input.nodes
    .map((node, index) => ({ raw: node, field: input.mapNode(node, index) }))
    .filter((item): item is { raw: NativeLayoutLikeNode; field: LayoutNode } => Boolean(item.field));
  const favoriteNode = mappedNodes.find((item) => item.field.widget === 'boolean_favorite' || item.field.name === 'is_favorite');
  const fieldNodes = mappedNodes
    .filter((item) => item !== favoriteNode)
    .map((item) => item.field);
  if (input.orderActive && input.fieldOrder.length) {
    const rank = new Map(input.fieldOrder.map((fieldName, order) => [fieldName, order]));
    fieldNodes.sort((left, right) => {
      const leftRank = rank.get(left.name) ?? Number.MAX_SAFE_INTEGER;
      const rightRank = rank.get(right.name) ?? Number.MAX_SAFE_INTEGER;
      return leftRank - rightRank;
    });
  }
  const schemas = input.applyReadonlyValues(input.buildSchemas(fieldNodes));
  if (!favoriteNode || !schemas.length) return schemas;
  const target = schemas.find((field) => field.name === 'name')
    || schemas.find((field) => ['char', 'text'].includes(String(field.type || '').trim().toLowerCase()))
    || schemas[0];
  if (target) {
    target.favoriteToggle = {
      name: favoriteNode.field.name,
      label: favoriteNode.field.label || favoriteNode.field.name,
      active: input.favoriteActive(favoriteNode.field.name),
      readonly: input.favoriteReadonly(favoriteNode.field),
      descriptor: favoriteNode.field.descriptor,
    };
  }
  return schemas;
}

export function schemaInputValueFromRaw(fieldType: string, raw: unknown) {
  const type = String(fieldType || '').trim().toLowerCase();
  if (type === 'many2one') {
    const id = normalizeRelationIds(raw)[0];
    return id ? String(id) : '';
  }
  if (raw === null || raw === undefined || raw === false) return '';
  if (type === 'date') return toDateInputValue(raw);
  if (type === 'datetime') return toDatetimeInputValue(raw);
  if (typeof raw === 'number' || typeof raw === 'boolean') return raw;
  return String(raw);
}

export function applyReadonlyFieldValues(
  schemas: FormSectionFieldSchema[],
  resolveFieldValue: ReadonlyFieldValueResolver,
): FormSectionFieldSchema[] {
  return schemas.map((field) => {
    if (!field.readonly) return field;
    const resolved = resolveFieldValue(field.name);
    if (!resolved.found) return field;
    return {
      ...field,
      value: resolved.value,
      inputValue: schemaInputValueFromRaw(String(field.type || ''), resolved.value),
    };
  });
}

export function shouldShowRequiredMark(input: RequiredMarkInput) {
  const node = input.node;
  if (node.kind !== 'field' || node.readonly) return false;
  if (!node.required) return false;
  if (input.showHud) return true;
  if (input.renderProfile !== 'create') return true;
  if (input.policyRequiredFields.size || input.validationRequiredFields.size) {
    return input.policyRequiredFields.has(node.name) || input.validationRequiredFields.has(node.name);
  }
  return input.coreFieldNames.includes(node.name);
}

export function isNativeFieldVisible(input: NativeFieldVisibilityInput) {
  const normalized = String(input.name || '').trim();
  if (!normalized) return false;
  if (input.node && !input.isNodeVisible(input.node)) return false;
  const statusField = String(input.statusField || '').trim();
  if (statusField && normalized === statusField) return false;
  if (normalized === 'message_needaction') return false;
  const semantic = input.semantic(normalized);
  if ((semantic.technical || semantic.semantic_type === 'technical') && !input.showHud) return false;
  if (semantic.surface_role === 'hidden' && !input.showHud) return false;
  const state = input.runtimeState(normalized);
  if (state.invisible) return false;
  const descriptor = input.resolveDescriptor(normalized, input.node);
  if (!descriptor) return false;
  if (isCreateWorkflowStateField(
    normalized,
    nativeFieldLabel(input.node || {}, descriptor, input.resolveFieldLabel),
    input.isCreate,
  )) return false;
  const resolved = input.evaluatePolicy(normalized, descriptor);
  if (resolved.visible) return true;
  // Native layout is already a backend-scoped form contract. Do not re-apply
  // the legacy core/advanced create-mode filter here, otherwise fields in
  // later notebook pages disappear even though the action-bound view exposes
  // them explicitly. Explicit invisible/status rules are handled above.
  if (input.node) return true;
  return input.renderProfile === 'create' && semantic.surface_role === 'advanced';
}

export function isNativeLayoutNodeVisible(input: NativeLayoutNodeVisibilityInput) {
  const nodeRaw = input.node;
  if (input.evaluateModifier(nativeModifierValue(nodeRaw, 'invisible'))) return false;
  const node = nodeRaw as Record<string, unknown>;
  const nodeType = String(node.type || '').trim().toLowerCase();
  if (node.visible === false && !(input.editable && nodeType === 'group')) return false;
  if (nodeType === 'group') {
    const title = input.normalizeGroupTitle(node.string || node.label || node.title);
    if (title && !input.isGroupVisible(title) && !input.editable) return false;
  }
  const fieldName = String(nodeRaw.name || '').trim();
  if (
    nodeType === 'field'
    && fieldName
    && input.isFieldVisibleInDraft(fieldName) === false
    && !input.editable
  ) {
    return false;
  }
  if (nodeType === 'button') {
    return Boolean(input.resolveAction(node));
  }
  return true;
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
