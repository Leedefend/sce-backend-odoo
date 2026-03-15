<template>
  <section class="scene">
    <section v-if="headerActions.length" class="scene-actions">
      <button
        v-for="action in headerActions"
        :key="`scene-header-${action.key}`"
        class="ghost"
        :disabled="status === 'loading'"
        @click="executeHeaderAction(action.key)"
      >
        {{ action.label || action.key }}
      </button>
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
    <ContractFormPage v-else-if="status === 'idle' && embeddedRecordActionId > 0" />
    <ActionView v-else-if="status === 'idle' && embeddedActionId > 0" />
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ActionView from './ActionView.vue';
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
const embeddedActionId = ref(0);
const embeddedRecordActionId = ref(0);

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
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
      layout: resolveSceneLayout(null),
      capabilities: [],
      breadcrumbs: [],
      tiles: [],
    };
  }
  return null;
}

async function resolveScene() {
  try {
    status.value = 'loading';
    clearError();
    embeddedActionId.value = 0;
    embeddedRecordActionId.value = 0;
    const sceneKey = String(route.meta?.sceneKey || route.params.sceneKey || '');
    const scene = getSceneByKey(sceneKey) || fallbackSceneFromSceneReady(sceneKey);
    if (!scene) {
      setError(new Error(`scene not found: ${sceneKey}`), 'scene not found');
      errorCopy.value = resolveErrorCopy(error.value, pageText('error_fallback', '场景加载失败'));
      status.value = 'error';
      return;
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
          await router.replace({ path: normalizedRoute, query: workspaceContextQuery });
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
            query: workspaceContextQuery,
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
          await router.replace({ path: route.path, query: nextQuery });
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
        await router.replace({ path: target.route, query: workspaceContextQuery });
        return;
      }
      // Do not early-fallback here; let explicit target/action resolution decide.
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
</style>
