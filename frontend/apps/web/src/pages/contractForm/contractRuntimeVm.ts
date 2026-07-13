import type { ContractAction } from './types';
import {
  collectUnifiedPageContractV2FieldWidgets,
  resolveUnifiedPageContractV2,
  resolveUnifiedPageContractV2FieldGroups,
  resolveUnifiedPageContractV2VisibleFields,
} from '../../app/contracts/unifiedPageContractV2';
import { viewTypeDisplayLabel } from './fieldUtils';
import { normalizeRouteDefault } from './valueUtils';

function recordOrEmpty(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

export type FormContractReadiness = {
  usable: boolean;
  issues: string[];
  fieldCount: number;
  layoutFieldCount: number;
  visibleCandidateCount: number;
};

export function analyzeFormContractReadiness(
  data: unknown,
  options?: { requirePureFormViewType?: boolean },
): FormContractReadiness {
  const issues: string[] = [];
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return { usable: false, issues: ['contract payload is not an object'], fieldCount: 0, layoutFieldCount: 0, visibleCandidateCount: 0 };
  }
  const row = data as Record<string, unknown>;
  const requirePureFormViewType = options?.requirePureFormViewType !== false;
  const collectLayoutFieldNames = (layoutRaw: unknown): Set<string> => {
    const names = new Set<string>();
    type LayoutGroupLike = { fields?: Array<Record<string, unknown>>; sub_groups?: LayoutGroupLike[] };
    type LayoutPageLike = { groups?: LayoutGroupLike[] };
    type LayoutNotebookLike = { pages?: LayoutPageLike[] };

    const walkStructuredGroup = (groupRaw: unknown) => {
      if (!groupRaw || typeof groupRaw !== 'object' || Array.isArray(groupRaw)) return;
      const group = groupRaw as LayoutGroupLike;
      const fields = Array.isArray(group.fields) ? group.fields : [];
      fields.forEach((fieldRaw) => {
        const field = fieldRaw && typeof fieldRaw === 'object' ? fieldRaw : {};
        const fieldName = String((field as Record<string, unknown>).name || '').trim();
        if (fieldName) names.add(fieldName);
      });
      const subGroups = Array.isArray(group.sub_groups) ? group.sub_groups : [];
      subGroups.forEach((sub) => walkStructuredGroup(sub));
    };

    const walkLegacyNode = (nodeRaw: unknown) => {
      if (Array.isArray(nodeRaw)) {
        nodeRaw.forEach((item) => walkLegacyNode(item));
        return;
      }
      if (!nodeRaw || typeof nodeRaw !== 'object') return;
      const node = nodeRaw as Record<string, unknown>;
      const kind = String(node.type || '').trim().toLowerCase();
      if (kind === 'field') {
        const fieldName = String(node.name || '').trim();
        if (fieldName) names.add(fieldName);
      }
      ['children', 'tabs', 'pages', 'nodes', 'items'].forEach((key) => walkLegacyNode(node[key]));
    };

    if (Array.isArray(layoutRaw)) {
      walkLegacyNode(layoutRaw);
      return names;
    }
    if (!layoutRaw || typeof layoutRaw !== 'object') return names;

    const layout = layoutRaw as Record<string, unknown>;
    const groups = Array.isArray(layout.groups) ? layout.groups : [];
    groups.forEach((group) => walkStructuredGroup(group));
    const notebooks = Array.isArray(layout.notebooks) ? layout.notebooks : [];
    notebooks.forEach((notebookRaw) => {
      const notebook = notebookRaw && typeof notebookRaw === 'object' && !Array.isArray(notebookRaw)
        ? notebookRaw as LayoutNotebookLike
        : null;
      const pages = Array.isArray(notebook?.pages) ? notebook.pages : [];
      pages.forEach((pageRaw) => {
        const page = pageRaw && typeof pageRaw === 'object' && !Array.isArray(pageRaw)
          ? pageRaw as LayoutPageLike
          : null;
        const pageGroups = Array.isArray(page?.groups) ? page.groups : [];
        pageGroups.forEach((group) => walkStructuredGroup(group));
      });
    });

    if (!names.size) walkLegacyNode(layoutRaw);
    return names;
  };

  const v2 = resolveUnifiedPageContractV2(row);
  const v2FieldNames = collectUnifiedPageContractV2FieldWidgets(row)
    .map((widget) => String(widget.fieldCode || '').trim())
    .filter(Boolean);
  const v2FieldNameSet = new Set(v2FieldNames);
  const fields = row.fields;
  const fieldMap = fields && typeof fields === 'object' && !Array.isArray(fields)
    ? fields as Record<string, unknown>
    : {};
  const fieldNames = Array.from(new Set([...Object.keys(fieldMap), ...v2FieldNames]));
  if (!fieldNames.length) issues.push('contract.fields is empty');

  const views = row.views;
  const formView = views && typeof views === 'object' && !Array.isArray(views)
    ? (views as Record<string, unknown>).form
    : undefined;
  const hasV2Form = v2?.pageInfo?.viewType === 'form' && v2FieldNames.length > 0;
  if (!hasV2Form && (!formView || typeof formView !== 'object' || Array.isArray(formView))) {
    issues.push('contract.views.form is missing');
  }
  const layout = formView && typeof formView === 'object' && !Array.isArray(formView)
    ? (formView as Record<string, unknown>).layout
    : {};
  const layoutFieldNames = collectLayoutFieldNames(layout);

  const head = row.head;
  const headViewType = head && typeof head === 'object' && !Array.isArray(head)
    ? String((head as Record<string, unknown>).view_type || '').trim().toLowerCase()
    : '';
  const viewType = String(row.view_type || '').trim().toLowerCase();
  const v2ViewType = String(v2?.pageInfo?.viewType || '').trim().toLowerCase();
  if (requirePureFormViewType) {
    if (headViewType && headViewType !== 'form') issues.push(`页面头部视图为 ${viewTypeDisplayLabel(headViewType)}，应为表单视图`);
    if (viewType && viewType !== 'form') issues.push(`页面视图为 ${viewTypeDisplayLabel(viewType)}，应为表单视图`);
    if (v2ViewType && v2ViewType !== 'form') issues.push(`页面结构视图为 ${viewTypeDisplayLabel(v2ViewType)}，应为表单视图`);
  }

  const visible = resolveUnifiedPageContractV2VisibleFields(row);
  const visibleNameSet = new Set(visible);
  const groupNames = new Set<string>();
  resolveUnifiedPageContractV2FieldGroups(row).forEach((item) => {
    if (!item || typeof item !== 'object') return;
    const fieldsRaw = (item as Record<string, unknown>).fields;
    if (!Array.isArray(fieldsRaw)) return;
    fieldsRaw.forEach((name) => {
      const normalized = String(name || '').trim();
      if (normalized) groupNames.add(normalized);
    });
  });
  v2FieldNames.forEach((name) => layoutFieldNames.add(name));
  if (!layoutFieldNames.size && !groupNames.size && !visibleNameSet.size) {
    issues.push('contract.views.form.layout has no field nodes');
  }
  const visibleCandidates = fieldNames.filter((name) =>
    visibleNameSet.has(name) || groupNames.has(name) || layoutFieldNames.has(name) || v2FieldNameSet.has(name),
  );
  if (fieldNames.length && !visibleCandidates.length) {
    issues.push('no visible field candidate from visible_fields/field_groups/layout');
  }

  return {
    usable: issues.length === 0,
    issues,
    fieldCount: fieldNames.length,
    layoutFieldCount: layoutFieldNames.size,
    visibleCandidateCount: visibleCandidates.length,
  };
}

