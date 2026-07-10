<template>
  <section v-if="pageSectionsReady" class="scene-contract-block-grid" :style="pageSectionStyle('root')" :data-contract-sections="pageSectionsFingerprint">
    <StatusPanel v-if="status === 'loading'" title="正在加载场景..." variant="info" />
    <StatusPanel v-else-if="status === 'error'" title="场景加载失败" :message="errorMessage" variant="error" />
    <PageRenderer
      v-else
      :contract="pageContract"
      :datasets="datasets"
      @action="handleAction"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import type { NavNode } from '@sc/schema';
import { intentRequest } from '../api/intents';
import StatusPanel from '../components/StatusPanel.vue';
import PageRenderer from '../components/page/PageRenderer.vue';
import { useSessionStore } from '../stores/session';
import { getSceneByKey } from '../app/resolvers/sceneRegistry';
import type { PageBlockActionEvent, PageOrchestrationBlock, PageOrchestrationContract } from '../app/pageOrchestration';
import { usePageContract } from '../app/pageContract';

type SceneBlock = Record<string, unknown> & {
  key?: string;
  type?: string;
  title?: string;
  subtitle?: string;
  value?: unknown;
  items?: Array<Record<string, unknown>>;
  target?: Record<string, unknown>;
};

type SceneContract = {
  schema_version?: string;
  scene?: Record<string, unknown>;
  title?: string;
  summary?: Record<string, unknown>;
  summary_rows?: Array<Record<string, unknown>>;
  blocks?: SceneBlock[];
  page?: {
    layout?: string;
    blocks?: SceneBlock[];
  };
};

const props = defineProps<{
  intent: string;
  sceneKey: string;
}>();

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const runtimePageContract = usePageContract('scene_contract_block_grid', { allowSceneContractFallback: true });
const pageSectionEnabled = runtimePageContract.sectionEnabled;
const pageSectionStyle = runtimePageContract.sectionStyle;
const pageSectionTagIs = runtimePageContract.sectionTagIs;
const pageSectionsReady = computed(() => (
  pageSectionEnabled('root', true)
  && pageSectionEnabled('main', true)
  && pageSectionTagIs('root', 'section')
  && pageSectionTagIs('main', 'section')
));
const pageSectionsFingerprint = computed(() => JSON.stringify([
  pageSectionStyle('main'),
]));
const status = ref<'loading' | 'error' | 'idle'>('loading');
const errorMessage = ref('');
const rawContract = ref<SceneContract | null>(null);

function asText(value: unknown) {
  return String(value || '').trim();
}

function parseRouteTarget(rawRoute: string) {
  const raw = asText(rawRoute);
  if (!raw) return null;
  const [path, queryRaw] = raw.split('?', 2);
  const query: Record<string, string> = {};
  if (queryRaw) {
    const params = new URLSearchParams(queryRaw);
    params.forEach((value, key) => {
      if (key) query[key] = value;
    });
  }
  return { path: path || raw, query };
}

function positiveRouteInt(...keys: string[]) {
  for (const key of keys) {
    const parsed = Number(route.query[key] || 0);
    if (Number.isFinite(parsed) && parsed > 0) return Math.trunc(parsed);
  }
  return 0;
}

function normalizeBlockType(type: unknown) {
  const raw = asText(type).toLowerCase();
  if (raw === 'metric_card') return 'metric';
  if (raw === 'shortcut_grid') return 'entry_grid';
  if (raw === 'warning_list') return 'alert_panel';
  if (raw === 'native_view_ref') return 'record_summary';
  return raw || 'record_summary';
}

function normalizeTone(value: unknown) {
  const raw = asText(value).toLowerCase();
  if (['success', 'warning', 'danger', 'info', 'neutral'].includes(raw)) return raw;
  return 'neutral';
}

function targetActionKey(blockKey: string) {
  return `open_${blockKey}`;
}

