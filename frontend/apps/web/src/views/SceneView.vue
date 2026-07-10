<template>
  <section class="scene" :class="{ 'scene--compact-controls': compactSceneControls }">
    <section
      v-if="headerActions.length || sceneViewSwitchOptions.length > 1"
      class="scene-top-controls"
      :class="{ 'scene-top-controls--compact': compactSceneControls }"
    >
      <section v-if="headerActions.length" class="scene-actions" :class="{ 'scene-actions--compact': compactSceneControls }">
        <button
          v-for="action in headerActions"
          :key="`scene-header-${action.key}`"
          class="ghost"
          :disabled="status === 'loading' || action.disabled"
          :title="action.disabledReason || ''"
          @click="executeHeaderAction(action.key)"
        >
          {{ action.label || action.key }}
        </button>
      </section>
      <section v-if="sceneViewSwitchOptions.length > 1" class="scene-view-switch" :class="{ 'scene-view-switch--compact': compactSceneControls }">
        <p v-if="!compactSceneControls" class="scene-view-switch__label">{{ pageText('scene_view_switch_label', '视图切换') }}</p>
        <div class="scene-view-switch__chips">
          <button
            v-for="item in sceneViewSwitchOptions"
            :key="`scene-view-switch-${item.key}`"
            class="scene-view-switch__chip"
            :class="{ active: item.active }"
            :disabled="item.active || status === 'loading'"
            @click="openSiblingScene(item.key)"
          >
            {{ item.label }}
          </button>
        </div>
      </section>
    </section>
    <StatusPanel
      v-if="pageSectionEnabled('status_loading', true) && pageSectionTagIs('status_loading', 'section') && status === 'loading'"
      :title="pageText('loading_title', '正在加载场景...')"
      variant="info"
      :style="pageSectionStyle('status_loading')"
    />
    <StatusPanel
      v-else-if="pageSectionEnabled('status_error', true) && pageSectionTagIs('status_error', 'section') && status === 'error'"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="error?.traceId"
      :error-code="error?.code"
      :reason-code="error?.reasonCode"
      :error-category="error?.errorCategory"
      :error-details="error?.details"
      :retryable="error?.retryable"
      :hint="errorCopy.hint"
      :suggested-action="error?.suggestedAction"
      variant="error"
      :style="pageSectionStyle('status_error')"
    />
    <StatusPanel
      v-else-if="pageSectionEnabled('status_forbidden', true) && pageSectionTagIs('status_forbidden', 'section') && status === 'forbidden'"
      :title="forbiddenCopy.title"
      :message="forbiddenCopy.message"
      :hint="forbiddenCopy.hint"
      variant="forbidden_capability"
      :on-retry="() => goWorkbench(ErrorCodes.CAPABILITY_MISSING)"
      :style="pageSectionStyle('status_forbidden')"
    />
    <StatusPanel
      v-else-if="status === 'idle' && !sceneContractEntryIntent && !handlingEntryGroups.length && !productDeliverySurface.visible && embeddedRecordActionId <= 0 && embeddedActionId <= 0"
      :title="pageText('status_idle_diag_title', '场景已加载，但没有可渲染目标')"
      :message="idleDiagnosticMessage"
      variant="info"
    />
    <SceneContractBlockGridView
      v-if="status === 'idle' && sceneContractEntryIntent"
      :intent="sceneContractEntryIntent"
      :scene-key="currentSceneKey"
    />
    <SceneBlocksRenderer
      v-if="status === 'idle' && !sceneContractEntryIntent && showSceneBlocksDebug && sceneBlocks.length"
      :blocks="sceneBlocks"
      @action="handleSceneBlockAction"
    />
    <StatusPanel
      v-if="status === 'idle' && !sceneContractEntryIntent && validationHint"
      :title="pageText('validation_surface_title', '表单约束提示')"
      :message="validationHint"
      variant="info"
    />
    <section
      v-if="status === 'idle' && !sceneContractEntryIntent && handlingEntryGroups.length"
      class="handling-surface"
    >
      <header class="handling-surface__header">
        <div>
          <p class="handling-surface__eyebrow">{{ pageText('handling_surface_eyebrow', '办理入口') }}</p>
          <h3 class="handling-surface__title">{{ pageText('handling_surface_title', '综合办理') }}</h3>
        </div>
        <span class="handling-surface__badge">{{ handlingEntryCatalog.item_count || handlingEntryItemCount }} 项</span>
      </header>
      <div class="handling-surface__grid">
        <article
          v-for="group in handlingEntryGroups"
          :key="group.key"
          class="handling-group"
        >
          <header class="handling-group__header">
            <h4>{{ group.title }}</h4>
            <span>{{ group.items.length }}</span>
          </header>
          <div class="handling-group__items">
            <button
              v-for="item in group.items"
              :key="item.key"
              type="button"
              class="handling-item"
              :disabled="!isHandlingEntryActionable(item)"
              :title="item.business_category_code"
              @click="openHandlingEntry(item)"
            >
              <span>{{ item.label }}</span>
            </button>
          </div>
        </article>
      </div>
    </section>
    <section
      v-if="status === 'idle' && !sceneContractEntryIntent && productDeliverySurface.visible"
      class="scene-delivery"
      :class="{ 'scene-delivery--advisory': productDeliverySurface.advisoryOnly }"
    >
      <div class="scene-delivery__copy">
        <p class="scene-delivery__eyebrow">
          {{ productDeliverySurface.advisoryOnly ? pageText('scene_delivery_eyebrow_advisory', '交付提示') : pageText('scene_delivery_eyebrow_direct', '交付入口') }}
        </p>
        <h3 class="scene-delivery__title">{{ productDeliverySurface.title }}</h3>
        <p class="scene-delivery__message">{{ productDeliverySurface.message }}</p>
      </div>
      <button
        v-if="productDeliverySurface.actionLabel"
        class="ghost scene-delivery__cta"
        type="button"
            :disabled="productDeliverySurface.actionDisabled || isLoading"
        @click="openProductDeliveryTarget()"
      >
        {{ productDeliverySurface.actionLabel }}
      </button>
    </section>
    <StatusPanel
      v-if="status === 'idle' && !sceneContractEntryIntent && runtimeDiagnosticMessage"
      :title="runtimeDiagnosticTitle"
      :message="runtimeDiagnosticMessage"
      variant="info"
    />
    <ContractFormPage v-if="status === 'idle' && !sceneContractEntryIntent && embeddedRecordActionId > 0" />
    <ActionView v-else-if="status === 'idle' && !sceneContractEntryIntent && embeddedActionId > 0" />
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router';
import ActionView from './ActionViewShell.vue';
import SceneContractBlockGridView from './SceneContractBlockGridView.vue';
import SceneBlocksRenderer from '../components/scene/SceneBlocksRenderer.vue';
import ContractFormPage from '../pages/ContractFormPage.vue';
import StatusPanel from '../components/StatusPanel.vue';
import { getSceneByKey, resolveSceneLayout } from '../app/resolvers/sceneRegistry';
import { useSessionStore } from '../stores/session';
import { evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { ErrorCodes } from '../app/error_codes';
import { resolveErrorCopy, useStatus } from '../composables/useStatus';
import { trackSceneOpen } from '../api/usage';
import { intentRequest } from '../api/intents';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import { readWorkspaceContext } from '../app/workspaceContext';
import { buildCanonicalSceneRouteTarget, normalizeLegacyWorkbenchPath, resolveSceneDefaultOrder } from '../app/routeQuery';
import { findActionMeta, findActionNodeByModel, findMenuNode } from '../app/menu';
import { usePageContract } from '../app/pageContract';
import { config } from '../config';
import type { NavNode } from '@sc/schema';
import { setSceneRegistryFromSceneReadyContract, type Scene, type SceneTarget } from '../app/resolvers/sceneRegistry';
import { isSceneBlocksDebugEnabled } from '../config/debug';

const route = useRoute();
const router = useRouter();
const showSceneBlocksDebug = computed(() => isSceneBlocksDebugEnabled(route));
const session = useSessionStore();
const pageContract = usePageContract('scene', { allowSceneContractFallback: true });
const pageText = pageContract.text;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const headerActions = computed(() => pageGlobalActions.value);
const currentSceneKey = computed(() => String(route.params.sceneKey || route.meta?.sceneKey || '').trim());
const sceneContractEntryIntentMap: Record<string, string> = {
  'workspace.home': 'workspace.home.enter',
  'dashboard.company': 'dashboard.company.enter',
};
const sceneContractEntryIntent = computed(() => {
  const routeIntent = String(route.query.entry_intent || route.query.scene_intent || '').trim();
  if (routeIntent) return routeIntent;
  return sceneContractEntryIntentMap[currentSceneKey.value] || '';
});
const findActionNodeByModelRef = findActionNodeByModel;
const scene = ref<Scene | null>(null);
const status = ref<'loading' | 'error' | 'forbidden' | 'idle'>('loading');
const isLoading = computed(() => status.value === 'loading');
const { error, clearError, setError } = useStatus();
const errorCopy = ref(resolveErrorCopy(null, pageText('error_fallback', '场景加载失败')));
const forbiddenCopy = ref({
  title: pageText('forbidden_title', '能力未开通'),
  message: pageText('forbidden_message', '当前角色无法进入该场景。'),
  hint: '',
});
const validationHint = ref('');
const embeddedActionId = ref(0);
const embeddedRecordActionId = ref(0);
const sceneReadyHydrateRequested = ref(false);
const compactSceneControls = computed(() => currentSceneKey.value === 'projects.list');
type SceneBlockViewMode = 'form' | 'list' | 'kanban';
type HandlingEntryItem = {
  key: string;
  label: string;
  business_category_code?: string;
  action_xmlid: string;
  entry_mode?: string;
  business_category_options?: Array<Record<string, unknown>>;
  target: Record<string, unknown>;
};
type HandlingEntryGroup = {
  key: string;
  title: string;
  items: HandlingEntryItem[];
};

function resolveSceneBlockViewMode(): SceneBlockViewMode {
  const routeMode = String(route.query.view_mode || '').trim().toLowerCase();
  if (routeMode === 'form') return 'form';
  if (routeMode === 'kanban') return 'kanban';
  const layoutKind = String(scene.value?.layout?.kind || '').trim().toLowerCase();
  if (layoutKind === 'record') return 'form';
  if (layoutKind === 'kanban') return 'kanban';
  return 'list';
}
const sceneBlocks = computed(() => {
  const currentScene = scene.value;
  const sceneReady = currentScene?.scene_ready;
  const mode = resolveSceneBlockViewMode();
  const byView = (sceneReady?.scene_blocks_by_view && typeof sceneReady.scene_blocks_by_view === 'object')
    ? sceneReady.scene_blocks_by_view
    : {};
  const modeBlocks = Array.isArray(byView?.[mode]) ? byView[mode] : [];
  const fallbackBlocks = Array.isArray(sceneReady?.scene_blocks) ? sceneReady.scene_blocks : [];
  const blocks = modeBlocks.length ? modeBlocks : fallbackBlocks;
  return blocks.filter((item) => item && typeof item === 'object') as Array<Record<string, unknown>>;
});

const handlingEntryCatalog = computed<Record<string, unknown>>(() => {
  const currentScene = scene.value;
  const direct = currentScene?.scene_ready?.handling_entry_catalog;
  if (direct && typeof direct === 'object') {
    return direct;
  }
  return {};
});

const handlingEntryGroups = computed<HandlingEntryGroup[]>(() => {
  const catalog = handlingEntryCatalog.value;
  if (String(catalog.contract_version || '').trim() !== 'handling_entry_catalog.v1') {
    return [];
  }
  const groups = Array.isArray(catalog.groups) ? catalog.groups : [];
  return groups
    .map((rawGroup, groupIndex) => {
      const group = rawGroup && typeof rawGroup === 'object' ? rawGroup as Record<string, unknown> : {};
      const rawItems = Array.isArray(group.items) ? group.items : [];
      const items = rawItems
        .map((rawItem, itemIndex) => {
          const item = rawItem && typeof rawItem === 'object' ? rawItem as Record<string, unknown> : {};
          const label = String(item.label || '').trim();
          const categoryCode = String(item.business_category_code || '').trim();
          const actionXmlid = String(item.action_xmlid || '').trim();
          const categoryOptions = Array.isArray(item.business_category_options)
            ? item.business_category_options.filter((option) => option && typeof option === 'object') as Array<Record<string, unknown>>
            : [];
          const target = item.target && typeof item.target === 'object' && !Array.isArray(item.target)
            ? item.target as Record<string, unknown>
            : {};
          const targetActionXmlid = String(target.action_xmlid || '').trim();
          if (!label || (!categoryCode && !categoryOptions.length && !actionXmlid && !targetActionXmlid)) return null;
          const mappedItem: HandlingEntryItem = {
            key: String(item.key || `${String(group.key || 'group')}.${itemIndex + 1}`).trim(),
            label,
            business_category_code: categoryCode || undefined,
            action_xmlid: actionXmlid || targetActionXmlid,
            entry_mode: String(item.entry_mode || '').trim() || undefined,
            business_category_options: categoryOptions,
            target,
          };
          return mappedItem;
        })
        .filter((item): item is HandlingEntryItem => Boolean(item));
      if (!items.length) return null;
      return {
        key: String(group.key || `group-${groupIndex + 1}`).trim(),
        title: String(group.title || group.key || `入口 ${groupIndex + 1}`).trim(),
        items,
      };
    })
    .filter((group): group is HandlingEntryGroup => Boolean(group));
});

const handlingEntryItemCount = computed(() => handlingEntryGroups.value.reduce((total, group) => total + group.items.length, 0));

function hasHandlingEntryCatalog(currentScene: Scene | null) {
  const catalog = currentScene?.scene_ready?.handling_entry_catalog;
  return Boolean(
    catalog
    && typeof catalog === 'object'
    && String((catalog as Record<string, unknown>).contract_version || '').trim() === 'handling_entry_catalog.v1',
  );
}

const idleDiagnosticMessage = computed(() => {
  const sceneKey = String(route.meta?.sceneKey || route.params.sceneKey || '').trim();
  const hint = pageText(
    'status_idle_diag_hint',
    '当前场景暂无可展示内容。',
  );
  return `${pageText('status_idle_diag_scene_prefix', '场景')}：${sceneKey || '-'}；${hint}`;
});

const runtimeDiagnosticTitle = computed(() => {
  const statusKey = String(resolveSceneRuntimeStatus() || '').trim();
  if (!statusKey) return pageText('runtime_diag_title_default', '场景运行状态');
  return pageText(`runtime_diag_title_${statusKey.toLowerCase()}`, statusKey);
});

const runtimeDiagnosticMessage = computed(() => {
  const runtime = resolveSceneRuntime();
  const statusKey = String(resolveSceneRuntimeStatus() || '').trim();
  const currentState = String(runtime.current_state || '').trim();
  const missingRequiredCount = Number(runtime.missing_required_count || 0);
  const activeTransitionCount = Number(runtime.active_transition_count || 0);
  const bridgeAligned = isSceneRuntimeBridgeAligned();
  const parts: string[] = [];

  if (statusKey && statusKey !== 'ready') {
    parts.push(`${pageText('runtime_diag_status_prefix', '运行状态')}：${statusKey}`);
  }
  if (currentState) {
    parts.push(`${pageText('runtime_diag_state_prefix', '记录状态')}：${currentState}`);
  }
  if (missingRequiredCount > 0) {
    parts.push(`${pageText('runtime_diag_missing_required_prefix', '缺少必填项')}：${missingRequiredCount}`);
  }
  if (activeTransitionCount > 0) {
    parts.push(`${pageText('runtime_diag_transition_prefix', '可执行流转')}：${activeTransitionCount}`);
  }
  if (!bridgeAligned) {
    parts.push(pageText('runtime_diag_alignment_mismatch', '当前场景语义尚未完全对齐。'));
  }

  return parts.join('；');
});

function asRuntimeRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? value as Record<string, unknown> : {};
}

