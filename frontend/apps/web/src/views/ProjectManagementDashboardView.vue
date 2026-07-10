<template>
  <section class="project-management-dashboard">
    <section v-if="status === 'loading'" class="status-wrap">
      <StatusPanel title="正在加载项目管理场景..." variant="info" />
    </section>
    <section v-else-if="status === 'error'" class="status-wrap">
      <StatusPanel :title="errorTitle" :message="errorMessage" variant="error" />
    </section>
    <section v-else>
      <PageRenderer
        :contract="orchestrationContract"
        :datasets="orchestrationDatasets"
        @action="handleBlockAction"
      />
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import PageRenderer from '../components/page/PageRenderer.vue';
import { intentRequest } from '../api/intents';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import type { PageBlockActionEvent, PageOrchestrationContract, PageOrchestrationZone } from '../app/pageOrchestration';
import { readWorkspaceContext } from '../app/workspaceContext';
import { formatAmountCN } from '../utils/semantic';

type RawBlock = {
  block_key: string;
  block_type: string;
  title?: string;
  state?: string;
  visibility?: Record<string, unknown>;
  data?: Record<string, unknown>;
  error?: Record<string, unknown>;
};

type RawZone = {
  zone_key: string;
  title?: string;
  zone_type?: string;
  display_mode?: string;
  blocks?: RawBlock[];
};

type DashboardResponse = {
  scene?: { key?: string; page?: string };
  page?: { key?: string; title?: string; route?: string };
  scene_contract_v1?: Record<string, unknown>;
  route_context?: Record<string, unknown>;
  project?: Record<string, unknown>;
  zones?: Record<string, RawZone>;
};

type SceneContractV1Zone = {
  key?: string;
  title?: string;
  zone_type?: string;
  display_mode?: string;
  block_keys?: string[];
  priority?: number;
};

const route = useRoute();
const router = useRouter();
const status = ref<'loading' | 'error' | 'idle'>('loading');
const raw = ref<DashboardResponse | null>(null);
const errorTitle = ref('项目管理场景加载失败');
const errorMessage = ref('');

function asText(value: unknown) {
  return String(value || '').trim();
}

function resolveProjectIdFromQuery() {
  const rawId = route.query.project_id;
  const value = Array.isArray(rawId) ? rawId[0] : rawId;
  const id = Number(value || 0);
  return Number.isFinite(id) && id > 0 ? id : 0;
}

const workspaceContextQuery = computed<LocationQueryRaw>(() => (
  readWorkspaceContext(route.query as Record<string, unknown>) as LocationQueryRaw
));

function resolveActionIntent(key: string, fallback = 'ui.contract') {
  const normalized = asText(key);
  if (!normalized) return fallback;
  if (normalized.startsWith('open_')) return 'ui.contract';
  if (normalized === 'refresh_page' || normalized === 'refresh') return 'api.data';
  return fallback;
}

function resolveActionTarget(key: string) {
  const map: Record<string, Record<string, unknown>> = {
    open_project_form: { kind: 'scene.key', scene_key: 'projects.ledger' },
    open_task_list: { kind: 'scene.key', scene_key: 'task.center' },
    open_task_overdue: { kind: 'scene.key', scene_key: 'task.center' },
    open_task_blocked: { kind: 'scene.key', scene_key: 'task.center' },
    open_payment_requests: { kind: 'scene.key', scene_key: 'finance.payment_requests' },
    open_settlement_orders: { kind: 'scene.key', scene_key: 'finance.settlement_orders' },
    open_risk_list: { kind: 'scene.key', scene_key: 'risk.center' },
    refresh_page: { kind: 'page.refresh' },
    refresh: { kind: 'page.refresh' },
  };
  return map[asText(key)] || {};
}

function asNumber(value: unknown) {
  const num = Number(value || 0);
  return Number.isFinite(num) ? num : 0;
}

function formatMetricValue(value: unknown, unit: string) {
  const num = asNumber(value);
  if (unit === '元') return formatAmountCN(num);
  if (unit === '%') return `${Math.round(num * 100) / 100}%`;
  return `${num}${unit || ''}`;
}