export function validateSurfaceMarkers(
  data: unknown,
  meta: Record<string, unknown> | null,
  expectedSurface: 'user' | 'native' | 'hud',
) {
  const issues: string[] = [];
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return { ok: false, issues: ['contract payload is not an object'] };
  }
  const row = data as Record<string, unknown>;
  const contractSurface = String(row.contract_surface || '').trim().toLowerCase();
  const renderMode = String(row.render_mode || '').trim().toLowerCase();
  const sourceMode = String(row.source_mode || '').trim().toLowerCase();
  const governedFromNative = row.governed_from_native;
  const surfaceMapping = row.surface_mapping;
  const metaSurface = String(meta?.contract_surface || '').trim().toLowerCase();

  if (!contractSurface) issues.push('missing contract_surface');
  if (!renderMode) issues.push('missing render_mode');
  if (!sourceMode) issues.push('missing source_mode');
  if (typeof governedFromNative !== 'boolean') issues.push('missing governed_from_native');
  if (!surfaceMapping || typeof surfaceMapping !== 'object' || Array.isArray(surfaceMapping)) {
    issues.push('missing surface_mapping');
  }

  if (metaSurface && contractSurface && metaSurface !== contractSurface) {
    issues.push(`meta.contract_surface=${metaSurface} mismatch data.contract_surface=${contractSurface}`);
  }
  if (contractSurface && contractSurface !== expectedSurface) {
    issues.push(`contract_surface=${contractSurface} mismatch expected=${expectedSurface}`);
  }

  if (contractSurface === 'native') {
    if (renderMode !== 'native') issues.push(`native surface requires render_mode=native, got ${renderMode || '-'}`);
    if (governedFromNative !== false) issues.push('native surface requires governed_from_native=false');
  } else if (contractSurface === 'user' || contractSurface === 'hud') {
    if (renderMode !== 'governed') issues.push(`governed surface requires render_mode=governed, got ${renderMode || '-'}`);
    if (governedFromNative !== true) issues.push('governed surface requires governed_from_native=true');
  }

  return { ok: issues.length === 0, issues };
}

