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
  route_context?: Record<string, unknown>;
  project?: Record<string, unknown>;
  zones?: Record<string, RawZone>;
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
    open_payment_requests: { kind: 'scene.key', scene_key: 'finance.payment_requests' },
    open_settlement_orders: { kind: 'scene.key', scene_key: 'finance.settlement_orders' },
    open_risk_list: { kind: 'scene.key', scene_key: 'risk.center' },
    refresh_page: { kind: 'page.refresh' },
    refresh: { kind: 'page.refresh' },
  };
  return map[asText(key)] || {};
}

function normalizeDatasetByBlock(block: RawBlock) {
  const blockType = asText(block.block_type);
  const data = (block.data && typeof block.data === 'object') ? block.data : {};
  const state = asText(block.state || '');
  if (blockType === 'record_summary') {
    if (data.summary && typeof data.summary === 'object' && !Array.isArray(data.summary)) {
      return Object.entries(data.summary as Record<string, unknown>).map(([key, value]) => ({
        key,
        label: key === 'name'
          ? '项目名称'
          : key === 'project_code'
            ? '项目编号'
            : key === 'partner_name'
              ? '建设单位'
              : key === 'manager_name'
                ? '项目负责人'
                : key === 'stage_name'
                  ? '项目状态'
                  : key,
        value: value ?? '--',
      }));
    }
  }
  if (blockType === 'metric_row') {
    const items = Array.isArray((data as Record<string, unknown>).items)
      ? (data as Record<string, unknown>).items as Array<Record<string, unknown>>
      : [];
    return items.map((item) => ({
      key: asText(item.key || ''),
      label: asText(item.label || item.key || '指标'),
      value: `${Number(item.value || 0)}${asText(item.unit || '')}`,
      tone: Number(item.value || 0) > 0 ? 'info' : 'neutral',
    }));
  }
  if (blockType === 'progress_summary') {
    const total = Number((data.task_total as number) || 0);
    const done = Number((data.task_done as number) || 0);
    const completion = Number((data.completion_percent as number) || 0);
    const doneRate = total > 0 ? Math.min(100, Math.max(0, Math.round((done * 100) / total))) : 0;
    return [
      { key: 'completion_percent', label: '总体完成率', value: completion },
      { key: 'task_done_rate', label: '任务完成率', value: doneRate },
    ];
  }
  if (blockType === 'alert_panel') {
    const alerts = Array.isArray(data.alerts) ? data.alerts : [];
    return alerts.map((item) => {
      const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
      return {
        id: asText(row.code || row.id || ''),
        title: asText(row.title || row.code || '风险提醒'),
        description: `当前数量：${asText(row.value || '0')}`,
        tone: asText(row.level || 'warning') === 'info' ? 'warning' : asText(row.level || 'warning'),
        action_key: 'open_risk_list',
      };
    });
  }
  if (blockType === 'record_table') {
    const columns = Array.isArray((data as Record<string, unknown>).columns)
      ? ((data as Record<string, unknown>).columns as string[])
      : [];
    const column_labels: Record<string, string> = {
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
    return { columns, rows, state, column_labels };
  }
  if (state === 'empty') {
    return { empty_message: '当前项目暂无可展示管理数据，请先补齐任务、合同和成本基础信息。' };
  }
  return data;
}

const orchestrationContract = computed<PageOrchestrationContract>(() => {
  const payload = raw.value || {};
  const zonesRaw = payload.zones && typeof payload.zones === 'object'
    ? Object.values(payload.zones)
    : [];
  const zones: PageOrchestrationZone[] = zonesRaw.map((zone, idx) => {
    const zoneKey = asText(zone.zone_key || `zone_${idx + 1}`);
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
      title: asText(zone.title || ''),
      zone_type: zoneKey.includes('risk') ? 'critical' : asText(zone.zone_type || 'primary'),
      display_mode: asText(zone.display_mode || 'stack'),
      priority: (
        zoneKey.includes('metrics') ? 100
          : zoneKey.includes('risk') ? 95
            : zoneKey.includes('progress') ? 90
              : zoneKey.includes('header') ? 85
                : 80 - idx
      ),
      blocks: normalizedBlocks,
    };
  });

  return {
    contract_version: 'page_orchestration_v1',
    scene_key: asText(payload.scene?.key || 'project.management'),
    page: {
      key: asText(payload.page?.key || 'project.management.dashboard'),
      title: '项目驾驶舱',
      subtitle: `聚焦指标、风险与进度 · 项目ID ${resolveProjectIdFromQuery() || '-'}`,
      page_type: 'dashboard',
      layout_mode: 'dashboard',
      header: {
        badges: [
          { label: '管理驾驶舱', tone: 'info' },
          { label: '7-block 合同兼容', tone: 'neutral' },
        ],
      },
      global_actions: [{ key: 'refresh_page', label: '刷新数据', intent: 'api.data' }],
    },
    zones,
  };
});

const orchestrationDatasets = computed<Record<string, unknown>>(() => {
  const payload = raw.value || {};
  const zonesRaw = payload.zones && typeof payload.zones === 'object'
    ? Object.values(payload.zones)
    : [];
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
    errorMessage.value = err instanceof Error ? err.message : 'unknown error';
  }
}

async function handleBlockAction(event: PageBlockActionEvent) {
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