function metricStatusLabel(value: unknown) {
  const status = asText(value || '').toLowerCase();
  const map: Record<string, string> = {
    good: '良好',
    normal: '正常',
    ready: '就绪',
    warning: '需关注',
    danger: '高风险',
    error: '异常',
    empty: '暂无数据',
  };
  return map[status] || asText(value || '--') || '--';
}

function metricStatusTone(value: unknown) {
  const status = asText(value || '').toLowerCase();
  if (['good', 'normal', 'ready'].includes(status)) return 'success';
  if (['warning', 'empty'].includes(status)) return 'warning';
  if (['danger', 'error'].includes(status)) return 'danger';
  return 'neutral';
}

function metricItemLabel(value: unknown) {
  const key = asText(value);
  const map: Record<string, string> = {
    progress: '执行进度',
    cost: '成本状态',
    payment: '付款状态',
    risk: '风险状态',
  };
  return map[key] || key || '指标';
}

function normalizeZoneName(zoneKey: string) {
  const key = asText(zoneKey);
  return key.startsWith('zone.') ? key.slice(5) : key;
}

function cockpitZoneMeta(zoneName: string) {
  const map: Record<string, { title: string; description: string; display_mode: string; zone_type: string; priority: number }> = {
    metrics: {
      title: '核心指标',
      description: '优先关注合同、产值、成本、回款与风险指标。',
      display_mode: 'grid',
      zone_type: 'primary',
      priority: 120,
    },
    risk: {
      title: '风险提醒',
      description: '优先处理高风险与未闭环事项。',
      display_mode: 'stack',
      zone_type: 'critical',
      priority: 110,
    },
    progress: {
      title: '项目进度',
      description: '关注里程碑达成与延期任务。',
      display_mode: 'stack',
      zone_type: 'primary',
      priority: 100,
    },
    contract: {
      title: '合同执行',
      description: '跟踪合同总额、执行金额与变更。',
      display_mode: 'stack',
      zone_type: 'secondary',
      priority: 90,
    },
    cost: {
      title: '成本控制',
      description: '关注目标成本、实际成本和偏差。',
      display_mode: 'stack',
      zone_type: 'secondary',
      priority: 85,
    },
    finance: {
      title: '资金情况',
      description: '关注应收应付与资金缺口。',
      display_mode: 'stack',
      zone_type: 'secondary',
      priority: 80,
    },
    header: {
      title: '项目头部信息',
      description: '项目身份与管理上下文。',
      display_mode: 'stack',
      zone_type: 'supporting',
      priority: 60,
    },
    board_summary: {
      title: '项目总览',
      description: '先从全局项目看板进入，再查看具体项目驾驶舱。',
      display_mode: 'grid',
      zone_type: 'primary',
      priority: 120,
    },
    project_entries: {
      title: '项目看板',
      description: '选择一个项目进入该项目的指标、风险与进度视图。',
      display_mode: 'grid',
      zone_type: 'secondary',
      priority: 110,
    },
  };
  return map[zoneName] || {
    title: '',
    description: '',
    display_mode: 'stack',
    zone_type: 'supporting',
    priority: 50,
  };
}

