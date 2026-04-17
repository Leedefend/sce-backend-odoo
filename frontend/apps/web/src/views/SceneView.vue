<template>
  <section class="scene">
    <section v-if="headerActions.length" class="scene-actions">
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
    <section v-if="sceneViewSwitchOptions.length > 1" class="scene-view-switch">
      <p class="scene-view-switch__label">{{ pageText('scene_view_switch_label', '视图切换') }}</p>
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
      v-else-if="status === 'idle' && embeddedRecordActionId <= 0 && embeddedActionId <= 0"
      :title="pageText('status_idle_diag_title', '场景已加载，但没有可渲染目标')"
      :message="idleDiagnosticMessage"
      variant="info"
    />
    <StatusPanel
      v-if="status === 'idle' && validationHint"
      :title="pageText('validation_surface_title', '表单约束提示')"
      :message="validationHint"
      variant="info"
    />
    <StatusPanel
      v-if="status === 'idle' && runtimeDiagnosticMessage"
      :title="runtimeDiagnosticTitle"
      :message="runtimeDiagnosticMessage"
      variant="info"
    />
    <ContractFormPage v-if="status === 'idle' && embeddedRecordActionId > 0" />
    <ActionView v-else-if="status === 'idle' && embeddedActionId > 0" />
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router';
import ActionView from './ActionViewShell.vue';
import ContractFormPage from '../pages/ContractFormPage.vue';
import StatusPanel from '../components/StatusPanel.vue';
import { getSceneByKey, resolveSceneLayout } from '../app/resolvers/sceneRegistry';
import { useSessionStore } from '../stores/session';
import { evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { ErrorCodes } from '../app/error_codes';
import { resolveErrorCopy, useStatus } from '../composables/useStatus';
import { trackSceneOpen } from '../api/usage';
import { readWorkspaceContext } from '../app/workspaceContext';
import { normalizeLegacyWorkbenchPath } from '../app/routeQuery';
import { findActionMeta, findActionNodeByModel, findMenuNode } from '../app/menu';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import type { NavNode } from '@sc/schema';
import type { Scene, SceneTarget } from '../app/resolvers/sceneRegistry';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const pageContract = usePageContract('scene');
const pageText = pageContract.text;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const pageConsumerRuntime = pageContract.consumerRuntime;
const pageConsumerRuntimeStatus = pageContract.consumerRuntimeStatus;
const pageConsumerRuntimeBridgeAligned = pageContract.consumerRuntimeBridgeAligned;
const headerActions = computed(() => pageGlobalActions.value);
const findActionNodeByModelRef = findActionNodeByModel;
const status = ref<'loading' | 'error' | 'forbidden' | 'idle'>('loading');
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
const PROJECT_SCENE_SWITCH_MAP: Record<string, Array<{ key: string; label: string }>> = {
  'projects.list': [
    { key: 'projects.list', label: '列表' },
    { key: 'projects.ledger', label: '看板' },
  ],
  'projects.ledger': [
    { key: 'projects.list', label: '列表' },
    { key: 'projects.ledger', label: '看板' },
  ],
};

const idleDiagnosticMessage = computed(() => {
  const sceneKey = String(route.meta?.sceneKey || route.params.sceneKey || '').trim();
  const hint = pageText(
    'status_idle_diag_hint',
    '请检查 scene registry target/action 映射，或确认该场景是否已切换到 scene-ready 渲染路径。',
  );
  return `${pageText('status_idle_diag_scene_prefix', '场景')}：${sceneKey || '-'}；${hint}`;
});

const runtimeDiagnosticTitle = computed(() => {
  const statusKey = String(pageConsumerRuntimeStatus() || '').trim();
  if (statusKey === 'readonly') return pageText('runtime_diag_title_readonly', '场景当前为只读状态');
  if (statusKey === 'empty') return pageText('runtime_diag_title_empty', '场景当前为空态');
  if (statusKey === 'restricted') return pageText('runtime_diag_title_restricted', '场景访问受限');
  return pageText('runtime_diag_title_default', '场景运行态提示');
});

const runtimeDiagnosticMessage = computed(() => {
  const runtime = pageConsumerRuntime.value || {};
  const statusKey = String(pageConsumerRuntimeStatus() || '').trim();
  const currentState = String(runtime.current_state || '').trim();
  const missingRequiredCount = Number(runtime.missing_required_count || 0);
  const activeTransitionCount = Number(runtime.active_transition_count || 0);
  const bridgeAligned = pageConsumerRuntimeBridgeAligned();
  const parts: string[] = [];

  if (statusKey && statusKey !== 'ready') {
    parts.push(`${pageText('runtime_diag_status_prefix', '运行态状态')}：${statusKey}`);
  }
  if (currentState) {
    parts.push(`${pageText('runtime_diag_state_prefix', '当前记录状态')}：${currentState}`);
  }
  if (missingRequiredCount > 0) {
    parts.push(`${pageText('runtime_diag_missing_required_prefix', '缺失必填项')}：${missingRequiredCount}`);
  }
  if (activeTransitionCount > 0) {
    parts.push(`${pageText('runtime_diag_transition_prefix', '可用流转数')}：${activeTransitionCount}`);
  }
  if (!bridgeAligned) {
    parts.push(pageText('runtime_diag_alignment_mismatch', '前端消费状态与桥接断言存在未对齐项，请优先检查 contract diagnostics。'));
  }

  return parts.join('；');
});

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
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

const sceneViewSwitchOptions = computed(() => {
  const currentSceneKey = String(route.params.sceneKey || route.meta?.sceneKey || '').trim();
  const group = PROJECT_SCENE_SWITCH_MAP[currentSceneKey] || [];
  if (!group.length) return [];
  return group
    .map((item) => {
      const scene = getSceneByKey(item.key);
      return {
        key: item.key,
        label: item.label,
        route: scene?.route || `/s/${item.key}`,
        active: item.key === currentSceneKey,
        menuId: Number(scene?.target?.menu_id || 0) || undefined,
      };
    })
    .filter((item) => Boolean(item.key && item.route));
});

function openSiblingScene(sceneKey: string) {
  const target = getSceneByKey(sceneKey);
  router.replace({
    path: target?.route || `/s/${sceneKey}`,
    query: (target ? resolveSceneSwitchQuery(target) : resolveSceneSwitchFallbackQuery()) as LocationQueryRaw,
  }).catch(() => {});
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
  const matched = headerActions.value.find((item) => item.key === actionKey);
  if (matched?.disabled) {
    return;
  }
  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: resolveWorkspaceContextQuery(),
    onRefresh: resolveScene,
    onFallback: async (key) => {
      if (key === 'open_workbench') {
        goWorkbench();
        return true;
      }
      if (key === 'refresh_page' || key === 'refresh') {
        await resolveScene();
        return true;
      }
      return false;
    },
  });
  if (!handled) {
    goWorkbench(ErrorCodes.ACT_UNSUPPORTED_TYPE);
  }
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
        if (String((node.meta as Record<string, unknown> | undefined)?.scene_source || '') === 'scene_contract') {
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

async function resolveScene() {
  try {
    status.value = 'loading';
    clearError();
    embeddedActionId.value = 0;
    embeddedRecordActionId.value = 0;
    validationHint.value = '';
    const sceneKey = String(route.meta?.sceneKey || route.params.sceneKey || '');
    const scene = getSceneByKey(sceneKey);
    if (!scene) {
      goWorkbench(ErrorCodes.CONTRACT_CONTEXT_MISSING);
      return;
    }

    const validationSurface = (scene.validation_surface && typeof scene.validation_surface === 'object')
      ? scene.validation_surface as Record<string, unknown>
      : {};
    const requiredFields = Array.isArray(validationSurface.required_fields)
      ? validationSurface.required_fields.map((item) => String(item || '').trim()).filter(Boolean)
      : [];
    if (requiredFields.length) {
      validationHint.value = `必填字段：${requiredFields.slice(0, 5).join('、')}${requiredFields.length > 5 ? ' 等' : ''}`;
    }

    const policy = evaluateCapabilityPolicy({ required: scene.capabilities || [], available: session.capabilities });
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

    const target = scene.target || {};
    const sceneLabel = String(scene.label || sceneKey || '').trim();
    const layout = resolveSceneLayout(scene);
    const workspaceContextQuery = sanitizeWorkspaceContextForLayout(
      layout.kind,
      resolveWorkspaceContextQuery() as Record<string, unknown>,
    );
    if (layout.kind === 'workspace') {
      if (typeof target.route === 'string' && target.route.trim()) {
        const normalizedRoute = normalizeLegacyWorkbenchPath(target.route);
        if (isPortalPath(normalizedRoute)) {
          // Delivery product must stay in unified SPA; do not bridge to legacy /portal pages.
          goUnifiedHome();
          return;
        }
        if (normalizedRoute !== route.fullPath) {
          await router.replace({ path: normalizedRoute, query: workspaceContextQuery as LocationQueryRaw });
          return;
        }
        // Keep evaluating action/menu/model targets for self-routed scene entries
        // such as /s/project.management?project_id=<id>.
      }
      // Workspace scene may still provide action/menu/model targets.
      const resolvedAction = resolveVisibleActionTarget(target, sceneKey);
      if (resolvedAction) {
        await router.replace({
          path: `/a/${resolvedAction.actionId}`,
          query: {
            menu_id: resolvedAction.menuId,
            scene_key: sceneKey || undefined,
            scene_label: sceneLabel || undefined,
            ...workspaceContextQuery,
          },
        });
        return;
      }
      if (target.model && target.record_id) {
        const recordId = resolveRecordId(target.record_id);
        if (recordId) {
          await router.replace({
            path: `/r/${target.model}/${recordId}`,
            query: { menu_id: target.menu_id || undefined, action_id: target.action_id || undefined, ...workspaceContextQuery },
          });
          return;
        }
      }
    }

    if (layout.kind === 'record') {
      const resolvedAction = resolveVisibleActionTarget(target, sceneKey);
      if (resolvedAction) {
        const nextQuery = {
          menu_id: resolvedAction.menuId,
          action_id: resolvedAction.actionId,
          scene_key: sceneKey || undefined,
          scene_label: sceneLabel || undefined,
          ...workspaceContextQuery,
        };
        const currentActionId = Number(route.query.action_id || 0);
        const currentMenuId = Number(route.query.menu_id || 0);
        const sameEmbeddedRouteState =
          currentActionId === resolvedAction.actionId
          && currentMenuId === Number(resolvedAction.menuId || 0)
          && String(route.query.scene_key || '') === sceneKey;
        if (!sameEmbeddedRouteState) {
          await router.replace({ path: route.path, query: nextQuery });
          return;
        }
        embeddedRecordActionId.value = resolvedAction.actionId;
        status.value = 'idle';
        return;
      }
      if (target.model) {
        const recordId = resolveRecordId(target.record_id ?? route.params.id);
        if (recordId) {
          await router.replace({
            path: `/r/${target.model}/${recordId}`,
            query: {
              menu_id: target.menu_id || undefined,
              action_id: target.action_id || undefined,
              ...workspaceContextQuery,
            },
          });
          return;
        }
      }
      if (typeof target.menu_xmlid === 'string' && target.menu_xmlid.trim()) {
        const menuNode = findActionNodeByMenuXmlid(session.menuTree, target.menu_xmlid);
        if (menuNode?.menu_id || menuNode?.id) {
          await router.replace({
            path: `/m/${menuNode.menu_id || menuNode.id}`,
            query: workspaceContextQuery as LocationQueryRaw,
          });
          return;
        }
      }
      if (target.action_id && !session.menuTree.length) {
        await router.replace({
          path: `/a/${target.action_id}`,
          query: {
            menu_id: target.menu_id || undefined,
            scene_key: sceneKey || undefined,
            scene_label: sceneLabel || undefined,
            ...workspaceContextQuery,
          },
        });
        return;
      }
    }

    if (layout.kind === 'list' || layout.kind === 'ledger') {
      const resolvedAction = resolveVisibleActionTarget(target, sceneKey);
      if (resolvedAction) {
        const nextQuery = {
          menu_id: resolvedAction.menuId,
          action_id: resolvedAction.actionId,
          scene_key: sceneKey || undefined,
          scene_label: sceneLabel || undefined,
          ...workspaceContextQuery,
        };
        const currentActionId = Number(route.query.action_id || 0);
        const currentMenuId = Number(route.query.menu_id || 0);
        const sameEmbeddedRouteState =
          currentActionId === resolvedAction.actionId
          && currentMenuId === Number(resolvedAction.menuId || 0)
          && String(route.query.scene_key || '') === sceneKey;
        if (!sameEmbeddedRouteState) {
          await router.replace({ path: route.path, query: nextQuery as LocationQueryRaw });
          return;
        }
        embeddedActionId.value = resolvedAction.actionId;
        status.value = 'idle';
        return;
      }
      if (target.model && target.record_id) {
        const recordId = resolveRecordId(target.record_id);
        if (recordId) {
          await router.replace({
            path: `/r/${target.model}/${recordId}`,
            query: {
              menu_id: target.menu_id || undefined,
              action_id: target.action_id || undefined,
              ...workspaceContextQuery,
            },
          });
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
        await router.replace({ path: target.route, query: workspaceContextQuery as LocationQueryRaw });
        return;
      }
      setError(
        new Error(pageText('error_scene_render_target_missing', 'scene render target missing')),
        pageText('error_scene_render_target_missing', 'scene render target missing'),
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
      err instanceof Error ? err : new Error(pageText('error_scene_resolve_failed', 'scene resolve failed')),
      pageText('error_scene_resolve_failed', 'scene resolve failed'),
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

watch(
  () => route.fullPath,
  () => {
    resolveScene();
  },
  { immediate: true }
);
</script>

<style scoped>
.scene {
  padding: 12px;
}

.scene-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.scene-view-switch {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
}

.scene-view-switch__label {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.scene-view-switch__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scene-view-switch__chip {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #0f172a;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.scene-view-switch__chip.active {
  background: #0f172a;
  color: #fff;
  border-color: #0f172a;
}

.scene-view-switch__chip:disabled {
  cursor: default;
  opacity: 0.75;
}
</style>