function resolveSceneRuntime() {
  const currentScene = scene.value;
  if (!currentScene) return {};
  const runtimeSources = [
    currentScene.runtime_handoff_surface,
    currentScene.scene_ready?.runtime_handoff_surface,
    currentScene.scene_ready?.runtime_policy,
    currentScene.page?.runtime,
    currentScene.validation_surface,
  ];
  for (const item of runtimeSources) {
    const runtime = asRuntimeRecord(item);
    if (Object.keys(runtime).length) {
      return runtime;
    }
  }
  return {};
}

function resolveSceneRuntimeStatus() {
  const runtime = resolveSceneRuntime();
  const statusCandidates = [
    runtime.runtime_status,
    runtime.status,
    runtime.delivery_mode,
    runtime.family,
  ];
  for (const item of statusCandidates) {
    const text = String(item || '').trim();
    if (text) return text;
  }
  return '';
}

function isSceneRuntimeBridgeAligned() {
  const runtime = resolveSceneRuntime();
  if (typeof runtime.bridge_aligned === 'boolean') {
    return runtime.bridge_aligned;
  }
  if (typeof runtime.semantic_bridge_aligned === 'boolean') {
    return runtime.semantic_bridge_aligned;
  }
  return true;
}

const sceneResolveSignature = computed(() => JSON.stringify({
  path: route.path,
  sceneKey: String(route.params.sceneKey || route.meta?.sceneKey || '').trim(),
  actionId: Number(route.query.action_id || 0) || 0,
  menuId: Number(route.query.menu_id || 0) || 0,
  model: String(route.query.model || '').trim(),
  recordId: String(route.query.record_id || '').trim(),
  sceneQueryKey: String(route.query.scene_key || '').trim(),
  releaseProduct: String(route.query.release_product || '').trim(),
  preset: String(route.query.preset || '').trim(),
  ctxSource: String(route.query.ctx_source || '').trim(),
  search: String(route.query.search || '').trim(),
  projectId: String(route.query.project_id || '').trim(),
  entryContext: String(route.query.entry_context || '').trim(),
}));
function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
}