export function contractModelName(data: unknown) {
  const row = recordOrEmpty(data);
  const head = recordOrEmpty(row.head);
  return String(head.model || row.model || '').trim();
}

export function buildRouteContractContext(routeQuery: Record<string, unknown>) {
  const context: Record<string, unknown> = {};
  Object.entries(routeQuery).forEach(([key, value]) => {
    if (key.startsWith('default_')) context[key] = normalizeRouteDefault(value);
  });
  [
    'current_business_category_code',
    'default_business_category_code',
    'allowed_business_category_codes',
    'current_business_category_label',
    'default_business_category_label',
  ].forEach((key) => {
    const value = routeQuery[key];
    if (value === undefined || value === null || value === '') return;
    if (Array.isArray(value)) {
      const items = value.map((item) => String(item || '').trim()).filter((item) => item !== '');
      if (items.length) context[key] = items;
      return;
    }
    const text = String(value).trim();
    if (text) context[key] = text;
  });
  const intakeMode = String(routeQuery.intake_mode || '').trim().toLowerCase();
  if (intakeMode === 'quick' || intakeMode === 'standard') context.intake_mode = intakeMode;
  return context;
}

export function collectRuntimeCapabilities(session: {
  capabilities?: unknown[];
  capabilityCatalog?: Record<string, { key?: unknown; state?: unknown; capability_state?: unknown }>;
}) {
  const out = new Set<string>();
  (session.capabilities || []).forEach((key) => {
    const normalized = String(key || '').trim();
    if (normalized) out.add(normalized);
  });
  Object.values(session.capabilityCatalog || {}).forEach((meta) => {
    const key = String(meta?.key || '').trim();
    if (!key) return;
    const state = String(meta?.state || '').trim().toUpperCase();
    const capState = String(meta?.capability_state || '').trim().toLowerCase();
    if (state === 'LOCKED' || capState === 'deny') return;
    out.add(key);
  });
  return out;
}

export function collectRuntimeUserGroups(user: { groups_xmlids?: unknown } | null | undefined) {
  return Array.isArray(user?.groups_xmlids)
    ? user.groups_xmlids.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
}

export function normalizeContractWarnings(rows: unknown) {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => {
      if (typeof row === 'string') return row;
      if (row && typeof row === 'object') {
        return String((row as Record<string, unknown>).message || (row as Record<string, unknown>).code || '');
      }
      return '';
    })
    .map((item) => item.trim())
    .filter((item) => Boolean(item) && !item.startsWith('access_policy:'));
}

