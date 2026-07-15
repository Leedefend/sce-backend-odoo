import type { ActionContract } from '@sc/schema';
import type { IntentRawResult } from '../../api/intents';
import {
  collectUnifiedPageContractV2FieldWidgets,
  resolveUnifiedPageContractV2BusinessOperationProfile,
  resolveUnifiedPageContractV2DeletePolicy,
  resolveUnifiedPageContractV2FieldGroups,
  resolveUnifiedPageContractV2FormStructureContract,
  resolveUnifiedPageContractV2GlobalStatus,
  resolveUnifiedPageContractV2ListProfile,
  resolveUnifiedPageContractV2MainData,
  resolveUnifiedPageContractV2SourceContext,
  resolveUnifiedPageContractV2SurfacePolicies,
  resolveUnifiedPageContractV2VisibleFields,
  type UnifiedPageContractV2Widget,
} from '../contracts/unifiedPageContractV2';

type Dict = Record<string, unknown>;
type ProjectionContractRawResult = IntentRawResult<ActionContract & Dict>;

function asDict(value: unknown): Dict {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Dict : {};
}

function asList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function resolveV2SourceContext(v2Contract: unknown): Dict {
  const root = asDict(v2Contract);
  const dataContract = asDict(root.dataContract);
  const dataMeta = asDict(dataContract.dataMeta);
  const runtime = asDict(root.runtimeContract);
  return asDict(dataMeta.sourceContext || runtime.sourceContext);
}

function resolveV2SearchContract(v2Contract: unknown): Dict {
  const root = asDict(v2Contract);
  const dataContract = asDict(root.dataContract);
  const dataMeta = asDict(dataContract.dataMeta);
  return asDict(root.searchContract || root.search || dataContract.search || dataMeta.search);
}

function resolveV2CollaborationContract(v2Contract: unknown): Dict {
  const root = asDict(v2Contract);
  const runtime = asDict(root.runtimeContract);
  return asDict(runtime.collaboration);
}

function stableFieldName(name: string) {
  return String(name || '').trim();
}

function uniqueFields(fields: string[]) {
  const seen = new Set<string>();
  return fields.filter((field) => {
    const name = String(field || '').trim();
    if (!name || seen.has(name)) return false;
    seen.add(name);
    return true;
  });
}

function inferFieldType(widget: UnifiedPageContractV2Widget, mainData: Dict): string {
  const widgetType = String(widget.widgetType || '').trim().toLowerCase();
  const componentConfig = asDict(widget.componentConfig);
  const explicitFieldType = String(widget.fieldType || componentConfig.fieldType || componentConfig.ttype || '').trim().toLowerCase();
  if (explicitFieldType) return explicitFieldType;
  const fieldName = stableFieldName(widget.fieldCode);
  const value = mainData[fieldName];
  if (widgetType === 'date' || widgetType === 'datetime') return widgetType;
  if (widgetType === 'textarea') return 'text';
  if (widgetType === 'select') return 'many2one';
  if (widgetType === 'many2many_tags') return 'many2many';
  if (widgetType === 'table') return Array.isArray(value) ? 'one2many' : 'many2many';
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return Number.isInteger(value) ? 'integer' : 'float';
  if (Array.isArray(value)) return fieldName.endsWith('_ids') ? 'many2many' : 'one2many';
  if (fieldName.endsWith('_id')) return 'many2one';
  return 'char';
}

function buildLegacyFieldDescriptor(widget: UnifiedPageContractV2Widget, mainData: Dict): Dict {
  const name = stableFieldName(widget.fieldCode);
  const type = inferFieldType(widget, mainData);
  const value = mainData[name];
  const componentConfig = asDict(widget.componentConfig);
  const readonly = componentConfig.readonly === true;
  const required = componentConfig.required === true;
  const componentRelation = String(componentConfig.relation || widget.relation || '').trim();
  const relation = ['many2one', 'one2many', 'many2many'].includes(type) ? componentRelation : '';
  const relationField = String(componentConfig.relation_field || componentConfig.relationField || '').trim();
  const relationEntry = asDict(componentConfig.relationEntry || componentConfig.relation_entry);
  const descriptor: Dict = {
    name,
    string: widget.label || name,
    label: widget.label || name,
    type,
    ttype: type,
    widget: widget.widgetType || '',
    readonly,
    required,
    optional: componentConfig.optional === true,
    invisible: componentConfig.invisible === true,
    column_invisible: componentConfig.column_invisible === true,
  };
  if (relation) {
    descriptor.relation = relation;
  }
  if (relationField) {
    descriptor.relation_field = relationField;
  }
  if (Object.keys(relationEntry).length) {
    descriptor.relation_entry = relationEntry;
  }
  const selection = Array.isArray(componentConfig.selection)
    ? componentConfig.selection
    : Array.isArray(value)
      ? value
      : [];
  if (type === 'selection' && selection.length) {
    descriptor.selection = selection;
  }
  return descriptor;
}

