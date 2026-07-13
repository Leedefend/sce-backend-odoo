import type {
  BusinessConfigCoverageScanItem,
  BusinessConfigRemediationAction,
  BusinessConfigSurfacePayload,
} from '../../api/businessConfig';

const BUSINESS_FIELD_LABEL_OVERRIDES: Record<string, string> = {
  can_review: '可审批',
};

const ANALYSIS_VIEW_TYPES = new Set(['pivot', 'graph', 'calendar', 'dashboard']);

export function boundaryLabel(boundary: unknown) {
  const value = String(boundary || '').trim();
  if (value === 'ui_only') return '仅页面设置';
  if (value === 'business_contract') return '业务默认配置';
  if (value === 'business_contract_not_user_preference') return '业务默认配置';
  if (value === 'business_contract_with_policy_runtime') return '菜单显示规则';
  if (value === 'business_contract_version') return '版本记录';
  if (value === 'coverage_guard') return '覆盖检查';
  if (value === 'industry_policy_runtime') return '行业业务规则';
  return value || '未声明来源';
}

export function sectionHelpLabel(sectionKey: string) {
  if (sectionKey === 'form') return '字段显示、隐藏、必填、布局';
  if (sectionKey === 'list_search') return '列表列、搜索条件、默认分组';
  if (sectionKey === 'analysis') return '透视、图表、日历、看板';
  if (sectionKey === 'menu') return '菜单入口、显示范围、发布状态';
  if (sectionKey === 'approval') return '启用审批、审批方式、审批岗位';
  return '业务配置';
}

export function sectionDisplayLabel(sectionKey: string, fallback: string) {
  if (sectionKey === 'form') return '表单字段与布局';
  if (sectionKey === 'list_search') return '列表与搜索';
  if (sectionKey === 'analysis') return '分析视图';
  if (sectionKey === 'menu') return '菜单入口';
  if (sectionKey === 'approval') return '审批规则';
  return fallback || '业务配置';
}

export function sectionPrimaryCopy(sectionKey: string) {
  if (sectionKey === 'form') return '调整字段显示、必填、顺序和页面布局。';
  if (sectionKey === 'list_search') return '调整列表列、搜索条件和默认分组。';
  if (sectionKey === 'analysis') return '查看透视、图表、日历和看板配置版本。';
  if (sectionKey === 'menu') return '调整这个页面在菜单中的显示方式。';
  if (sectionKey === 'approval') return '设置这个业务是否需要审批、审批方式和审批岗位。';
  return '调整当前业务页面配置。';
}

export function sectionTaskKindLabel(sectionKey: string) {
  if (sectionKey === 'form') return '页面结构';
  if (sectionKey === 'list_search') return '查询体验';
  if (sectionKey === 'analysis') return '分析视图';
  if (sectionKey === 'menu') return '导航入口';
  if (sectionKey === 'approval') return '办理规则';
  return '业务配置';
}

export function sectionPrimaryActionLabel(sectionKey: string) {
  if (sectionKey === 'form') return '配置表单与布局';
  if (sectionKey === 'list_search') return '配置列表与搜索';
  if (sectionKey === 'analysis') return '配置分析';
  if (sectionKey === 'menu') return '配置菜单';
  if (sectionKey === 'approval') return '配置审批规则';
  return '配置';
}

export function viewTypeLabel(viewType: string) {
  if (viewType === 'form') return '表单';
  if (viewType === 'tree' || viewType === 'list') return '列表';
  if (viewType === 'search') return '搜索';
  if (viewType === 'pivot') return '透视';
  if (viewType === 'graph') return '图表';
  if (viewType === 'calendar') return '日历';
  if (viewType === 'dashboard') return '看板';
  return viewType || '通用';
}

export function pageViewModeText(row: BusinessConfigCoverageScanItem) {
  const modes = String(row.view_mode || '')
    .split(',')
    .map((item) => viewTypeLabel(item.trim()))
    .filter(Boolean);
  return modes.length ? `页面类型 ${modes.join('、')}` : '页面类型 通用';
}

