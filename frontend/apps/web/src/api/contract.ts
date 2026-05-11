import { intentRequestRaw, type IntentRawResult } from './intents';
import { ApiError } from './client';
import type { ActionContract } from '@sc/schema';
import { extractLiteContractFromIntentBody } from '../app/runtime/unifiedPageContractLitePilot';
import type { UnifiedPageContractLite } from '../app/contracts/unifiedPageContractLite';
import {
  collectUnifiedPageContractV2FieldWidgets,
  resolveUnifiedPageContractV2GlobalStatus,
  resolveUnifiedPageContractV2MainData,
  resolveUnifiedPageContractV2SourceContext,
  type UnifiedPageContractV2,
  type UnifiedPageContractV2Widget,
} from '../app/contracts/unifiedPageContractV2';

type LoadActionContractOptions = {
  recordId?: number | null;
  renderProfile?: 'create' | 'edit' | 'readonly' | null;
  surface?: 'user' | 'native' | 'hud' | null;
  sourceMode?: string | null;
};

type LoadModelContractOptions = LoadActionContractOptions & {
  viewType?: 'form' | 'tree' | 'kanban';
};

type Dict = Record<string, unknown>;
type ProjectionContractRawResult = IntentRawResult<ActionContract & Dict>;

function asDict(value: unknown): Dict {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Dict : {};
}

function resolveV2SourceContext(v2Contract: unknown): Dict {
  const root = asDict(v2Contract);
  const dataContract = asDict(root.dataContract);
  const dataMeta = asDict(dataContract.dataMeta);
  const runtime = asDict(root.runtimeContract);
  return asDict(dataMeta.sourceContext || runtime.sourceContext);
}

function stableFieldName(name: string) {
  return String(name || '').trim();
}

function guessRelationModel(fieldName: string, model: string): string {
  const normalized = stableFieldName(fieldName);
  const relationMap: Record<string, string> = {
    partner_id: 'res.partner',
    user_id: 'res.users',
    manager_id: 'res.users',
    company_id: 'res.company',
    country_id: 'res.country',
    currency_id: 'res.currency',
    project_id: 'project.project',
    task_id: 'project.task',
    parent_id: model,
  };
  return relationMap[normalized] || '';
}

function inferFieldType(widget: UnifiedPageContractV2Widget, mainData: Dict, model: string): string {
  const widgetType = String(widget.widgetType || '').trim().toLowerCase();
  const fieldName = stableFieldName(widget.fieldCode);
  const value = mainData[fieldName];
  if (widgetType === 'date' || widgetType === 'datetime') return widgetType;
  if (widgetType === 'textarea') return 'text';
  if (widgetType === 'select') return 'many2one';
  if (widgetType === 'table') return fieldName.endsWith('_ids') || Array.isArray(value) ? 'one2many' : 'many2many';
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return Number.isInteger(value) ? 'integer' : 'float';
  if (Array.isArray(value)) return fieldName.endsWith('_ids') ? 'many2many' : 'one2many';
  if (fieldName.endsWith('_id')) return 'many2one';
  return 'char';
}