function buildLegacyFormLayout(fieldWidgets: UnifiedPageContractV2Widget[], fieldLabels: Record<string, string>): Dict[] {
  return [{
    type: 'sheet',
    string: 'sheet',
    children: [{
      type: 'group',
      string: 'group',
      children: fieldWidgets.map((widget) => ({
        type: 'field',
        name: stableFieldName(widget.fieldCode),
        string: fieldLabels[stableFieldName(widget.fieldCode)] || widget.label || widget.fieldCode,
      })),
    }],
  }];
}

function walkV2LayoutNodes(rows: unknown[], visit: (row: Dict) => void) {
  (Array.isArray(rows) ? rows : []).forEach((item) => {
    const row = asDict(item);
    if (!Object.keys(row).length) return;
    visit(row);
    for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
      walkV2LayoutNodes(asList(row[key]), visit);
    }
  });
}

function collectV2LayoutButtons(v2Contract: Dict): Dict[] {
  const out: Dict[] = [];
  const seen = new Set<string>();
  const root = asDict(v2Contract);
  const mainData = asDict(asDict(root.dataContract).mainData);
  const layoutContract = asDict(root.layoutContract);
  const findCountField = (shortLabel: string): string => {
    let countField = '';
    walkV2LayoutNodes(asList(layoutContract.containerTree), (row) => {
      if (countField) return;
      if (String(row.type || row.kind || '').trim().toLowerCase() !== 'field') return;
      const fieldInfo = asDict(row.fieldInfo || row.field_info);
      const fieldType = String(fieldInfo.type || '').trim().toLowerCase();
      if (!['one2many', 'many2many'].includes(fieldType)) return;
      const label = String(row.label || row.string || fieldInfo.label || row.name || '').trim();
      const name = String(row.name || '').trim();
      if (label.includes(shortLabel) || name.includes(shortLabel)) {
        countField = name;
      }
    });
    return countField;
  };
  walkV2LayoutNodes(asList(layoutContract.containerTree), (row) => {
    const nodeType = String(row.type || row.kind || '').trim().toLowerCase();
    if (nodeType !== 'button') return;
    const action = asDict(row.action);
    const payload = asDict(action.payload);
    const key = stableFieldName(String(action.name || row.key || row.name || row.label || ''));
    if (!key || seen.has(key)) return;
    seen.add(key);
    const level = String(action.level || row.level || 'body').trim().toLowerCase();
    const kind = String(action.kind || row.buttonType || '').trim().toLowerCase();
    const rawLabel = String(action.label || row.label || row.string || key).trim() || key;
    let label = rawLabel;
    if (level === 'smart' && rawLabel.endsWith('管理')) {
      const shortLabel = rawLabel.replace(/管理$/, '').trim();
      const countField = findCountField(shortLabel);
      const count = countField && Array.isArray(mainData[countField]) ? mainData[countField].length : null;
      if (count !== null) {
        label = `${count}${shortLabel || rawLabel}`;
      }
    }
    out.push({
      key,
      name: key,
      label,
      kind: kind === 'server' ? 'server' : kind === 'open' ? 'object' : 'object',
      level,
      selection: 'none',
      actionId: null,
      methodName: String(payload.method || '').trim() || key,
      targetModel: '',
      context: {},
      domainRaw: String(payload.domain_raw || '').trim(),
      target: String(payload.target || '').trim(),
      url: String(payload.url || '').trim(),
      enabled: true,
      hint: '',
      semantic: level === 'smart' ? 'secondary_action' : 'primary_action',
      visibleProfiles: Array.isArray(action.visible_profiles) ? action.visible_profiles : ['create', 'edit', 'readonly'],
      requiredParams: [],
      requiresReason: false,
      actionSafety: action.action_safety,
    });
  });
  const actionRules = asList(asDict(asDict(root.actionContract).actionRuleList));
  actionRules.forEach((raw) => {
    const row = asDict(raw);
    const sourceWidgetId = String(row.sourceWidgetId || row.source_widget_id || '').trim();
    if (sourceWidgetId !== 'page.header') return;
    const triggerType = String(row.triggerType || row.trigger_type || '').trim();
    if (triggerType && triggerType !== 'click') return;
    const key = stableFieldName(String(row.actionKey || row.key || row.actionId || ''));
    if (!key || seen.has(key)) return;
    seen.add(key);
    const target = asDict(row.target);
    const clientMode = String(target.mode || target.client_mode || '').trim();
    const level = 'header';
    out.push({
      key,
      name: key,
      label: String(row.label || key).trim() || key,
      kind: clientMode ? 'client' : 'open',
      intent: String(row.intent || '').trim(),
      level,
      selection: 'none',
      actionId: Number(target.action_id || 0) || null,
      methodName: '',
      targetModel: String(target.model || '').trim(),
      context: {},
      domainRaw: String(target.domain_raw || '').trim(),
      target: String(target.target || '').trim(),
      url: String(target.url || target.route || '').trim(),
      payload: {
        mode: clientMode,
        client_mode: clientMode,
      },
      enabled: true,
      hint: '',
      semantic: 'secondary_action',
      sourceWidgetId,
      visibleProfiles: ['create', 'edit', 'readonly'],
      requiredParams: [],
      requiresReason: false,
    });
  });
  return out;
}