export function normalizeSearchFilters(rows: unknown) {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => {
      const item = row && typeof row === 'object' && !Array.isArray(row)
        ? row as Record<string, unknown>
        : {};
      return {
        key: String(item.key || '').trim(),
        label: String(item.label || item.key || '').trim(),
        domainRaw: String(item.domain_raw || '').trim(),
        contextRaw: String(item.context_raw || '').trim(),
      };
    })
    .filter((row) => row.key && row.label);
}

export function collectPrimaryActionRequiredFields(actionPolicies: unknown) {
  const out = new Set<string>();
  const map = recordOrEmpty(actionPolicies) as Record<string, { semantic?: string; enabled_when?: { required_fields?: string[] } }>;
  Object.values(map).forEach((policy) => {
    const semantic = String(policy?.semantic || '').trim().toLowerCase();
    if (semantic !== 'primary_action') return;
    const requiredFields = Array.isArray(policy?.enabled_when?.required_fields)
      ? policy.enabled_when.required_fields
      : [];
    requiredFields.forEach((field) => {
      const normalized = String(field || '').trim();
      if (normalized) out.add(normalized);
    });
  });
  return out;
}

export function resolveBusinessCategoryContext(params: {
  contractRecord: unknown;
  routeQuery: Record<string, unknown>;
  relationBusinessCategoryLabel: string;
}) {
  const contractRecord = recordOrEmpty(params.contractRecord);
  const head = recordOrEmpty(contractRecord.head);
  const headContext = recordOrEmpty(head.context);
  const contractContext = recordOrEmpty(contractRecord.context);
  const query = params.routeQuery;
  return {
    label: String(
      query.current_business_category_label
      || query.default_business_category_label
      || headContext.current_business_category_label
      || headContext.default_business_category_label
      || contractContext.current_business_category_label
      || contractContext.default_business_category_label
      || params.relationBusinessCategoryLabel
      || '',
    ).trim(),
    code: String(
      query.current_business_category_code
      || query.default_business_category_code
      || headContext.current_business_category_code
      || headContext.default_business_category_code
      || contractContext.current_business_category_code
      || contractContext.default_business_category_code
      || '',
    ).trim(),
  };
}

export function buildWorkflowTransitions(params: {
  rows: unknown;
  actions: ContractAction[];
  profile: 'create' | 'edit' | 'readonly';
  showHud: boolean;
}) {
  if (!Array.isArray(params.rows)) return [];
  if (params.profile === 'create') return [];
  const headerActionKeys = new Set(
    params.actions
      .filter((item) => item.level === 'header' || item.level === 'toolbar')
      .map((item) => item.key),
  );
  const transitions = params.rows.map((raw, idx) => {
    const row = raw && typeof raw === 'object' && !Array.isArray(raw)
      ? raw as Record<string, { label?: unknown; name?: unknown; kind?: unknown } | unknown>
      : {};
    const trigger = row.trigger && typeof row.trigger === 'object' && !Array.isArray(row.trigger)
      ? row.trigger as Record<string, unknown>
      : {};
    const triggerLabel = String(trigger.label || '').trim();
    const triggerName = String(trigger.name || '').trim();
    const triggerKind = String(trigger.kind || '').trim().toLowerCase();
    const action = params.actions.find((item) => {
      if (triggerKind && item.kind && item.kind !== triggerKind) return false;
      if (triggerName && (item.methodName === triggerName || item.key.includes(triggerName))) return true;
      if (triggerLabel && item.label === triggerLabel) return true;
      return false;
    }) || null;
    return {
      key: `wf_${idx}`,
      label: triggerLabel || triggerName || `transition_${idx + 1}`,
      notes: String(row.notes || ''),
      action,
    };
  });
  if (params.showHud) return transitions;
  return transitions.filter((item) => {
    const label = String(item.label || '').trim();
    if (!item.action) return false;
    if (item.action?.key && headerActionKeys.has(item.action.key)) return false;
    if (/^\d+$/.test(label)) return false;
    return true;
  });
}