function buildLegacyFieldDescriptor(widget: UnifiedPageContractV2Widget, mainData: Dict, model: string): Dict {
  const name = stableFieldName(widget.fieldCode);
  const type = inferFieldType(widget, mainData, model);
  const value = mainData[name];
  const componentConfig = asDict(widget.componentConfig);
  const readonly = componentConfig.readonly === true;
  const required = componentConfig.required === true;
  const relation = type === 'many2one' ? guessRelationModel(name, model) : '';
  const relationEntry = type === 'many2one'
    ? {
        model: relation,
        create_mode: 'disabled',
        can_read: true,
        can_create: false,
        delete_policy: {},
        reason_code: '',
        default_vals: {},
        inline_create: {
          enabled: false,
          create_on_no_match: false,
          name_field: 'name',
          match: 'exact_label',
        },
        action_id: null,
        menu_id: null,
        source: 'ui.contract.v2',
        ui_labels: {
          search_more: '搜索更多',
          create_and_edit: '创建并编辑',
          quick_create: '快速创建',
          inline_create: '使用“%s”创建',
          missing_create_entry: '没有可创建入口',
        },
      }
    : undefined;
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
  if (relationEntry) {
    descriptor.relation_entry = relationEntry;
  }
  if (type === 'selection' && Array.isArray(value)) {
    descriptor.selection = value;
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

function buildLegacySubViews(fieldWidgets: UnifiedPageContractV2Widget[], mainData: Dict, model: string): Dict {
  const out: Dict = {};
  fieldWidgets.forEach((widget) => {
    const fieldName = stableFieldName(widget.fieldCode);
    const type = inferFieldType(widget, mainData, model);
    if (type !== 'one2many' && type !== 'many2many') return;
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

function buildRuntimeProjectionFromV2(v2Contract: Dict, requestParams: Dict = {}): Dict {
  const pageInfo = asDict(v2Contract.pageInfo);
  const sourceContext = resolveV2SourceContext(v2Contract);
  const renderProfile = String(sourceContext.renderProfile || sourceContext.render_profile || '').trim();
  const v2Fields = collectUnifiedPageContractV2FieldWidgets(v2Contract);
  const mainData = resolveUnifiedPageContractV2MainData(v2Contract);
  const v2SourceContext = resolveUnifiedPageContractV2SourceContext(v2Contract);
  const globalStatus = resolveUnifiedPageContractV2GlobalStatus(v2Contract);
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
  const fields = v2Fields.reduce<Record<string, Dict>>((acc, widget) => {
    const descriptor = buildLegacyFieldDescriptor(widget, mainData, model);
    if (descriptor.name) {
      acc[descriptor.name as string] = descriptor;
    }
    return acc;
  }, {});
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
  const formLayout = buildLegacyFormLayout(v2Fields, fieldLabels);
  const subviews = buildLegacySubViews(v2Fields, mainData, model);
  const chatterEnabled = fieldNames.some((name) => ['message_ids', 'message_follower_ids', 'website_message_ids'].includes(name));
  const attachmentsEnabled = fieldNames.some((name) => ['message_attachment_count', 'doc_count', 'attachment_ids'].includes(name));
  const formView = viewType === 'form'
    ? {
        layout: formLayout,
        fields: fieldNames,
        subviews,
        ui_labels: {
          reload: '刷新',
          discard: '放弃',
          save: '保存',
          cancel: '取消',
        },
        ...(chatterEnabled ? { chatter: { enabled: true, label: '沟通', actions: [] } } : {}),
        ...(attachmentsEnabled ? {
          attachments: {
            enabled: true,
            upload: { max_bytes: 25 * 1024 * 1024 },
            ui_labels: {
              label: '附件',
              upload: '上传附件',
              uploading: '上传中...',
              download: '下载',
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
    visible_fields: fieldNames,
    field_groups: [],
    contract_surface: contractSurface,
    render_mode: renderMode,
    source_mode: sourceMode,
    governed_from_native: contractSurface !== 'native',
    surface_mapping: buildSurfaceMapping(contractSurface, renderMode, sourceMode),
    __v2_main_data: mainData,
    __v2_source_context: v2SourceContext,
  };
}

function adaptUnifiedPageContractV2Raw(result: IntentRawResult<Dict>, requestParams: Dict): ProjectionContractRawResult {
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

async function requestUnifiedPageContractV2Raw(params: Record<string, unknown>) {
  const result = await intentRequestRaw<Dict>({
    intent: 'ui.contract.v2',
    params: {
      client_type: 'web_pc',
      delivery_profile: 'full',
      ...params,
    },
  });
  const adapted = adaptUnifiedPageContractV2Raw(result, params);
  if (!Object.keys(adapted.data || {}).length) {
    throw new ApiError('ui.contract.v2 missing projection payload', 500, result.traceId, {
      reasonCode: 'UNIFIED_PAGE_CONTRACT_V2_PROJECTION_MISSING',
      kind: 'contract',
      retryable: false,
    });
  }
  return adapted;
}

export async function loadActionUnifiedPageContractV2(actionId: number, options?: LoadActionContractOptions): Promise<UnifiedPageContractV2> {
  const result = await requestUnifiedPageContractV2Raw(buildActionContractParams(actionId, options));
  return asDict(result.data.__unified_page_contract_v2) as UnifiedPageContractV2;
}

function rethrowContractError(err: unknown, context: { op: 'action_open' | 'model'; model?: string; actionId?: number }): never {
  if (!(err instanceof ApiError)) {
    throw err;
  }
  const message = String(err.message || '').trim();
  const isNativeBlocked = err.status === 410 && message.includes('native ui.contract op is disabled');
  if (!isNativeBlocked) {
    throw err;
  }
  const subject = context.op === 'action_open'
    ? `action_id=${Number(context.actionId || 0)}`
    : `model=${String(context.model || '').trim() || '-'}`;
  throw new ApiError(
    `ui.contract blocked by delivery policy (${subject}); switch to scene-ready scene route (/s/:sceneKey)`,
    err.status,
    err.traceId,
    {
      reasonCode: 'UI_CONTRACT_NATIVE_BLOCKED',
      kind: 'contract',
      hint: 'Prefer Scene-ready contract path: system.init -> scene registry -> /s/:sceneKey',
      errorCategory: err.errorCategory,
      retryable: false,
      suggestedAction: 'open_scene_route',
      details: {
        blocked_op: context.op,
        blocked_subject: subject,
      },
    },
  );
}

function buildActionContractParams(actionId: number, options?: LoadActionContractOptions) {
  const params: Record<string, unknown> = { op: 'action_open', action_id: actionId };
  const recordId = Number(options?.recordId || 0);
  if (Number.isFinite(recordId) && recordId > 0) {
    params.record_id = recordId;
  }
  const profile = String(options?.renderProfile || '').trim().toLowerCase();
  if (profile === 'create' || profile === 'edit' || profile === 'readonly') {
    params.render_profile = profile;
  }
  const surface = String(options?.surface || '').trim().toLowerCase();
  if (surface === 'user' || surface === 'native' || surface === 'hud') {
    params.contract_surface = surface;
    if (surface === 'hud') {
      params.contract_mode = 'hud';
      params.hud = 1;
    }
  }
  const sourceMode = String(options?.sourceMode || '').trim();
  if (sourceMode) {
    params.source_mode = sourceMode;
  }
  return params;
}

export async function loadActionContract(actionId: number, options?: LoadActionContractOptions) {
  try {
    const result = await requestUnifiedPageContractV2Raw(buildActionContractParams(actionId, options));
    return result.data;
  } catch (err) {
    rethrowContractError(err, { op: 'action_open', actionId });
  }
}

export async function loadActionContractRaw(actionId: number, options?: LoadActionContractOptions) {
  try {
    return await requestUnifiedPageContractV2Raw(buildActionContractParams(actionId, options));
  } catch (err) {
    rethrowContractError(err, { op: 'action_open', actionId });
  }
}

function buildModelContractParams(model: string, options?: LoadModelContractOptions) {
  const params: Record<string, unknown> = {
    op: 'model',
    model: String(model || '').trim(),
    view_type: options?.viewType || 'form',
  };
  const recordId = Number(options?.recordId || 0);
  if (Number.isFinite(recordId) && recordId > 0) {
    params.record_id = recordId;
  }
  const profile = String(options?.renderProfile || '').trim().toLowerCase();
  if (profile === 'create' || profile === 'edit' || profile === 'readonly') {
    params.render_profile = profile;
  }
  const surface = String(options?.surface || '').trim().toLowerCase();
  if (surface === 'user' || surface === 'native' || surface === 'hud') {
    params.contract_surface = surface;
    if (surface === 'hud') {
      params.contract_mode = 'hud';
      params.hud = 1;
    }
  }
  const sourceMode = String(options?.sourceMode || '').trim();
  if (sourceMode) {
    params.source_mode = sourceMode;
  }
  return params;
}

export async function loadModelContractRaw(model: string, options?: LoadModelContractOptions) {
  try {
    return await requestUnifiedPageContractV2Raw(buildModelContractParams(model, options));
  } catch (err) {
    rethrowContractError(err, { op: 'model', model });
  }
}

export async function loadModelUnifiedPageContractV2(model: string, options?: LoadModelContractOptions): Promise<UnifiedPageContractV2> {
  const result = await requestUnifiedPageContractV2Raw(buildModelContractParams(model, options));
  return asDict(result.data.__unified_page_contract_v2) as UnifiedPageContractV2;
}

export async function loadModelLitePreviewContract(model: string, options?: LoadModelContractOptions): Promise<UnifiedPageContractLite | null> {
  const viewType = options?.viewType || 'tree';
  const result = await intentRequestRaw<Record<string, unknown>>({
    intent: 'load_contract',
    params: {
      model: String(model || '').trim(),
      view_type: viewType,
      include: 'all',
      contractMode: 'lite_preview',
      contractVersion: '2.0.0',
      entryPoint: 'load_contract',
      clientType: 'web_pc',
      fallbackMode: 'legacy_default',
      traceId: `lite-frontend-pilot-${String(model || '').trim() || 'model'}-${viewType}`,
    },
  });
  return extractLiteContractFromIntentBody(result.rawBody);
}