function collectV2Statusbar(v2Contract: Dict): Dict | null {
  const root = asDict(v2Contract);
  const layoutContract = asDict(root.layoutContract);
  let statusField = '';
  let states: Array<{ value: string; label: string }> = [];
  walkV2LayoutNodes(asList(layoutContract.containerTree), (row) => {
    if (statusField) return;
    if (String(row.type || row.kind || '').trim().toLowerCase() !== 'field') return;
    const name = stableFieldName(String(row.name || row.field || ''));
    if (!['lifecycle_state', 'state', 'stage_id'].includes(name)) return;
    const fieldInfo = asDict(row.fieldInfo || row.field_info);
    const selection = Array.isArray(fieldInfo.selection) ? fieldInfo.selection : [];
    const mapped = selection.map((item) => {
      const pair = Array.isArray(item) ? item : [];
      return {
        value: String(pair[0] ?? '').trim(),
        label: String(pair[1] ?? pair[0] ?? '').trim(),
      };
    }).filter((item) => item.value && item.label);
    if (!mapped.length) return;
    statusField = name;
    states = mapped;
  });
  if (!statusField || !states.length) return null;
  return { field: statusField, states };
}

function buildLegacySubViews(fieldWidgets: UnifiedPageContractV2Widget[], mainData: Dict): Dict {
  const out: Dict = {};
  fieldWidgets.forEach((widget) => {
    const fieldName = stableFieldName(widget.fieldCode);
    const type = inferFieldType(widget, mainData);
    if (type !== 'one2many' && type !== 'many2many') return;
    const componentConfig = asDict(widget.componentConfig);
    const subview = asDict(componentConfig.subview || componentConfig.subView);
    if (Object.keys(subview).length) {
      out[fieldName] = subview;
      return;
    }
    out[fieldName] = {
      tree: { columns: ['display_name'] },
      policies: {
        inline_edit: true,
        can_create: true,
        can_unlink: true,
        ui_labels: {
          add_row: '添加行',
          remove: '移除',
          restore: '撤销',
        },
      },
    };
  });
  return out;
}

function buildSurfaceMapping(surface: string, renderMode: string, sourceMode: string) {
  return {
    contract_surface: surface,
    render_mode: renderMode,
    source_mode: sourceMode,
    governed_from_native: surface !== 'native',
  };
}

function resolveV2DeletePolicy(v2Contract: Dict, model: string): Dict {
  const targetModel = String(model || '').trim();
  if (!targetModel) return {};
  const topLevel = resolveUnifiedPageContractV2DeletePolicy(v2Contract);
  if (Object.keys(topLevel).length && (!String(topLevel.model || '').trim() || String(topLevel.model || '').trim() === targetModel)) {
    return topLevel;
  }
  return {};
}