function normalizeDatasetByBlock(block: RawBlock) {
  const blockType = asText(block.block_type);
  const blockKey = asText(block.block_key);
  const data = (block.data && typeof block.data === 'object') ? block.data : {};
  const state = asText(block.state || '');
  if (blockType === 'record_summary') {
    const summaryRows = Array.isArray(data.summary_rows)
      ? data.summary_rows as Array<Record<string, unknown>>
      : [];
    if (summaryRows.length) {
      return summaryRows.map((row, index) => ({
        key: asText(row.key || `summary-${index + 1}`),
        label: asText(row.label || row.key || `摘要 ${index + 1}`),
        value: row.value ?? '--',
      }));
    }
    const semantic = data.semantic_summary && typeof data.semantic_summary === 'object' && !Array.isArray(data.semantic_summary)
      ? data.semantic_summary as Record<string, unknown>
      : null;
    const summary = data.summary && typeof data.summary === 'object' && !Array.isArray(data.summary)
      ? data.summary as Record<string, unknown>
      : null;
    const source = semantic || summary;
    if (source && blockKey.includes('project.header')) {
      const rows = [
        { key: 'project_name', label: '项目名称', value: source.project_name ?? source.name ?? '--' },
        { key: 'project_code', label: '项目编码', value: source.project_code ?? '--' },
        { key: 'current_stage', label: '当前阶段', value: source.current_stage ?? source.stage_name ?? '--' },
        { key: 'project_manager', label: '项目经理', value: source.project_manager ?? source.manager_name ?? '--' },
        { key: 'owner_org', label: '建设单位', value: source.owner_org ?? source.partner_name ?? '--' },
        { key: 'planned_finish_date', label: '计划竣工', value: source.planned_finish_date ?? source.date_end ?? '--' },
        { key: 'health_state', label: '健康度', value: source.health_state ?? '--' },
      ];
      return rows.filter((row) => asText(row.value) !== '');
    }
    if (source && ('budget_target' in source || 'actual_cost' in source || 'cost_variance' in source)) {
      return [
        { key: 'budget_target', label: '目标成本', value: formatAmountCN(source.budget_target) },
        { key: 'actual_cost', label: '实际成本', value: formatAmountCN(source.actual_cost) },
        { key: 'cost_variance', label: '成本偏差', value: formatAmountCN(source.cost_variance) },
        { key: 'cost_variance_rate', label: '偏差率', value: formatMetricValue(source.cost_variance_rate, '%') },
        { key: 'cost_completion_rate', label: '成本完成率', value: formatMetricValue(source.cost_completion_rate, '%') },
        { key: 'budget_count', label: '预算条目', value: formatMetricValue(source.budget_count, '条') },
        { key: 'cost_ledger_count', label: '成本台账', value: formatMetricValue(source.cost_ledger_count, '条') },
      ];
    }
  }
  if (blockType === 'metric_row') {
    const kpi = data.kpi && typeof data.kpi === 'object' && !Array.isArray(data.kpi)
      ? data.kpi as Record<string, unknown>
      : null;
    if (kpi) {
      return [
        { key: 'contract_amount', label: '合同金额', value: formatMetricValue(kpi.contract_amount, '元'), tone: 'info', hint: '项目收入基线' },
        { key: 'output_value', label: '已完成产值', value: formatMetricValue(kpi.output_value, '元'), tone: 'info', hint: '执行产值累计' },
        { key: 'progress_rate', label: '完成率', value: formatMetricValue(kpi.progress_rate, '%'), tone: 'info', hint: '计划执行进度' },
        { key: 'cost_spent', label: '成本支出', value: formatMetricValue(kpi.cost_spent, '元'), tone: 'warning', hint: '实际成本累计' },
        { key: 'profit_estimate', label: '利润估算', value: formatMetricValue(kpi.profit_estimate, '元'), tone: 'success', hint: '产值-成本' },
        { key: 'payment_received', label: '回款金额', value: formatMetricValue(kpi.payment_received, '元'), tone: 'success', hint: '已回款' },
        { key: 'payment_rate', label: '回款率', value: formatMetricValue(kpi.payment_rate, '%'), tone: 'info', hint: '回款/合同额' },
        { key: 'risk_open_count', label: '风险事项', value: formatMetricValue(kpi.risk_open_count, '项'), tone: asNumber(kpi.risk_open_count) > 0 ? 'warning' : 'neutral', hint: '待闭环风险数' },
      ];
    }
    const items = Array.isArray((data as Record<string, unknown>).items)
      ? (data as Record<string, unknown>).items as Array<Record<string, unknown>>
      : [];
    if (items.some((item) => 'status' in item || 'explain' in item)) {
      return items.map((item, index) => ({
        key: asText(item.key || `metric-${index + 1}`),
        label: asText(item.label || metricItemLabel(item.key)),
        value: 'value' in item ? formatMetricValue(item.value, asText(item.unit || '')) : metricStatusLabel(item.status),
        tone: asText(item.tone || metricStatusTone(item.status)),
        hint: asText(item.explain || item.hint || ''),
        action_key: asText(item.action_key || ''),
      }));
    }
    return items.map((item) => ({
      key: asText(item.key || ''),
      label: asText(item.label || item.key || '指标'),
      value: formatMetricValue(item.value, asText(item.unit || '')),
      tone: asNumber(item.value || 0) > 0 ? 'info' : 'neutral',
    }));
  }
  if (blockType === 'entry_grid') {
    return Array.isArray((data as Record<string, unknown>).items)
      ? (data as Record<string, unknown>).items
      : [];
  }
  if (blockType === 'progress_summary') {
    const total = asNumber(data.task_total);
    const done = asNumber(data.task_done);
    const openCount = asNumber(data.task_open);
    const criticalTasks = asNumber(data.task_critical);
    const blockedTasks = asNumber(data.task_blocked);
    const completion = asNumber(data.completion_percent);
    const doneRate = total > 0 ? Math.min(100, Math.max(0, Math.round((done * 100) / total))) : 0;
    const milestoneProgress = asNumber(data.milestone_progress);
    const delayedTasks = asNumber(data.task_overdue);
    const delayedMilestones = asNumber(data.milestone_delay);
    const upcomingDays = asNumber(data.milestone_upcoming_days);
    const criticalPathHealth = metricStatusLabel(data.critical_path_health);
    return [
      { key: 'completion_percent', label: '总体完成率', value: completion, unit: '%' },
      { key: 'task_done_rate', label: '任务完成率', value: doneRate, unit: '%' },
      { key: 'milestone_progress', label: '里程碑完成率', value: milestoneProgress, unit: '%' },
      { key: 'critical_path_health', label: '关键路径健康度', value: criticalPathHealth },
      { key: 'task_open', label: '未完成任务', value: openCount, unit: '项' },
      { key: 'task_critical', label: '关键任务', value: criticalTasks, unit: '项' },
      { key: 'task_blocked', label: '阻塞任务', value: blockedTasks, unit: '项' },
      { key: 'delayed_tasks', label: '延期任务数', value: delayedTasks, unit: '项' },
      { key: 'delayed_milestones', label: '延期里程碑数', value: delayedMilestones, unit: '项' },
      { key: 'milestone_upcoming_days', label: '下一里程碑剩余天数', value: upcomingDays, unit: '天' },
    ];
  }
  if (blockType === 'alert_panel') {
    const alerts = Array.isArray(data.alerts) ? data.alerts : [];
    const rows = alerts.map((item) => {
      const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
      const actionKey = asText(row.action_key || 'open_risk_list') || 'open_risk_list';
      const hint = asText(row.hint || '');
      return {
        id: asText(row.code || row.id || ''),
        title: asText(row.title || row.code || '风险提醒'),
        description: hint ? `当前数量：${asText(row.value || '0')} · ${hint}` : `当前数量：${asText(row.value || '0')}`,
        tone: asText(row.level || 'warning') === 'info' ? 'warning' : asText(row.level || 'warning'),
        source: asText(row.source || 'business'),
        action_key: actionKey,
      };
    });
    const summary = data.summary && typeof data.summary === 'object' && !Array.isArray(data.summary)
      ? data.summary as Record<string, unknown>
      : null;
    if (summary) {
      rows.unshift({
        id: 'risk-score',
        title: `风险评分：${asNumber(summary.risk_score)}`,
        description: `等级：${asText(summary.risk_level || '--')} · 未闭环：${asNumber(summary.risk_open)} · 高风险：${asNumber(summary.risk_critical)} · 任务延期：${asNumber(summary.progress_task_overdue)} · 任务阻塞：${asNumber(summary.progress_task_blocked)} · 里程碑延期：${asNumber(summary.progress_milestone_delay)}`,
        tone: asText(summary.risk_level) === 'high' ? 'danger' : asText(summary.risk_level) === 'medium' ? 'warning' : 'info',
        source: 'business',
        action_key: 'open_risk_list',
      });
    }
    return rows;
  }
  if (blockType === 'record_table') {
    const summary = data.summary && typeof data.summary === 'object' && !Array.isArray(data.summary)
      ? data.summary as Record<string, unknown>
      : null;
    if (summary && ('contract_total' in summary || 'receivable' in summary)) {
      if ('contract_total' in summary) {
        return {
          columns: ['contract_total', 'executed_amount', 'performance_rate', 'subcontract_total', 'change_amount'],
          column_labels: {
            contract_total: '收入合同总额',
            executed_amount: '执行金额',
            performance_rate: '履约率',
            subcontract_total: '支出合同总额',
            change_amount: '变更金额',
          },
          rows: [{
            contract_total: formatAmountCN(summary.contract_total),
            executed_amount: formatAmountCN(summary.executed_amount),
            performance_rate: formatMetricValue(summary.performance_rate, '%'),
            subcontract_total: formatAmountCN(summary.subcontract_total),
            change_amount: formatAmountCN(summary.change_amount),
          }, {
            contract_total: `收入合同数：${asNumber(summary.contract_count_income)} 项`,
            executed_amount: `支出合同数：${asNumber(summary.contract_count_expense)} 项`,
            performance_rate: '--',
            subcontract_total: '--',
            change_amount: '--',
          }],
          state,
        };
      }
      return {
        columns: ['receivable', 'received', 'receive_pending', 'payable', 'paid', 'pay_pending', 'gap', 'net_cash'],
        column_labels: {
          receivable: '应收',
          received: '已收',
          receive_pending: '待收',
          payable: '应付',
          paid: '已付',
          pay_pending: '待付',
          gap: '资金缺口',
          net_cash: '净现金流',
        },
        rows: [{
          receivable: formatAmountCN(summary.receivable),
          received: formatAmountCN(summary.received),
          receive_pending: formatAmountCN(summary.receive_pending),
          payable: formatAmountCN(summary.payable),
          paid: formatAmountCN(summary.paid),
          pay_pending: formatAmountCN(summary.pay_pending),
          gap: formatAmountCN(summary.gap),
          net_cash: formatAmountCN(summary.net_cash),
        }],
        state,
      };
    }

    const columns = Array.isArray((data as Record<string, unknown>).columns)
      ? ((data as Record<string, unknown>).columns as string[])
      : [];
    const columnLabels: Record<string, string> = {
      contract_count: '合同数量',
      contract_amount_total: '合同总额',
      payment_request_total: '付款申请总数',
    };
    const rows = Array.isArray((data as Record<string, unknown>).rows)
      ? ((data as Record<string, unknown>).rows as Array<Record<string, unknown>>).map((row) => ({
        contract_count: row.contract_count,
        contract_amount_total: row.contract_amount_total ? formatAmountCN(row.contract_amount_total) : '--',
        payment_request_total: row.payment_request_total,
      }))
      : [];
    return { columns, rows, state, column_labels: columnLabels };
  }
  if (state === 'empty') {
    if (blockKey.includes('project.header')) {
      return { empty_message: '未找到可管理项目，请先选择项目后查看驾驶舱。' };
    }
    if (blockKey.includes('project.risk')) {
      return { empty_message: '当前项目暂无风险记录，继续保持。' };
    }
    return { empty_message: '当前项目暂无可展示管理数据，请先补齐任务、合同和成本基础信息。' };
  }
  return data;
}