function asRouteQuery(query: Record<string, unknown>): LocationQueryRaw {
  return query as LocationQueryRaw;
}

function resolveTargetRecordEntry(target: SceneTarget) {
  const entryTarget = (target.entry_target && typeof target.entry_target === 'object')
    ? target.entry_target as Record<string, unknown>
    : undefined;
  const recordEntry = (entryTarget?.record_entry && typeof entryTarget.record_entry === 'object')
    ? entryTarget.record_entry as Record<string, unknown>
    : undefined;
  const model = String(recordEntry?.model || target.model || route.query.model || '').trim();
  const rawRecordId = recordEntry?.record_id ?? target.record_id ?? route.query.record_id;
  const recordId = resolveRecordId(rawRecordId);
  const actionId = Number(recordEntry?.action_id || target.action_id || route.query.action_id || 0);
  const menuId = Number(recordEntry?.menu_id || target.menu_id || route.query.menu_id || 0);
  return {
    model,
    recordId,
    actionId: Number.isFinite(actionId) && actionId > 0 ? actionId : 0,
    menuId: Number.isFinite(menuId) && menuId > 0 ? menuId : 0,
  };
}

function resolveSceneSwitchQuery(scene: Scene) {
  const next: Record<string, unknown> = {
    ...resolveWorkspaceContextQuery(),
  };
  const releaseProduct = String(route.query.release_product || '').trim();
  if (releaseProduct) {
    next.release_product = releaseProduct;
  }
  if (scene.target.menu_id) {
    next.menu_id = scene.target.menu_id;
  }
  return next;
}

function resolveSceneSwitchFallbackQuery() {
  const next: Record<string, unknown> = {
    ...resolveWorkspaceContextQuery(),
  };
  const releaseProduct = String(route.query.release_product || '').trim();
  if (releaseProduct) {
    next.release_product = releaseProduct;
  }
  return next;
}

function handleSceneBlockAction(payload: { block: Record<string, unknown>; action: Record<string, unknown> }) {
  const action = payload.action || {};
  const target = (action.target && typeof action.target === 'object' && !Array.isArray(action.target))
    ? action.target as Record<string, unknown>
    : {};
  const route = String(target.route || '').trim();
  if (route) {
    void router.push({ path: route, query: asRouteQuery(resolveWorkspaceContextQuery() as Record<string, unknown>) });
    return;
  }
  const sceneKey = String(target.scene_key || '').trim();
  if (sceneKey) {
    const sceneNode = getSceneByKey(sceneKey);
    void router.push(buildCanonicalSceneRouteTarget(sceneKey, {
      scene: sceneNode,
      query: asRouteQuery(resolveWorkspaceContextQuery() as Record<string, unknown>),
      menuId: sceneNode?.target?.menu_id,
      actionId: sceneNode?.target?.action_id,
    }));
  }
}

function isHandlingEntryActionable(item: HandlingEntryItem) {
  const target = item.target || {};
  return Boolean(
    String(target.route || '').trim()
    || String(target.scene_key || '').trim()
    || String(target.action_xmlid || item.action_xmlid || '').trim()
    || Number(target.action_id || target.menu_id || 0) > 0
  );
}

function openHandlingEntry(item: HandlingEntryItem) {
  if (!isHandlingEntryActionable(item)) return;
  const target: Record<string, unknown> = {
    ...(item.target || {}),
    action_xmlid: String(item.target?.action_xmlid || item.action_xmlid || '').trim() || undefined,
  };
  const routeTarget = String(target.route || '').trim();
  const workspaceContextQuery = resolveWorkspaceContextQuery() as Record<string, unknown>;
  if (routeTarget) {
    void router.push({ path: routeTarget, query: asRouteQuery(workspaceContextQuery) });
    return;
  }
  const sceneKey = String(target.scene_key || '').trim();
  if (sceneKey) {
    const targetScene = getSceneByKey(sceneKey);
    void router.push(buildCanonicalSceneRouteTarget(sceneKey, {
      scene: targetScene,
      query: asRouteQuery(workspaceContextQuery),
      menuId: targetScene?.target?.menu_id,
      actionId: targetScene?.target?.action_id,
    }));
    return;
  }
  const resolvedAction = resolveVisibleActionTarget(target as SceneTarget, currentSceneKey.value);
  if (!resolvedAction) return;
  void router.push({
    path: `/a/${resolvedAction.actionId}`,
    query: asRouteQuery({
      ...workspaceContextQuery,
      menu_id: Number(resolvedAction.menuId || 0) || undefined,
      action_id: resolvedAction.actionId,
      business_category_code: item.business_category_code || undefined,
    }),
  });
}