function buildRuntimeProjectionFromV2(v2Contract: Dict, requestParams: Dict = {}): Dict {
  const pageInfo = asDict(v2Contract.pageInfo);
  const sourceContext = resolveV2SourceContext(v2Contract);
  const renderProfile = String(sourceContext.renderProfile || sourceContext.render_profile || '').trim();
  const v2Fields = collectUnifiedPageContractV2FieldWidgets(v2Contract);
  const v2PrimarySource = asDict(asDict(asDict(v2Contract.dataContract).dataSource).primary);
  const v2PrimaryParams = asDict(v2PrimarySource.params);
  const v2PrimaryFields = Array.isArray(v2PrimaryParams.fields)
    ? (v2PrimaryParams.fields as unknown[]).map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  const mainData = resolveUnifiedPageContractV2MainData(v2Contract);
  const v2SourceContext = resolveUnifiedPageContractV2SourceContext(v2Contract);
  const v2SearchContract = resolveV2SearchContract(v2Contract);
  const v2Collaboration = resolveV2CollaborationContract(v2Contract);
  const v2Runtime = asDict(v2Contract.runtimeContract);
  const businessWorkspace = asDict(v2Runtime.businessWorkspace);
  const businessActions = asList(v2Runtime.businessActions).filter((item) => Object.keys(asDict(item)).length);
  const v2ListProfile = resolveUnifiedPageContractV2ListProfile(v2Contract);
  const sourceListProfile = v2ListProfile;
  const formalFieldGroups = resolveUnifiedPageContractV2FieldGroups(v2Contract);
  const formalVisibleFields = resolveUnifiedPageContractV2VisibleFields(v2Contract);
  const formalBusinessProfile = resolveUnifiedPageContractV2BusinessOperationProfile(v2Contract);
  const formalFormStructureContract = resolveUnifiedPageContractV2FormStructureContract(v2Contract);
  const globalStatus = resolveUnifiedPageContractV2GlobalStatus(v2Contract);
  const workflowContract = Object.keys(asDict(v2Contract.workflowContract)).length
    ? asDict(v2Contract.workflowContract)
    : asDict(asDict(v2Contract.runtimeContract).workflowContract);
  const layoutButtons = collectV2LayoutButtons(v2Contract);
  const statusbar = collectV2Statusbar(v2Contract);
  const model = String(pageInfo.model || '').trim();
  const viewType = String(pageInfo.viewType || requestParams.view_type || 'form').trim() || 'form';
  const contractSurface = String(requestParams.contract_surface || requestParams.surface || 'user').trim().toLowerCase() || 'user';
  const sourceMode = String(requestParams.source_mode || '').trim() || 'governance_pipeline';
  const renderMode = contractSurface === 'native' ? 'native' : 'governed';
  const fieldLabels = v2Fields.reduce<Record<string, string>>((acc, widget) => {
    const fieldName = stableFieldName(widget.fieldCode);
    if (fieldName) acc[fieldName] = widget.label || fieldName;
    return acc;
  }, {});
  const fallbackListColumns = uniqueFields(v2PrimaryFields.filter((name) => name !== 'id'));
  if (!v2Fields.length && fallbackListColumns.length && (viewType === 'list' || viewType === 'tree')) {
    const fallbackListLabels: Record<string, string> = {
      name: '名称',
      project_code: '编号',
      operation_strategy: '经营方式',
      business_nature: '经营性质',
      lifecycle_state: '状态',
      manager_id: '负责人',
      write_date: '更新时间',
    };
    fallbackListColumns.forEach((name) => {
      if (!fieldLabels[name]) {
        fieldLabels[name] = fallbackListLabels[name] || name;
      }
    });
  }
  const fields = v2Fields.reduce<Record<string, Dict>>((acc, widget) => {
    const descriptor = buildLegacyFieldDescriptor(widget, mainData);
    if (descriptor.name) {
      acc[descriptor.name as string] = descriptor;
    }
    return acc;
  }, {});
  if (!v2Fields.length && fallbackListColumns.length && (viewType === 'list' || viewType === 'tree')) {
    fallbackListColumns.forEach((name) => {
      if (fields[name]) return;
      fields[name] = {
        name,
        string: fieldLabels[name] || name,
        label: fieldLabels[name] || name,
        type: 'char',
        ttype: 'char',
        readonly: false,
        required: false,
      };
    });
  }
  const fieldNames = Object.keys(fields);
  const context = asDict(sourceContext.context);
  const head: Dict = {
    model,
    view_type: viewType,
    title: pageInfo.pageName,
    ...(renderProfile ? { render_profile: renderProfile } : {}),
    ...(Object.keys(context).length ? { context } : {}),
    permissions: {
      rights: {
        read: true,
        write: globalStatus?.pageAuth === 'read' ? false : true,
        create: globalStatus?.pageAuth === 'read' ? false : true,
        unlink: globalStatus?.pageAuth === 'read' ? false : true,
      },
    },
  };
  const rights = asDict(asDict(head.permissions).rights);
  const activeField = fieldNames.includes('active') ? 'active' : '';
  const writeAllowed = rights.write !== false;
  const unlinkRightAllowed = rights.unlink !== false;
  const deletePolicy = resolveV2DeletePolicy(v2Contract, model);
  const unlinkAllowed = deletePolicy.allowed === true && String(deletePolicy.delete_mode || '').trim().toLowerCase() === 'unlink';
  const sourceSurfacePolicies = resolveUnifiedPageContractV2SurfacePolicies(v2Contract);
  const sourceBatchPolicy = asDict(sourceSurfacePolicies.batch_policy);
  const sourceBatchActions = Array.isArray(sourceBatchPolicy.available_actions)
    ? sourceBatchPolicy.available_actions.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  let batchActions: string[] = [];
  if (sourceBatchActions.length) {
    batchActions = sourceBatchActions;
  } else {
    if (writeAllowed && activeField) {
      batchActions.push('archive', 'activate');
    }
    if (unlinkRightAllowed && unlinkAllowed) {
      batchActions.push('delete');
    }
  }
  const batchPolicy = {
    ...sourceBatchPolicy,
    enabled: sourceBatchPolicy.enabled === false ? false : batchActions.length > 0,
    active_field: String(sourceBatchPolicy.active_field || activeField || '').trim(),
    archive_value: Object.prototype.hasOwnProperty.call(sourceBatchPolicy, 'archive_value')
      ? sourceBatchPolicy.archive_value
      : (activeField ? false : null),
    activate_value: Object.prototype.hasOwnProperty.call(sourceBatchPolicy, 'activate_value')
      ? sourceBatchPolicy.activate_value
      : (activeField ? true : null),
    delete_mode: String(sourceBatchPolicy.delete_mode || (unlinkAllowed ? 'unlink' : 'none')).trim().toLowerCase(),
    available_actions: batchActions,
  };
  const formLayout = buildLegacyFormLayout(v2Fields, fieldLabels);
  const subviews = buildLegacySubViews(v2Fields, mainData);
  const v2Chatter = asDict(v2Collaboration.chatter);
  const v2Attachments = asDict(v2Collaboration.attachments);
  const chatterEnabled = Boolean(v2Chatter.enabled)
    || fieldNames.some((name) => ['message_ids', 'message_follower_ids', 'website_message_ids'].includes(name));
  const attachmentsEnabled = Boolean(v2Attachments.enabled)
    || fieldNames.some((name) => ['message_attachment_count', 'doc_count', 'attachment_ids'].includes(name));
  const formView = viewType === 'form'
    ? {
        layout: formLayout,
        fields: fieldNames,
        subviews,
        ...(statusbar ? { statusbar } : {}),
        ...(layoutButtons.length ? {
          header_buttons: layoutButtons.filter((item) => String(item.level || '').trim().toLowerCase() === 'header'),
          button_box: layoutButtons.filter((item) => String(item.level || '').trim().toLowerCase() === 'smart'),
          stat_buttons: layoutButtons.filter((item) => String(item.level || '').trim().toLowerCase() === 'smart'),
        } : {}),
        ui_labels: {
          reload: '刷新',
          discard: '放弃',
          save: '保存',
          cancel: '取消',
        },
        ...(Object.keys(businessWorkspace).length ? { business_workspace: businessWorkspace } : {}),
        ...(businessActions.length ? { business_actions: businessActions } : {}),
        ...(chatterEnabled ? {
          chatter: Object.keys(v2Chatter).length
            ? { ...v2Chatter, enabled: true }
            : { enabled: true, label: '沟通', actions: [] },
        } : {}),
        ...(attachmentsEnabled ? {
          attachments: {
            ...v2Attachments,
            enabled: true,
            upload: Object.keys(asDict(v2Attachments.upload)).length
              ? asDict(v2Attachments.upload)
              : { max_bytes: 25 * 1024 * 1024 },
            ui_labels: {
              label: '附件',
              upload: '上传附件',
              uploading: '上传中...',
              download: '下载',
              ...asDict(v2Attachments.ui_labels),
            },
          },
        } : {}),
      }
    : {
        layout: formLayout,
        fields: fieldNames,
        subviews,
        ui_labels: {
          reload: '刷新',
          discard: '放弃',
          save: '保存',
          cancel: '取消',
        },
      };
  return {
    model,
    view_type: viewType,
    render_profile: renderProfile || undefined,
    head,
    fields,
    views: {
      form: formView,
      ...(viewType !== 'form' ? { [viewType]: formView } : {}),
    },
    ...(Object.keys(v2SearchContract).length ? { search: v2SearchContract } : {}),
    visible_fields: formalVisibleFields.length ? formalVisibleFields : fieldNames,
    list_profile: Object.keys(sourceListProfile).length
      ? sourceListProfile
      : (
        !v2Fields.length
        && fallbackListColumns.length
        && (viewType === 'list' || viewType === 'tree')
      )
        ? {
          columns: fallbackListColumns,
          fact_columns: fallbackListColumns,
          hidden_columns: [],
          column_labels: fallbackListColumns.reduce<Record<string, string>>((acc, name) => {
            acc[name] = fieldLabels[name] || name;
            return acc;
          }, {}),
          row_primary: fallbackListColumns.includes('name') ? 'name' : fallbackListColumns[0] || '',
          row_secondary: '',
          preference_policy: {
            scope: 'ui_only',
            allow_visibility: true,
            allow_order: true,
            allow_width: true,
            locked_columns: [],
            must_request_columns: fallbackListColumns,
          },
          batch_policy: batchPolicy,
        }
        : undefined,
    field_groups: formalFieldGroups,
    ...(Object.keys(formalBusinessProfile).length ? { business_operation_profile: formalBusinessProfile } : {}),
    ...(Object.keys(formalFormStructureContract).length ? { form_structure_contract: formalFormStructureContract } : {}),
    contract_surface: contractSurface,
    render_mode: renderMode,
    source_mode: sourceMode,
    governed_from_native: contractSurface !== 'native',
    surface_policies: {
      delete_mode: batchPolicy.delete_mode,
      batch_policy: batchPolicy,
    },
    surface_mapping: buildSurfaceMapping(contractSurface, renderMode, sourceMode),
    ...(Object.keys(workflowContract).length ? {
      workflowContract,
      runtimeContract: { workflowContract },
    } : {}),
    __v2_main_data: mainData,
    __v2_source_context: v2SourceContext,
  };
}