function asSceneContractV1(payload: DashboardResponse | null): Record<string, unknown> {
  const rawContract = payload?.scene_contract_v1;
  return rawContract && typeof rawContract === 'object' ? rawContract as Record<string, unknown> : {};
}

function resolveDashboardZones(payload: DashboardResponse | null) {
  const sceneContract = asSceneContractV1(payload);
  const zonesV1 = Array.isArray(sceneContract.zones) ? sceneContract.zones as SceneContractV1Zone[] : [];
  const blocksV1 = sceneContract.blocks && typeof sceneContract.blocks === 'object'
    ? sceneContract.blocks as Record<string, RawBlock>
    : {};
  if (zonesV1.length > 0 && Object.keys(blocksV1).length > 0) {
    return zonesV1.map((zone, index) => {
      const zoneKey = asText(zone.key || `zone_${index + 1}`);
      const blockKeys = Array.isArray(zone.block_keys) ? zone.block_keys : [];
      const blocks = blockKeys
        .map((blockKey) => blocksV1[asText(blockKey)])
        .filter((block): block is RawBlock => Boolean(block && typeof block === 'object'));
      return {
        zone_key: zoneKey,
        title: asText(zone.title || ''),
        zone_type: asText(zone.zone_type || ''),
        display_mode: asText(zone.display_mode || ''),
        blocks,
      } as RawZone;
    });
  }
  const zonesRaw = payload?.zones && typeof payload.zones === 'object'
    ? Object.entries(payload.zones).map(([zoneKey, zoneValue]) => normalizeRuntimeZone(zoneKey, zoneValue))
    : [];
  return zonesRaw as RawZone[];
}