async function hydrateSceneReadyForCurrentScene(sceneKey: string) {
  const key = String(sceneKey || '').trim();
  if (!key || sceneReadyHydrateRequested.value) {
    return false;
  }
  sceneReadyHydrateRequested.value = true;
  try {
    const result = await intentRequest<Record<string, unknown>>({
      intent: 'system.init',
      params: {
        scene: 'web',
        with_preload: false,
        scene_ready_mode: 'full',
        with: ['workspace_home'],
        ...(config.startupRootXmlid ? { root_xmlid: config.startupRootXmlid } : {}),
        scene_key: key,
      },
      meta: { startup_chain_bypass: true },
    });
    const contract = result.scene_ready_contract_v1;
    if (contract && typeof contract === 'object' && Array.isArray((contract as Record<string, unknown>).scenes)) {
      const readyContract = contract as Record<string, unknown>;
      session.sceneReadyContractV1 = readyContract as never;
      setSceneRegistryFromSceneReadyContract(readyContract as never);
      return true;
    }
  } catch (err) {
    // Ignore hydration failures here; the existing fallback rendering can continue.
    // eslint-disable-next-line no-console
    console.warn('[scene-view] scene-ready hydration failed', err);
  }
  return false;
}


const sceneViewSwitchOptions = computed(() => {
  const currentScene = scene.value;
  const switchSurface = (currentScene?.scene_ready?.switch_surface || {}) as Record<string, unknown>;
  const items = Array.isArray(switchSurface.items)
    ? switchSurface.items as Array<Record<string, unknown>>
    : [];
  if (!items.length) return [];
  return items
    .map((item) => {
      const key = String(item.key || '').trim();
      if (!key) return null;
      const scene = getSceneByKey(key);
      const route = String(item.route || scene?.route || `/s/${key}`).trim();
      return {
        key,
        label: String(item.label || scene?.label || key).trim(),
      route,
      active: Boolean(item.active),
      menuId: Number(scene?.target?.menu_id || 0) || undefined,
    };
  })
    .filter((item): item is { key: string; label: string; route: string; active: boolean; menuId: number | undefined } => Boolean(item))
    .filter((item) => Boolean(item.key && item.route));
});

const productDeliverySurface = computed(() => {
  const currentScene = scene.value;
  const surface = (currentScene?.scene_ready?.product_delivery_surface || {}) as Record<string, unknown>;
  const deliveryMode = String(surface.delivery_mode || '').trim();
  if (!deliveryMode) {
    return {
      visible: false,
      advisoryOnly: false,
      title: '',
      message: '',
      actionLabel: '',
      actionDisabled: true,
      finalScene: '',
    };
  }

  const entryAction = (surface.entry_action && typeof surface.entry_action === 'object')
    ? surface.entry_action as Record<string, unknown>
    : {};
  const finalScene = String(surface.final_scene || '').trim();
  const advisoryOnly = deliveryMode === 'advisory_only';
  const actionLabel = String(entryAction.label || '').trim();
  const title = advisoryOnly
    ? pageText('scene_delivery_title_advisory', '当前场景提供下一步建议')
    : pageText('scene_delivery_title_direct', '当前场景已准备好交付入口');
  const message = advisoryOnly
    ? pageText('scene_delivery_message_advisory', '当前阶段保持 advisory-only，由后端语义决定下一步提示，不在前端扩展深链行为。')
    : pageText('scene_delivery_message_direct', '当前阶段使用后端提供的交付语义，统一呈现 direct delivery 入口，不在前端推导业务规则。');

  return {
    visible: true,
    advisoryOnly,
    title,
    message,
    actionLabel,
    actionDisabled: !finalScene || finalScene === currentSceneKey.value,
    finalScene,
  };
});

function hasConsumableDeliveryRoot(scene: Scene | null) {
  const currentScene = scene || null;
  if (!currentScene) {
    return false;
  }
  const runtimeHandoff = (currentScene.runtime_handoff_surface && typeof currentScene.runtime_handoff_surface === 'object')
    ? currentScene.runtime_handoff_surface as Record<string, unknown>
    : {};
  const productDelivery = (currentScene.scene_ready?.product_delivery_surface && typeof currentScene.scene_ready.product_delivery_surface === 'object')
    ? currentScene.scene_ready.product_delivery_surface as Record<string, unknown>
    : {};
  const handlingCatalog = (currentScene.scene_ready?.handling_entry_catalog && typeof currentScene.scene_ready.handling_entry_catalog === 'object')
    ? currentScene.scene_ready.handling_entry_catalog as Record<string, unknown>
    : {};
  return Boolean(
    String(runtimeHandoff.final_scene || '').trim()
    || String(productDelivery.final_scene || '').trim()
    || String(productDelivery.delivery_mode || '').trim()
    || String(handlingCatalog.contract_version || '').trim(),
  );
}

function openSiblingScene(sceneKey: string) {
  const target = getSceneByKey(sceneKey);
  router.replace(buildCanonicalSceneRouteTarget(sceneKey, {
    scene: target,
    query: asRouteQuery(target ? resolveSceneSwitchQuery(target) : resolveSceneSwitchFallbackQuery()),
    menuId: target?.target?.menu_id,
    actionId: target?.target?.action_id,
  })).catch(() => {});
}

function openProductDeliveryTarget() {
  const targetSceneKey = productDeliverySurface.value.finalScene;
  if (!targetSceneKey || targetSceneKey === currentSceneKey.value) {
    return;
  }
  const target = getSceneByKey(targetSceneKey);
  router.replace(buildCanonicalSceneRouteTarget(targetSceneKey, {
    scene: target,
    query: asRouteQuery(target ? resolveSceneSwitchQuery(target) : resolveSceneSwitchFallbackQuery()),
    menuId: target?.target?.menu_id,
    actionId: target?.target?.action_id,
  })).catch(() => {});
}
function sanitizeWorkspaceContextForLayout(
  layoutKind: 'workspace' | 'record' | 'list' | 'ledger' | 'kanban' | 'dashboard',
  raw: Record<string, unknown>,
) {
  if (layoutKind !== 'list' && layoutKind !== 'ledger') {
    return raw;
  }
  const next = { ...raw };
  delete next.project_id;
  return next;
}

function isPortalPath(url: string) {
  return url.startsWith('/portal/');
}

function goWorkbench(reason?: string) {
  const query: Record<string, string> = {};
  if (reason) {
    query.reason = reason;
    query.scene = String(route.params.sceneKey || '');
  }
  router.replace({
    name: 'workbench',
    query,
  }).catch(() => {});
}

function goUnifiedHome() {
  router.replace({
    path: '/',
    query: resolveWorkspaceContextQuery(),
  }).catch(() => {});
}

async function executeHeaderAction(actionKey: string) {
  const key = String(actionKey || '').trim();
  if (!key) return;
  const handled = await executePageContractAction({
    actionKey: key,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: resolveWorkspaceContextQuery() as LocationQueryRaw,
    onRefresh: resolveScene,
    onFallback: () => {
      goWorkbench(ErrorCodes.ACT_UNSUPPORTED_TYPE);
      return true;
    },
  });
  if (!handled) goWorkbench(ErrorCodes.ACT_UNSUPPORTED_TYPE);
}

function resolveRecordId(targetRecord: unknown) {
  if (typeof targetRecord === 'string' && targetRecord.startsWith(':')) {
    const key = targetRecord.slice(1);
    const raw = route.params[key];
    if (typeof raw === 'string' || typeof raw === 'number') {
      return raw;
    }
  }
  return targetRecord;
}