function normalizeDataset(block: SceneBlock) {
  const target = block.target && typeof block.target === 'object' ? block.target : {};
  const actionKey = targetActionKey(asText(block.key));
  if (block.type === 'metric_card') {
    return [{
      key: asText(block.key),
      label: asText(block.title),
      value: block.value ?? '--',
      hint: asText(block.subtitle),
      tone: normalizeTone(block.tone),
      action_key: actionKey,
      target,
    }];
  }
  if (block.type === 'shortcut_grid') {
    return (Array.isArray(block.items) ? block.items : []).map((item, index) => ({
      id: asText(item.key) || `entry-${index + 1}`,
      title: asText(item.label || item.title) || `入口 ${index + 1}`,
      hint: asText(item.subtitle || item.hint),
      action_key: targetActionKey(`${asText(block.key)}_${asText(item.key) || index + 1}`),
      target: item.target && typeof item.target === 'object' ? item.target : {},
    }));
  }
  if (block.type === 'todo_list' || block.type === 'warning_list') {
    return (Array.isArray(block.items) ? block.items : []).map((item, index) => ({
      id: asText(item.key) || `${block.type}-${index + 1}`,
      title: asText(item.title) || asText(item.label) || `事项 ${index + 1}`,
      description: asText(item.description || item.subtitle) || (
        Number(item.count || 0) > 0 ? `待处理 ${Number(item.count || 0)} 条` : ''
      ),
      count: Number(item.count || 0),
      source: asText(item.source || item.model || block.model || 'business'),
      source_label: asText(item.source_label || item.sourceLabel),
      tone: block.type === 'warning_list' ? 'warning' : 'info',
      action_label: '打开',
      action_key: targetActionKey(`${asText(block.key)}_${asText(item.key) || index + 1}`),
      target: item.target && typeof item.target === 'object' ? item.target : {},
    }));
  }
  if (block.type === 'native_view_ref') {
    return [
      {
        key: 'summary',
        label: '说明',
        value: asText(block.summary) || '可继续打开原生明细。',
      },
      {
        key: 'model',
        label: '业务对象',
        value: asText(block.model) || '--',
      },
      {
        key: 'count',
        label: '记录数',
        value: Number(block.count || 0),
      },
    ];
  }
  return block;
}

function normalizeBlock(block: SceneBlock, index: number): PageOrchestrationBlock {
  const key = asText(block.key) || `block_${index + 1}`;
  return {
    key,
    block_type: normalizeBlockType(block.type),
    title: block.type === 'metric_card' ? '' : asText(block.title),
    subtitle: asText(block.subtitle),
    priority: 100 - index,
    tone: normalizeTone(block.tone),
    data_source: `ds_${key}`,
    actions: block.target && typeof block.target === 'object'
      ? [{ key: targetActionKey(key), label: block.type === 'native_view_ref' ? '打开明细' : '打开' }]
      : [],
  };
}

const blocks = computed(() => {
  const page = rawContract.value?.page;
  const pageBlocks = Array.isArray(page?.blocks) ? page.blocks : [];
  const rootBlocks = Array.isArray(rawContract.value?.blocks) ? rawContract.value.blocks : [];
  const summaryRows = Array.isArray(rawContract.value?.summary_rows) ? rawContract.value.summary_rows : [];
  const summaryBlocks: SceneBlock[] = summaryRows.map((row, index) => ({
    key: asText(row.key) || `summary_${index + 1}`,
    type: 'metric_card',
    title: asText(row.label) || asText(row.key) || `指标 ${index + 1}`,
    subtitle: asText(row.copy),
    value: row.value ?? '--',
    tone: 'neutral',
  }));
  return [...summaryBlocks, ...(pageBlocks.length ? pageBlocks : rootBlocks)];
});

const pageContract = computed<PageOrchestrationContract>(() => ({
  schema_version: 'v1',
  contract_version: 'page_orchestration_v1',
  scene_key: props.sceneKey,
  page: {
    key: props.sceneKey,
    title: asText(rawContract.value?.title || rawContract.value?.scene?.title) || props.sceneKey,
    subtitle: asText(rawContract.value?.scene?.subtitle),
    page_type: 'dashboard',
    layout_mode: 'block_grid',
  },
  zones: [{
    key: 'main',
    title: '',
    display_mode: 'grid',
    zone_type: 'primary',
    priority: 100,
    blocks: blocks.value.map(normalizeBlock),
  }],
}));

const datasets = computed<Record<string, unknown>>(() => {
  const out: Record<string, unknown> = {};
  blocks.value.forEach((block, index) => {
    const key = asText(block.key) || `block_${index + 1}`;
    out[`ds_${key}`] = normalizeDataset(block);
  });
  return out;
});

function findActionNodeByXmlid(nodes: NavNode[], xmlid: string): NavNode | null {
  const wanted = asText(xmlid);
  if (!wanted) return null;
  for (const node of nodes) {
    const nodeXmlid = asText(node.meta?.action_xmlid);
    if (nodeXmlid === wanted && node.meta?.action_id) return node;
    if (node.children?.length) {
      const found = findActionNodeByXmlid(node.children, wanted);
      if (found) return found;
    }
  }
  return null;
}