export function pageDesignStatus(row: BusinessConfigCoverageScanItem) {
  if (!row.runtime_route?.path) return '暂不可预览';
  if (row.runtime_missing_view_types.includes('form')) return '可生成后设计';
  if (row.target_view_types.includes('form')) return '可设计表单';
  return '可打开页面';
}

export function rowCoverageProgressText(row: BusinessConfigCoverageScanItem) {
  const targets = (row.target_view_types || []).map((item) => String(item || '').trim()).filter(Boolean);
  const expected = targets.length || 1;
  const configured = targets.filter((viewType) => Number(row.coverage?.[viewType] || 0) > 0).length;
  const runtime = targets.filter((viewType) => Number(row.runtime_coverage?.[viewType] || 0) > 0).length;
  return `配置 ${configured}/${expected}，生效 ${runtime}/${expected}`;
}

export function rowMissingContractViewTypes(row: BusinessConfigCoverageScanItem) {
  return (row.runtime_missing_view_types || [])
    .filter((viewType) => String(row.runtime_gap_reasons?.[viewType] || '').trim() === 'missing_contract');
}

export function rowActionHintText(row: BusinessConfigCoverageScanItem) {
  if (!row.has_menu) return '需配置菜单入口';
  const reasons = new Set(Object.values(row.runtime_gap_reasons || {}).map((item) => String(item || '').trim()).filter(Boolean));
  if (reasons.has('missing_contract')) {
    const missingContractTypes = rowMissingContractViewTypes(row);
    return `待配置 ${missingContractTypes.map(viewTypeLabel).join('、')}`;
  }
  if (reasons.has('not_published')) return '需发布配置版本';
  if (reasons.has('not_runtime_applicable')) return '需检查作用域';
  if (row.user_preference_count > 0) return '存在个人配置';
  return '';
}

export function rowBootstrapMissingViewTypes(row: BusinessConfigCoverageScanItem, allowedViewTypes: string[]) {
  const allowed = new Set(allowedViewTypes);
  return rowMissingContractViewTypes(row)
    .filter((viewType) => allowed.has(viewType));
}

export function visibleRowRemediationActions(row: BusinessConfigCoverageScanItem) {
  return (row.remediation_actions || [])
    .filter((action: BusinessConfigRemediationAction) => ['configure_contract', 'publish_contract', 'fix_scope', 'configure_menu', 'review_user_preference_boundary'].includes(action.code))
    .slice(0, 2);
}

export function rowHasListSearchConfig(row: BusinessConfigCoverageScanItem) {
  return row.target_view_types.some((viewType) => viewType === 'tree' || viewType === 'search')
    || String(row.view_mode || '').split(',').some((viewType) => ['tree', 'list', 'search'].includes(viewType.trim()));
}

export function rowHasFormConfig(row: BusinessConfigCoverageScanItem) {
  return row.target_view_types.includes('form')
    || String(row.view_mode || '').split(',').some((viewType) => viewType.trim() === 'form');
}

export function rowHasAnalysisConfig(row: BusinessConfigCoverageScanItem) {
  return row.target_view_types.some((viewType) => ANALYSIS_VIEW_TYPES.has(viewType))
    || String(row.view_mode || '').split(',').some((viewType) => ANALYSIS_VIEW_TYPES.has(viewType.trim()));
}

export function runtimeReasonLabel(reason: string) {
  if (reason === 'missing_contract') return '未配置';
  if (reason === 'not_published') return '未发布';
  if (reason === 'not_runtime_applicable') return '作用域未命中';
  if (reason === 'not_published_or_not_runtime_applicable') return '未发布/作用域未命中';
  return reason || '未知';
}

export function severityLabel(severity: string) {
  if (severity === 'error') return '阻断';
  if (severity === 'warning') return '警告';
  if (severity === 'notice') return '提示';
  return '正常';
}

export function overallStatusLabel(status: string) {
  if (status === 'blocked') return '阻断';
  if (status === 'warning') return '警告';
  if (status === 'notice') return '提示';
  if (status === 'pass') return '通过';
  return status || '未知';
}

export function versionStatusLabel(status: string) {
  if (status === 'published') return '已发布';
  if (status === 'draft') return '草稿';
  if (status === 'archived') return '已归档';
  return status || '未知';
}