function resolveVisibleActionTarget(target: SceneTarget, sceneKey = '') {
  const isSceneContractNav = (() => {
    const navMeta = (session.initMeta as Record<string, unknown> | null)?.nav_meta as Record<string, unknown> | undefined;
    if (String(navMeta?.nav_source || '') === 'scene_contract_v1') {
      return true;
    }
    const walk = (nodes: NavNode[]): boolean => {
      for (const node of nodes || []) {
        if (String(node.meta?.scene_source || '') === 'scene_contract') {
          return true;
        }
        if (node.children?.length && walk(node.children)) {
          return true;
        }
      }
      return false;
    };
    return walk(session.menuTree || []);
  })();

  const normalizedSceneKey = String(sceneKey || '').trim();
  if (normalizedSceneKey) {
    const hinted = session.sceneActionHints?.[normalizedSceneKey];
    const hintedActionId = Number(hinted?.actionId || 0);
    if (hintedActionId > 0) {
      if (!session.menuTree.length || findActionMeta(session.menuTree, hintedActionId) || isSceneContractNav) {
        return {
          actionId: hintedActionId,
          menuId: Number(hinted?.menuId || target.menu_id || 0) || undefined,
        };
      }
    }
  }

  const actionId = Number(target.action_id || 0);
  if (actionId > 0) {
    const targetRoute = String(target.route || '').trim();
    if (normalizedSceneKey && resolveRoutePathOnly(targetRoute) === `/s/${normalizedSceneKey}`) {
      return { actionId, menuId: Number(target.menu_id || 0) || undefined };
    }
    if (!session.menuTree.length || findActionMeta(session.menuTree, actionId) || isSceneContractNav) {
      return { actionId, menuId: Number(target.menu_id || 0) || undefined };
    }
  }

  const targetMenuId = Number(target.menu_id || 0);
  if (targetMenuId > 0) {
    const menuNode = findMenuNode(session.menuTree, targetMenuId);
    if (menuNode?.meta?.action_id) {
      return {
        actionId: menuNode.meta.action_id,
        menuId: Number(menuNode.menu_id || menuNode.id || targetMenuId) || undefined,
      };
    }
  }

  const menuXmlid = String(target.menu_xmlid || '').trim();
  if (menuXmlid) {
    const menuNode = findActionNodeByMenuXmlid(session.menuTree, menuXmlid);
    if (menuNode?.meta?.action_id) {
      return {
        actionId: menuNode.meta.action_id,
        menuId: Number(menuNode.menu_id || menuNode.id || 0) || undefined,
      };
    }
  }

  const actionXmlid = String(target.action_xmlid || '').trim();
  if (actionXmlid) {
    const actionNode = findActionNodeByActionXmlid(session.menuTree, actionXmlid);
    if (actionNode?.meta?.action_id) {
      return {
        actionId: actionNode.meta.action_id,
        menuId: Number(actionNode.menu_id || actionNode.id || target.menu_id || 0) || undefined,
      };
    }
  }

  const model = String(target.model || '').trim();
  if (model) {
    const modelNode = findActionNodeByModelRef(session.menuTree, model);
    if (modelNode?.meta?.action_id) {
      return {
        actionId: modelNode.meta.action_id,
        menuId: Number(modelNode.menu_id || modelNode.id || target.menu_id || 0) || undefined,
      };
    }
  }

  if (normalizedSceneKey) {
    const sceneNode = findActionNodeBySceneKey(session.menuTree, normalizedSceneKey);
    if (sceneNode?.meta?.action_id) {
      return {
        actionId: sceneNode.meta.action_id,
        menuId: Number(sceneNode.menu_id || sceneNode.id || 0) || undefined,
      };
    }
  }

  const routeActionId = Number(route.query.action_id || 0);
  if (routeActionId > 0) {
    return {
      actionId: routeActionId,
      menuId: Number(route.query.menu_id || 0) || undefined,
    };
  }

  return null;
}

function isSameRouteTarget(targetRoute: string, query: Record<string, unknown>) {
  const raw = String(targetRoute || '').trim();
  if (!raw) return false;
  const [pathOnly, queryRaw] = raw.split('?', 2);
  if (pathOnly !== route.path) return false;
  if (!queryRaw) {
    return Object.keys(query || {}).length === 0 && Object.keys(route.query || {}).length === 0;
  }
  const targetQuery = new URLSearchParams(queryRaw);
  const currentQuery = new URLSearchParams();
  const merged = query || {};
  Object.entries(merged).forEach(([k, v]) => {
    if (v === undefined || v === null || v === '') return;
    currentQuery.set(k, String(v));
  });
  return targetQuery.toString() === currentQuery.toString();
}

function fallbackSceneFromSceneReady(sceneKey: string): Scene | null {
  const key = String(sceneKey || '').trim();
  if (!key) {
    return null;
  }
  const contract = session.sceneReadyContractV1;
  const rows = Array.isArray(contract?.scenes) ? contract.scenes : [];
  for (const item of rows) {
    if (!item || typeof item !== 'object') continue;
    const row = item as Record<string, unknown>;
    const scene = (row.scene && typeof row.scene === 'object') ? row.scene as Record<string, unknown> : {};
    const page = (row.page && typeof row.page === 'object') ? row.page as Record<string, unknown> : {};
    const meta = (row.meta && typeof row.meta === 'object') ? row.meta as Record<string, unknown> : {};
    const target = (meta.target && typeof meta.target === 'object') ? meta.target as Record<string, unknown> : {};
    const validationSurface = (row.validation_surface && typeof row.validation_surface === 'object')
      ? row.validation_surface as Record<string, unknown>
      : {};
    const rowKey = String(scene.key || page.scene_key || '').trim();
    if (rowKey !== key) continue;
    const routePath = String(page.route || target.route || `/s/${key}`).trim() || `/s/${key}`;
    const actionId = Number(target.action_id || 0);
    const menuId = Number(target.menu_id || 0);
    return {
      key,
      label: String(scene.title || key),
      route: routePath,
      target: {
        route: routePath,
        action_id: actionId > 0 ? actionId : undefined,
        menu_id: menuId > 0 ? menuId : undefined,
      },
      validation_surface: validationSurface,
      layout: resolveSceneLayout(null),
      capabilities: [],
      breadcrumbs: [],
      tiles: [],
    };
  }
  return null;
}

function fallbackSceneFromEntryIntent(sceneKey: string): Scene | null {
  const key = String(sceneKey || '').trim();
  if (!sceneContractEntryIntentMap[key]) return null;
  return {
    key,
    label: key === 'dashboard.company' ? '公司驾驶舱' : '角色首页',
    route: `/s/${key}`,
    target: {
      route: `/s/${key}`,
    },
    page: {
      key,
      page_type: 'dashboard',
      layout_mode: 'block_grid',
    },
    layout: resolveSceneLayout(null),
    capabilities: [],
    breadcrumbs: [],
    tiles: [],
  };
}

function resolveRoutePathOnly(targetRoute: string) {
  const raw = String(targetRoute || '').trim();
  if (!raw) return '';
  return raw.split('?', 2)[0] || '';
}

function resolveCanonicalSceneOwnerQuery(sceneKey: string, workspaceContextQuery: Record<string, unknown>) {
  return {
    scene_key: sceneKey || undefined,
    ...workspaceContextQuery,
  };
}

function resolveSceneActionOrder(scene: Scene, target: SceneTarget, sceneKey: string) {
  const explicit = String(route.query.order || route.query.sort || '').trim();
  if (explicit) return explicit;
  return resolveSceneDefaultOrder(sceneKey, { ...scene, target });
}