function normalizeRuntimeZone(zoneKey: string, value: unknown): RawZone {
  const zone = value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
  const normalizedKey = asText(zone.zone_key || zoneKey);
  const existingBlocks = Array.isArray(zone.blocks)
    ? zone.blocks.filter((block): block is RawBlock => Boolean(block && typeof block === 'object'))
    : [];
  if (existingBlocks.length) {
    return {
      zone_key: normalizedKey,
      title: asText(zone.title || ''),
      zone_type: asText(zone.zone_type || ''),
      display_mode: asText(zone.display_mode || ''),
      blocks: existingBlocks,
    };
  }

  const blocks: RawBlock[] = [];
  const directBlock = zone.block && typeof zone.block === 'object' && !Array.isArray(zone.block)
    ? zone.block as RawBlock
    : null;
  if (directBlock) {
    blocks.push(directBlock);
  }

  const project = zone.project && typeof zone.project === 'object' && !Array.isArray(zone.project)
    ? zone.project as Record<string, unknown>
    : null;
  if (!blocks.length && project) {
    blocks.push({
      block_key: `block.project.${normalizedKey}`,
      block_type: 'record_summary',
      title: '项目概况',
      state: 'ready',
      data: { semantic_summary: project },
    });
  }

  const items = Array.isArray(zone.items) ? zone.items as Array<Record<string, unknown>> : [];
  if (!blocks.length && items.length) {
    blocks.push({
      block_key: `block.project.${normalizedKey}`,
      block_type: 'metric_row',
      title: '核心指标',
      state: 'ready',
      data: { items },
    });
  }

  const summaryRows = Array.isArray(zone.summary_rows)
    ? zone.summary_rows as Array<Record<string, unknown>>
    : [];
  if (!blocks.length && summaryRows.length) {
    blocks.push({
      block_key: `block.project.${normalizedKey}`,
      block_type: 'record_summary',
      title: cockpitZoneMeta(normalizeZoneName(normalizedKey)).title || '摘要',
      state: 'ready',
      data: { summary_rows: summaryRows },
    });
  }

  return {
    zone_key: normalizedKey,
    title: asText(zone.title || ''),
    zone_type: asText(zone.zone_type || ''),
    display_mode: asText(zone.display_mode || ''),
    blocks,
  };
}