function findMenuNodeByXmlid(nodes: NavNode[], xmlid: string): NavNode | null {
  const wanted = asText(xmlid);
  if (!wanted) return null;
  for (const node of nodes) {
    const nodeXmlid = asText((node as NavNode & { xmlid?: string }).xmlid || node.meta?.menu_xmlid);
    if (nodeXmlid === wanted) return node;
    if (node.children?.length) {
      const found = findMenuNodeByXmlid(node.children, wanted);
      if (found) return found;
    }
  }
  return null;
}

function findTargetByActionKey(actionKey: string) {
  for (const block of blocks.value) {
    const blockKey = asText(block.key);
    if (targetActionKey(blockKey) === actionKey) {
      return block.target && typeof block.target === 'object' ? block.target : {};
    }
    const items = Array.isArray(block.items) ? block.items : [];
    for (let index = 0; index < items.length; index += 1) {
      const item = items[index] || {};
      const itemActionKey = targetActionKey(`${blockKey}_${asText(item.key) || index + 1}`);
      if (itemActionKey === actionKey) {
        return item.target && typeof item.target === 'object' ? item.target : {};
      }
    }
  }
  return {};
}

async function openTarget(target: Record<string, unknown>) {
  const sceneKey = asText(target.scene_key || target.sceneKey);
  if (sceneKey) {
    const scene = getSceneByKey(sceneKey);
    const rawRoute = asText(target.route || scene?.target?.route || scene?.route || `/s/${sceneKey}`);
    const parsed = parseRouteTarget(rawRoute);
    if (parsed) {
      await router.push({ path: parsed.path, query: { ...route.query, ...parsed.query } });
      return true;
    }
  }
  const routePath = asText(target.route);
  if (routePath) {
    const parsed = parseRouteTarget(routePath);
    await router.push({
      path: parsed?.path || routePath,
      query: {
        ...route.query,
        ...(parsed?.query || {}),
      },
    });
    return true;
  }
  const actionXmlid = asText(target.action_xmlid);
  const actionNode = findActionNodeByXmlid(session.menuTree, actionXmlid);
  if (actionNode?.meta?.action_id) {
    await router.push({
      path: `/a/${actionNode.meta.action_id}`,
      query: {
        action_id: String(actionNode.meta.action_id),
        menu_id: actionNode.menu_id ? String(actionNode.menu_id) : undefined,
      },
    });
    return true;
  }
  const menuXmlid = asText(target.menu_xmlid);
  const menuNode = findMenuNodeByXmlid(session.menuTree, menuXmlid);
  if (menuNode?.meta?.action_id) {
    await router.push({
      path: `/a/${menuNode.meta.action_id}`,
      query: {
        action_id: String(menuNode.meta.action_id),
        menu_id: menuNode.menu_id ? String(menuNode.menu_id) : undefined,
      },
    });
    return true;
  }
  if (menuNode?.menu_id) {
    await router.push({ path: `/m/${menuNode.menu_id}` });
    return true;
  }
  return false;
}

async function handleAction(event: PageBlockActionEvent) {
  const itemTarget = event.item?.target && typeof event.item.target === 'object' ? event.item.target as Record<string, unknown> : {};
  const eventTarget = event.target && Object.keys(event.target).length ? event.target : {};
  const target = Object.keys(eventTarget).length
    ? eventTarget
    : Object.keys(itemTarget).length
      ? itemTarget
      : findTargetByActionKey(event.actionKey);
  await openTarget((target || {}) as Record<string, unknown>);
}

async function loadContract() {
  try {
    status.value = 'loading';
    errorMessage.value = '';
    const data = await intentRequest<SceneContract>({
      intent: props.intent,
      params: {
        project_id: positiveRouteInt('project_id', 'record_id') || undefined,
        record_id: positiveRouteInt('record_id', 'project_id') || undefined,
      },
      context: {
        scene_key: props.sceneKey,
        project_id: positiveRouteInt('project_id', 'record_id') || undefined,
      },
    });
    rawContract.value = (data && typeof data === 'object') ? data : {};
    status.value = 'idle';
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '场景区块加载失败';
    status.value = 'error';
  }
}

watch(
  () => [props.intent, props.sceneKey, route.fullPath],
  () => {
    void loadContract();
  },
  { immediate: true },
);
</script>

<style scoped>
.scene-contract-block-grid {
  display: grid;
  gap: 12px;
  padding: 12px;
}
</style>