export function analysisItemLabel(item: string) {
  const text = String(item || '').trim();
  if (!text) return '';
  const [viewType, ...rest] = text.split('.');
  const label = viewTypeLabel(viewType);
  return rest.length ? `${label}：${rest.join(' / ')}` : label;
}

export function countDiff(left: string[], right: string[]) {
  const leftSet = new Set(left);
  const rightSet = new Set(right);
  return {
    added: right.filter((name) => !leftSet.has(name)),
    removed: left.filter((name) => !rightSet.has(name)),
  };
}

export function formatDiffNames(names: string[]) {
  const visible = names.slice(0, 3).join('、');
  if (!visible) return '';
  return names.length > 3 ? `${visible} 等 ${names.length} 项` : visible;
}

export function runtimeReasonText(row: BusinessConfigCoverageScanItem) {
  return row.runtime_missing_view_types
    .map((viewType) => `${viewTypeLabel(viewType)}:${runtimeReasonLabel(row.runtime_gap_reasons[viewType] || '')}`)
    .join('，');
}

export function runtimeEvidenceText(row: BusinessConfigCoverageScanItem) {
  return row.target_view_types
    .map((viewType) => {
      const evidence = row.runtime_evidence[viewType];
      if (!evidence) return '';
      return `${viewTypeLabel(viewType)} ${evidence.configured_count}/${evidence.published_count}/${evidence.runtime_count}`;
    })
    .filter(Boolean)
    .join('，');
}

export function runtimeRouteText(row: BusinessConfigCoverageScanItem) {
  const runtimeRoute = row.runtime_route || {};
  const path = String(runtimeRoute.path || '').trim();
  if (!path) return '';
  const params = new URLSearchParams();
  Object.entries(runtimeRoute.query || {}).forEach(([key, value]) => {
    const text = String(value || '').trim();
    if (key && text) params.set(key, text);
  });
  const query = params.toString();
  return query ? `${path}?${query}` : path;
}

export function remediationActionLabel(code: string) {
  if (code === 'configure_contract') return '补齐配置';
  if (code === 'publish_contract') return '查看版本';
  if (code === 'fix_scope') return '检查范围';
  if (code === 'configure_menu') return '配置菜单';
  if (code === 'review_user_preference_boundary') return '检查个人设置';
  return code;
}

export function deliveryReadinessItemStatusText(item: NonNullable<BusinessConfigSurfacePayload['delivery_readiness']>['items'][number]) {
  if (item.status === 'ready') return '就绪';
  return '待处理';
}

export function namesToText(names: string[]) {
  return names.join(', ');
}

export function parseNames(raw: string) {
  const seen = new Set<string>();
  return String(raw || '')
    .split(/[\n,，]+/)
    .map((item) => item.trim())
    .filter((item) => {
      if (!item || seen.has(item)) return false;
      seen.add(item);
      return true;
    });
}

export function normalizeNamesText(raw: string) {
  return namesToText(parseNames(raw));
}

export function cleanBusinessFieldLabel(name: unknown, label: unknown) {
  const fieldName = String(name || '').trim();
  const override = BUSINESS_FIELD_LABEL_OVERRIDES[fieldName];
  if (override) return override;
  let text = String(label || fieldName || '').trim();
  if (fieldName.startsWith('p1_visible_') && text.startsWith('P1可见')) {
    text = text.slice('P1可见'.length).trim();
  }
  return text || fieldName;
}

export function fieldTypeLabel(type: string) {
  const value = String(type || '').trim();
  if (value === 'many2one') return '关联';
  if (value === 'many2many' || value === 'one2many') return '明细';
  if (value === 'monetary' || value === 'float' || value === 'integer') return '数值';
  if (value === 'date' || value === 'datetime') return '日期';
  if (value === 'boolean') return '是/否';
  if (value === 'selection') return '选项';
  if (value === 'text' || value === 'html') return '长文本';
  if (value === 'char') return '文本';
  return value;
}

export function shortFieldNameHint(name: string) {
  const cleaned = String(name || '').trim();
  if (!cleaned) return '';
  return cleaned.length > 28 ? `${cleaned.slice(0, 12)}...${cleaned.slice(-10)}` : cleaned;
}