function isCanonicalSceneOwnerTarget(target: SceneTarget, sceneKey: string) {
  const normalizedSceneKey = String(sceneKey || '').trim();
  if (!normalizedSceneKey) {
    return false;
  }
  const targetPath = resolveRoutePathOnly(String(target.route || ''));
  if (targetPath !== `/s/${normalizedSceneKey}`) {
    return false;
  }
  if (Number(target.action_id || 0) > 0) {
    return false;
  }
  if (Number(target.record_id || 0) > 0) {
    return false;
  }
  if (String(target.model || '').trim()) {
    return false;
  }
  const entryTarget = (target.entry_target && typeof target.entry_target === 'object')
    ? target.entry_target as Record<string, unknown>
    : {};
  const recordEntry = (entryTarget.record_entry && typeof entryTarget.record_entry === 'object')
    ? entryTarget.record_entry as Record<string, unknown>
    : {};
  return Number(recordEntry.action_id || 0) <= 0 && Number(recordEntry.record_id || 0) <= 0;
}

async function resolveScene() {
  try {
    status.value = 'loading';
    clearError();
    scene.value = null;
    embeddedActionId.value = 0;
    embeddedRecordActionId.value = 0;
    validationHint.value = '';
    const sceneKey = String(route.meta?.sceneKey || route.params.sceneKey || '');
    let resolvedScene = getSceneByKey(sceneKey) || fallbackSceneFromSceneReady(sceneKey) || fallbackSceneFromEntryIntent(sceneKey);
    if (!resolvedScene && sceneKey) {
      await hydrateSceneReadyForCurrentScene(sceneKey);
      resolvedScene = getSceneByKey(sceneKey) || fallbackSceneFromSceneReady(sceneKey) || fallbackSceneFromEntryIntent(sceneKey);
    }
    if (!resolvedScene) {
      setError(new Error(`${pageText('error_scene_not_found', '未找到场景')}：${sceneKey}`), pageText('error_scene_not_found', '未找到场景'));
      errorCopy.value = resolveErrorCopy(error.value, pageText('error_fallback', '场景加载失败'));
      status.value = 'error';
      return;
    }
    scene.value = resolvedScene;
    if (!sceneBlocks.value.length || !hasHandlingEntryCatalog(scene.value)) {
      await hydrateSceneReadyForCurrentScene(sceneKey);
      scene.value = getSceneByKey(sceneKey) || resolvedScene;
    }
    if (sceneContractEntryIntentMap[sceneKey]) {
      status.value = 'idle';
      return;
    }

    const validationSurface = (resolvedScene.validation_surface && typeof resolvedScene.validation_surface === 'object')
      ? resolvedScene.validation_surface as Record<string, unknown>
      : {};
    const requiredFields = Array.isArray(validationSurface.required_fields)
      ? validationSurface.required_fields.map((item) => String(item || '').trim()).filter(Boolean)
      : [];
    if (requiredFields.length) {
      validationHint.value = `必填字段：${requiredFields.slice(0, 5).join('、')}${requiredFields.length > 5 ? ' 等' : ''}`;
    }

    const policy = evaluateCapabilityPolicy({ required: resolvedScene.capabilities || [], available: session.capabilities });
    if (policy.state !== 'enabled') {
      const missing = Array.isArray(policy.missing) ? policy.missing : [];
      const details = missing
        .map((key) => {
          const meta = session.capabilityCatalog[key];
          if (!meta) return key;
          const reason = String(meta.reason || '').trim();
          if (!reason) return meta.label || key;
          return `${meta.label || key}${pageText('forbidden_detail_reason_left', '（')}${reason}${pageText('forbidden_detail_reason_right', '）')}`;
        })
        .slice(0, 4);
      const level = String(session.productFacts.license?.level || '').trim();
      forbiddenCopy.value = {
        title:
          policy.state === 'disabled_permission'
            ? pageText('forbidden_title_permission', '权限不足')
            : pageText('forbidden_title', '能力未开通'),
        message: details.length
          ? `${pageText('forbidden_message_missing_prefix', '缺少能力：')}${details.join(pageText('forbidden_message_missing_sep', '、'))}`
          : pageText('forbidden_message_scope_missing', '当前角色能力范围不包含该场景所需能力。'),
        hint: level && level !== 'enterprise'
          ? `${pageText('forbidden_hint_license_prefix', '当前 License：')}${level}${pageText('forbidden_hint_license_suffix', '，可联系管理员评估升级或开通。')}`
          : pageText('forbidden_hint_default', '可联系管理员开通对应能力。'),
      };
      status.value = 'forbidden';
      return;
    }
    void trackSceneOpen(sceneKey).catch(() => {});

    const target = resolvedScene.target || {};
    const sceneLabel = String(resolvedScene.label || sceneKey || '').trim();
    const layout = resolveSceneLayout(resolvedScene);
    const workspaceContextQuery = sanitizeWorkspaceContextForLayout(
      layout.kind,
      resolveWorkspaceContextQuery() as Record<string, unknown>,
    );
    const canonicalOwnerQuery = resolveCanonicalSceneOwnerQuery(sceneKey, workspaceContextQuery);
    const hasForeignSceneQuery = Boolean(
      route.query.menu_id
      || route.query.action_id
      || route.query.scene_label
    );
    const hasActionRouteContext = Number(route.query.action_id || 0) > 0 || Number(route.query.menu_id || 0) > 0;
    if (hasForeignSceneQuery && !hasActionRouteContext && isCanonicalSceneOwnerTarget(target, sceneKey)) {
      await router.replace({ path: route.path, query: asRouteQuery(canonicalOwnerQuery) });
      return;
    }
    if (layout.kind === 'workspace') {
      if (hasHandlingEntryCatalog(resolvedScene)) {
        status.value = 'idle';
        return;
      }
      if (typeof target.route === 'string' && target.route.trim()) {
        const normalizedRoute = normalizeLegacyWorkbenchPath(target.route);
        if (isPortalPath(normalizedRoute)) {
          // Delivery product must stay in unified SPA; do not bridge to legacy /portal pages.
          goUnifiedHome();
          return;
        }
        const normalizedPathOnly = resolveRoutePathOnly(normalizedRoute);
        if (normalizedPathOnly && normalizedPathOnly !== route.path) {
          await router.replace({ path: normalizedRoute, query: asRouteQuery(workspaceContextQuery) });
          return;
        }
        // Keep evaluating action/menu/model targets for self-routed scene entries
        // such as /s/project.management?project_id=<id>.
      }
      const page = resolvedScene.page;
      const pageType = String(page?.page_type || '').trim().toLowerCase();
      const layoutMode = String(page?.layout_mode || '').trim().toLowerCase();
      if (pageType === 'dashboard' || layoutMode === 'dashboard') {
        status.value = 'idle';
        return;
      }
      // Workspace scene may still provide action/menu/model targets.
      const resolvedAction = resolveVisibleActionTarget(target, sceneKey);
      if (resolvedAction) {
        const defaultOrder = resolveSceneActionOrder(resolvedScene, target, sceneKey);
        const effectiveMenuId = Number(route.query.menu_id || 0) || Number(resolvedAction.menuId || 0) || undefined;
        const nextQuery = {
          menu_id: effectiveMenuId,
          action_id: resolvedAction.actionId,
          scene_key: sceneKey || undefined,
          scene_label: sceneLabel || undefined,
          order: defaultOrder || undefined,
          ...workspaceContextQuery,
        };
        const currentActionId = Number(route.query.action_id || 0);
        const currentMenuId = Number(route.query.menu_id || 0);
        const sameEmbeddedRouteState =
          currentActionId === resolvedAction.actionId
          && currentMenuId === Number(effectiveMenuId || 0)
          && String(route.query.scene_key || '') === sceneKey;
        if (!sameEmbeddedRouteState) {
          await router.replace({ path: route.path, query: asRouteQuery(nextQuery) });
          return;
        }
        embeddedActionId.value = resolvedAction.actionId;
        status.value = 'idle';
        return;
      }
      {
        const recordEntry = resolveTargetRecordEntry(target);
        if (recordEntry.model && recordEntry.recordId && recordEntry.actionId > 0) {
          const nextQuery = {
            menu_id: recordEntry.menuId || undefined,
            action_id: recordEntry.actionId,
            scene_key: sceneKey || undefined,
            scene_label: sceneLabel || undefined,
            model: recordEntry.model || undefined,
            record_id: recordEntry.recordId,
            ...workspaceContextQuery,
          };
          const sameEmbeddedRouteState =
            Number(route.query.action_id || 0) === recordEntry.actionId
            && Number(route.query.menu_id || 0) === Number(recordEntry.menuId || 0)
            && Number(route.query.record_id || 0) === recordEntry.recordId
            && String(route.query.model || '').trim() === String(recordEntry.model || '').trim()
            && String(route.query.scene_key || '') === sceneKey;
          if (!sameEmbeddedRouteState) {
            await router.replace({ path: route.path, query: asRouteQuery(nextQuery) });
            return;
          }
          embeddedRecordActionId.value = recordEntry.actionId;
          status.value = 'idle';
          return;
        }
      }
    }

    if (layout.kind === 'record') {
      const resolvedAction = resolveVisibleActionTarget(target, sceneKey);
      if (resolvedAction) {
        const defaultOrder = resolveSceneActionOrder(resolvedScene, target, sceneKey);
        const effectiveMenuId = Number(route.query.menu_id || 0) || Number(resolvedAction.menuId || 0) || undefined;
        const nextQuery = {
          menu_id: effectiveMenuId,
          action_id: resolvedAction.actionId,
          scene_key: sceneKey || undefined,
          scene_label: sceneLabel || undefined,
          order: defaultOrder || undefined,
          ...workspaceContextQuery,
        };
        const currentActionId = Number(route.query.action_id || 0);
        const currentMenuId = Number(route.query.menu_id || 0);
        const sameEmbeddedRouteState =
          currentActionId === resolvedAction.actionId
          && currentMenuId === Number(effectiveMenuId || 0)
          && String(route.query.scene_key || '') === sceneKey;
        if (!sameEmbeddedRouteState) {
          await router.replace({ path: route.path, query: asRouteQuery(nextQuery) });
          return;
        }
        embeddedRecordActionId.value = resolvedAction.actionId;
        status.value = 'idle';
        return;
      }
      {
        const recordEntry = resolveTargetRecordEntry(target);
        if (recordEntry.model && recordEntry.recordId && recordEntry.actionId > 0) {
          const nextQuery = {
            menu_id: recordEntry.menuId || undefined,
            action_id: recordEntry.actionId,
            scene_key: sceneKey || undefined,
            scene_label: sceneLabel || undefined,
            model: recordEntry.model,
            record_id: recordEntry.recordId,
            ...workspaceContextQuery,
          };
          const sameEmbeddedRouteState =
            Number(route.query.action_id || 0) === recordEntry.actionId
            && Number(route.query.menu_id || 0) === Number(recordEntry.menuId || 0)
            && Number(route.query.record_id || 0) === recordEntry.recordId
            && String(route.query.model || '').trim() === recordEntry.model
            && String(route.query.scene_key || '') === sceneKey;
          if (!sameEmbeddedRouteState) {
            await router.replace({ path: route.path, query: asRouteQuery(nextQuery) });
            return;
          }
          embeddedRecordActionId.value = recordEntry.actionId;
          status.value = 'idle';
          return;
        }
      }
      if (typeof target.menu_xmlid === 'string' && target.menu_xmlid.trim()) {
        const menuNode = findActionNodeByMenuXmlid(session.menuTree, target.menu_xmlid);
        if (menuNode?.menu_id || menuNode?.id) {
          await router.replace({
            path: `/m/${menuNode.menu_id || menuNode.id}`,
            query: asRouteQuery(workspaceContextQuery),
          });
          return;
        }
      }
      if (target.action_id && !session.menuTree.length) {
        const nextQuery = {
          menu_id: target.menu_id || undefined,
          action_id: target.action_id,
          scene_key: sceneKey || undefined,
          scene_label: sceneLabel || undefined,
          ...workspaceContextQuery,
        };
        const sameEmbeddedRouteState =
          Number(route.query.action_id || 0) === Number(target.action_id || 0)
          && Number(route.query.menu_id || 0) === Number(target.menu_id || 0)
          && String(route.query.scene_key || '') === sceneKey;
        if (!sameEmbeddedRouteState) {
          await router.replace({ path: route.path, query: asRouteQuery(nextQuery) });
          return;
        }
        embeddedRecordActionId.value = Number(target.action_id || 0);
        status.value = 'idle';
        return;
      }
    }

    if (layout.kind === 'list' || layout.kind === 'ledger') {
      const resolvedAction = resolveVisibleActionTarget(target, sceneKey);
      if (resolvedAction) {
        const defaultOrder = resolveSceneActionOrder(resolvedScene, target, sceneKey);
        const effectiveMenuId = Number(route.query.menu_id || 0) || Number(resolvedAction.menuId || 0) || undefined;
        const nextQuery = {
          menu_id: effectiveMenuId,
          action_id: resolvedAction.actionId,
          scene_key: sceneKey || undefined,
          scene_label: sceneLabel || undefined,
          order: defaultOrder || undefined,
          ...workspaceContextQuery,
        };
        const currentActionId = Number(route.query.action_id || 0);
        const currentMenuId = Number(route.query.menu_id || 0);
        const sameEmbeddedRouteState =
          currentActionId === resolvedAction.actionId
          && currentMenuId === Number(effectiveMenuId || 0)
          && String(route.query.scene_key || '') === sceneKey;
        if (!sameEmbeddedRouteState) {
          await router.replace({ path: route.path, query: asRouteQuery(nextQuery) });
          return;
        }
        embeddedActionId.value = resolvedAction.actionId;
        status.value = 'idle';
        return;
      }
      {
        const recordEntry = resolveTargetRecordEntry(target);
        if (recordEntry.model && recordEntry.recordId && recordEntry.actionId > 0) {
          const nextQuery = {
            menu_id: recordEntry.menuId || undefined,
            action_id: recordEntry.actionId,
            scene_key: sceneKey || undefined,
            scene_label: sceneLabel || undefined,
            model: recordEntry.model || undefined,
            record_id: recordEntry.recordId,
            ...workspaceContextQuery,
          };
          const sameEmbeddedRouteState =
            Number(route.query.action_id || 0) === recordEntry.actionId
            && Number(route.query.menu_id || 0) === Number(recordEntry.menuId || 0)
            && Number(route.query.record_id || 0) === recordEntry.recordId
            && String(route.query.model || '').trim() === String(recordEntry.model || '').trim()
            && String(route.query.scene_key || '') === sceneKey;
          if (!sameEmbeddedRouteState) {
            await router.replace({ path: route.path, query: asRouteQuery(nextQuery) });
            return;
          }
          embeddedRecordActionId.value = recordEntry.actionId;
          status.value = 'idle';
          return;
        }
      }
    }

    if (target.route) {
      if (isPortalPath(target.route)) {
        goUnifiedHome();
        return;
      }
      if (!isSameRouteTarget(target.route, workspaceContextQuery)) {
        await router.replace({ path: target.route, query: asRouteQuery(workspaceContextQuery) });
        return;
      }
      if (hasConsumableDeliveryRoot(resolvedScene)) {
        status.value = 'idle';
        return;
      }
      setError(
        new Error(pageText('error_scene_render_target_missing', '缺少场景渲染目标')),
        pageText('error_scene_render_target_missing', '缺少场景渲染目标'),
        ErrorCodes.SCENE_KIND_UNSUPPORTED,
      );
      errorCopy.value = resolveErrorCopy(error.value, pageText('error_fallback', '场景加载失败'));
      status.value = 'error';
      return;
    }

    setError(
      new Error(pageText('error_scene_target_unsupported', '')),
      pageText('error_scene_target_unsupported', ''),
      ErrorCodes.SCENE_KIND_UNSUPPORTED,
    );
    errorCopy.value = resolveErrorCopy(error.value, pageText('error_fallback', '场景加载失败'));
    status.value = 'error';
  } catch (err) {
    setError(
      err instanceof Error ? err : new Error(pageText('error_scene_resolve_failed', '场景解析失败')),
      pageText('error_scene_resolve_failed', '场景解析失败'),
    );
    errorCopy.value = resolveErrorCopy(error.value, pageText('error_fallback', '场景加载失败'));
    status.value = 'error';
  }
}