const orchestrationContract = computed<PageOrchestrationContract>(() => {
  const payload = raw.value || {};
  const projectName = asText((payload.project && typeof payload.project === 'object') ? (payload.project as Record<string, unknown>).name : '');
  const projectId = resolveProjectIdFromQuery() || asNumber((payload.project as Record<string, unknown> | undefined)?.id);
  const projectHint = projectName ? ` · ${projectName}` : '';
  const pageKey = asText(payload.page?.key || (projectId > 0 ? 'project.management.dashboard' : 'project.management.board'));
  const isBoard = pageKey === 'project.management.board';
  const zonesRaw = resolveDashboardZones(payload);
  const zones: PageOrchestrationZone[] = zonesRaw.map((zone, idx) => {
    const zoneKey = asText(zone.zone_key || `zone_${idx + 1}`);
    const zoneName = normalizeZoneName(zoneKey);
    const zoneMeta = cockpitZoneMeta(zoneName);
    const blocks = Array.isArray(zone.blocks) ? zone.blocks : [];
    const normalizedBlocks = blocks.map((block, bidx) => {
      const blockKey = asText(block.block_key || `${zoneKey}.block_${bidx + 1}`);
      const data = (block.data && typeof block.data === 'object') ? block.data : {};
      const quickActions = Array.isArray((data as Record<string, unknown>).quick_actions)
        ? (data as Record<string, unknown>).quick_actions as Array<Record<string, unknown>>
        : [];
      const actions = quickActions.map((row) => ({
        key: asText(row.key || ''),
        label: asText(row.label || row.key || ''),
        intent: asText(row.intent || 'ui.contract'),
      })).filter((row) => row.key);
      return {
        key: blockKey,
        block_type: asText(block.block_type || 'record_summary'),
        title: asText(block.title || ''),
        priority: 100 - bidx,
        data_source: `ds_${blockKey}`,
        actions,
      };
    });
    return {
      key: zoneKey,
      title: asText(zoneMeta.title || zone.title || ''),
      description: asText(zoneMeta.description || ''),
      zone_type: asText(zoneMeta.zone_type || zone.zone_type || 'supporting'),
      display_mode: asText(zoneMeta.display_mode || zone.display_mode || 'stack'),
      priority: Number(zoneMeta.priority || (50 - idx)),
      blocks: normalizedBlocks,
    };
  });

  return {
    contract_version: 'page_orchestration_v1',
    scene_key: asText(payload.scene?.key || 'project.management'),
    page: {
      key: pageKey,
      title: isBoard ? '项目看板' : '项目驾驶舱',
      subtitle: isBoard
        ? '先选择项目，再进入该项目的指标、风险与进度视图'
        : `聚焦指标、风险与进度${projectHint} · 项目ID ${projectId || '-'}`,
      page_type: isBoard ? 'board' : 'dashboard',
      layout_mode: isBoard ? 'board' : 'dashboard',
      header: {
        badges: [
          { label: isBoard ? '全局项目入口' : '管理驾驶舱', tone: 'info' },
          { label: isBoard ? '项目选择' : '7-block 合同兼容', tone: 'neutral' },
        ],
      },
      global_actions: [{ key: 'refresh_page', label: '刷新数据', intent: 'api.data' }],
    },
    zones,
  };
});