export function adaptUnifiedPageContractV2Raw(result: IntentRawResult<Dict>, requestParams: Dict): ProjectionContractRawResult {
  const v2Contract = asDict(result.data);
  const projection = buildRuntimeProjectionFromV2(v2Contract, requestParams);
  const sourceContext = resolveV2SourceContext(v2Contract);
  const sourceContextRaw = asDict(sourceContext.context);
  const v2RenderProfile = String(sourceContext.renderProfile || sourceContext.render_profile || '').trim();
  const projectionHead = asDict(projection.head);
  const adaptedHead: Dict = {
    ...projectionHead,
    ...(!projectionHead.context && Object.keys(sourceContextRaw).length ? { context: sourceContextRaw } : {}),
    ...(!projectionHead.render_profile && v2RenderProfile ? { render_profile: v2RenderProfile } : {}),
  };
  const adaptedData = {
    ...projection,
    ...(Object.keys(adaptedHead).length ? { head: adaptedHead } : {}),
    ...(!projection.render_profile && v2RenderProfile ? { render_profile: v2RenderProfile } : {}),
    __v2_main_data: asDict(asDict(v2Contract.dataContract).mainData),
    __unified_page_contract_v2: v2Contract,
  } as ActionContract & Dict;
  return {
    ...result,
    data: adaptedData,
    meta: {
      ...result.meta,
      unified_page_contract_version: asDict(v2Contract.pageInfo).contractVersion,
      unified_page_contract_source: 'ui.contract.v2',
    },
    rawBody: {
      ...(asDict(result.rawBody)),
      data: adaptedData,
      unified_page_contract_v2: v2Contract,
    },
  };
}