function findActionNodeByMenuXmlid(nodes: NavNode[], menuXmlid: string): NavNode | null {
  if (!menuXmlid) return null;
  const walk = (items: NavNode[]): NavNode | null => {
    for (const node of items) {
      const xmlid = String((node as NavNode & { xmlid?: string }).xmlid || node.meta?.menu_xmlid || '').trim();
      if (xmlid && xmlid === menuXmlid) {
        return node;
      }
      if (node.children?.length) {
        const found = walk(node.children);
        if (found) return found;
      }
    }
    return null;
  };
  return walk(nodes) || null;
}

function findActionNodeBySceneKey(nodes: NavNode[], sceneKey: string): NavNode | null {
  if (!sceneKey) return null;
  const wanted = String(sceneKey || '').trim();
  const walk = (items: NavNode[]): NavNode | null => {
    for (const node of items) {
      const nodeSceneKey = String(
        (node as NavNode & { scene_key?: string; sceneKey?: string }).scene_key
          || (node as NavNode & { scene_key?: string; sceneKey?: string }).sceneKey
          || node.meta?.scene_key
          || '',
      ).trim();
      if (nodeSceneKey === wanted && node.meta?.action_id) {
        return node;
      }
      if (node.children?.length) {
        const found = walk(node.children);
        if (found) return found;
      }
    }
    return null;
  };
  return walk(nodes) || null;
}