const orchestrationDatasets = computed<Record<string, unknown>>(() => {
  const payload = raw.value || {};
  const zonesRaw = resolveDashboardZones(payload);
  const datasets: Record<string, unknown> = {};
  zonesRaw.forEach((zone) => {
    const blocks = Array.isArray(zone.blocks) ? zone.blocks : [];
    blocks.forEach((block) => {
      const blockKey = asText(block.block_key || '');
      if (!blockKey) return;
      datasets[`ds_${blockKey}`] = normalizeDatasetByBlock(block);
    });
  });
  return datasets;
});

async function loadDashboard() {
  try {
    status.value = 'loading';
    const projectId = resolveProjectIdFromQuery();
    const data = await intentRequest<DashboardResponse>({
      intent: 'project.dashboard',
      params: projectId > 0 ? { project_id: projectId } : {},
      context: {
        scene_key: 'project.management',
        page_key: 'project.management.dashboard',
        ...(projectId > 0 ? { project_id: projectId } : {}),
      },
    });
    raw.value = (data && typeof data === 'object') ? data : {};
    status.value = 'idle';
  } catch (err) {
    status.value = 'error';
    errorTitle.value = '项目管理场景加载失败';
    errorMessage.value = err instanceof Error ? err.message : '项目管理场景加载失败';
  }
}

async function handleBlockAction(event: PageBlockActionEvent) {
  if (event.actionKey === 'open_project_dashboard') {
    const projectId = asNumber(event.item?.project_id || event.item?.entry_id);
    if (projectId > 0) {
      await router.push({
        path: '/s/project.management',
        query: {
          ...workspaceContextQuery.value,
          project_id: String(projectId),
        },
      });
      return;
    }
  }
  await executePageContractAction({
    actionKey: event.actionKey,
    router,
    actionIntent: resolveActionIntent,
    actionTarget: resolveActionTarget,
    query: workspaceContextQuery.value,
    onRefresh: loadDashboard,
    onFallback: async () => false,
  });
}

watch(
  () => route.fullPath,
  () => {
    loadDashboard();
  },
  { immediate: true },
);
</script>

<style scoped>
.project-management-dashboard {
  display: grid;
  gap: 12px;
  padding: 12px;
}
.status-wrap {
  padding: 4px;
}
</style>