function findActionNodeByActionXmlid(nodes: NavNode[], actionXmlid: string): NavNode | null {
  if (!actionXmlid) return null;
  const wanted = String(actionXmlid || '').trim();
  const walk = (items: NavNode[]): NavNode | null => {
    for (const node of items) {
      const nodeActionXmlid = String(
        (node as NavNode & { action_xmlid?: string; actionXmlid?: string }).action_xmlid
          || (node as NavNode & { action_xmlid?: string; actionXmlid?: string }).actionXmlid
          || node.meta?.action_xmlid
          || '',
      ).trim();
      if (nodeActionXmlid === wanted && node.meta?.action_id) {
        return node;
      }
      if (node.children?.length) {
        const found = walk(node.children);
        if (found) return found;
      }
    }
    return null;
  };
  return walk(nodes) || null;
}

watch(
  sceneResolveSignature,
  () => {
    resolveScene();
  },
  { immediate: true }
);
</script>

<style scoped>
.scene {
  padding: 12px;
  min-width: 0;
}

.scene--compact-controls {
  padding: 2px 0 0;
}

.scene-top-controls {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
}

.scene-top-controls--compact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 4px;
  min-width: 0;
}

.scene-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scene-actions--compact {
  flex-wrap: wrap;
  gap: 4px;
  margin: 0;
  min-width: 0;
}

.scene-view-switch {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
}

.scene-view-switch--compact {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 0;
  min-width: 0;
}

.scene-view-switch__label {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--sc-app-text-secondary);
}

.scene-view-switch__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scene-view-switch--compact .scene-view-switch__chips {
  flex-wrap: wrap;
  gap: 4px;
  min-width: 0;
}

.scene-view-switch__chip {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
}

.scene-view-switch__chip.active {
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
  border-color: var(--sc-semantic-surface-interactive);
}

.scene-view-switch__chip:disabled {
  cursor: default;
  opacity: 0.75;
}

.scene-delivery {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
  padding: 14px 16px;
  border: 1px solid var(--sc-app-info-border);
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-info-bg);
}

.scene-delivery--advisory {
  background: var(--sc-app-warning-bg);
  border-color: var(--sc-app-warning-border);
}

.scene-delivery__copy {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.scene-delivery__eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--sc-app-text-secondary);
}

.scene-delivery__title {
  margin: 0;
  font-size: 16px;
  color: var(--sc-app-text-primary);
  overflow-wrap: anywhere;
}

.scene-delivery__message {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--sc-app-text-secondary);
  overflow-wrap: anywhere;
}

.scene-delivery__cta {
  white-space: nowrap;
}

.handling-surface {
  display: grid;
  gap: 12px;
  margin-bottom: 12px;
}

.handling-surface__header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
  padding: 2px 0;
  min-width: 0;
}

.handling-surface__eyebrow {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 700;
  color: var(--sc-app-text-secondary);
}

.handling-surface__title {
  margin: 0;
  font-size: 20px;
  color: var(--sc-app-text-primary);
}

.handling-surface__badge {
  flex: 0 0 auto;
  min-width: 34px;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 999px;
  padding: 4px 10px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--sc-app-text-secondary);
  background: var(--sc-app-panel);
}

.handling-surface__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}

.handling-group {
  display: grid;
  align-content: start;
  gap: 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  padding: 12px;
  min-width: 0;
}

.handling-group__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
}

.handling-group__header h4 {
  margin: 0;
  font-size: 15px;
  color: var(--sc-app-text-primary);
  overflow-wrap: anywhere;
}

.handling-group__header span {
  flex: 0 0 auto;
  min-width: 26px;
  border-radius: 999px;
  padding: 2px 8px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--sc-app-info-text);
  background: var(--sc-app-info-bg);
  border: 1px solid var(--sc-app-info-border);
}

.handling-group__items {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(148px, 1fr));
  gap: 8px;
}

.handling-item {
  display: grid;
  gap: 4px;
  min-height: 66px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 9px 10px;
  text-align: left;
  cursor: pointer;
}

.handling-item:hover:not(:disabled) {
  border-color: var(--sc-semantic-surface-interactive);
  box-shadow: 0 10px 22px var(--sc-app-focus-ring);
}

.handling-item:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.handling-item span {
  font-size: 13px;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.handling-item small {
  font-size: 11px;
  line-height: 1.25;
  color: var(--sc-app-text-secondary);
  overflow-wrap: anywhere;
}

.scene-top-controls--compact :deep(.ghost) {
  padding: 5px 11px;
  border-radius: 999px;
  white-space: normal;
  overflow-wrap: anywhere;
}

.scene-top-controls--compact .scene-view-switch__chip {
  padding: 5px 11px;
}

@media (max-width: 860px) {
  .scene-top-controls--compact {
    flex-wrap: wrap;
    align-items: stretch;
  }

  .scene-actions--compact,
  .scene-view-switch--compact .scene-view-switch__chips {
    flex-wrap: wrap;
  }

  .scene-delivery {
    flex-direction: column;
    align-items: stretch;
  }

  .handling-surface__header {
    align-items: stretch;
  }

  .handling-surface__grid {
    grid-template-columns: 1fr;
  }

  .handling-group__items {
    grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  }
}
</style>
