<template>
  <section class="scene">
    <StatusPanel v-if="status === 'loading'" :title="pageText('loading_title', '正在加载场景...')" variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
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
    />
    <StatusPanel
      v-else-if="status === 'forbidden'"
      :title="forbiddenCopy.title"
      :message="forbiddenCopy.message"
      :hint="forbiddenCopy.hint"
      variant="forbidden_capability"
      :on-retry="() => goWorkbench(ErrorCodes.CAPABILITY_MISSING)"
    />
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
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
import type { NavNode } from '@sc/schema';
import type { SceneTarget } from '../app/resolvers/sceneRegistry';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const pageContract = usePageContract('scene');
const pageText = pageContract.text;
const findActionNodeByModelRef = findActionNodeByModel;
const status = ref<'loading' | 'error' | 'forbidden' | 'idle'>('loading');
const { error, clearError, setError } = useStatus();
const errorCopy = ref(resolveErrorCopy(null, pageText('error_fallback', '场景加载失败')));
const forbiddenCopy = ref({
  title: pageText('forbidden_title', '能力未开通'),
  message: pageText('forbidden_message', '当前角色无法进入该场景。'),
  hint: '',
});

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
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

function isScenePlaceholderRoute() {
  const name = String(route.name || '').toLowerCase();
  return name === 'scene' || String(route.path || '').startsWith('/scene/');
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
  const actionId = Number(target.action_id || 0);
  if (actionId > 0) {
    if (!session.menuTree.length || findActionMeta(session.menuTree, actionId)) {
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

  const normalizedSceneKey = String(sceneKey || '').trim();
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
    const sceneKey = String(route.meta?.sceneKey || route.params.sceneKey || '');
    const scene = getSceneByKey(sceneKey);
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
          return `${meta.label || key}（${reason}）`;
        })
        .slice(0, 4);
      const level = String(session.productFacts.license?.level || '').trim();
      forbiddenCopy.value = {
        title:
          policy.state === 'disabled_permission'
            ? pageText('forbidden_title_permission', '权限不足')
            : pageText('forbidden_title', '能力未开通'),
        message: details.length
          ? `缺少能力：${details.join('、')}`
          : pageText('forbidden_message_scope_missing', '当前角色能力范围不包含该场景所需能力。'),
        hint: level && level !== 'enterprise' ? `当前 License：${level}，可联系管理员评估升级或开通。` : '可联系管理员开通对应能力。',
      };
      status.value = 'forbidden';
      return;
    }
    void trackSceneOpen(sceneKey).catch(() => {});

    const target = scene.target || {};
    const layout = resolveSceneLayout(scene);
    const workspaceContextQuery = resolveWorkspaceContextQuery();
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
        if (isScenePlaceholderRoute()) {
          goWorkbench();
          return;
        }
      }
      // Workspace scene may still provide action/menu/model targets.
      const resolvedAction = resolveVisibleActionTarget(target, sceneKey);
      if (resolvedAction) {
        await router.replace({
          path: `/a/${resolvedAction.actionId}`,
          query: { menu_id: resolvedAction.menuId, ...workspaceContextQuery },
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
        await router.replace({
          path: `/a/${resolvedAction.actionId}`,
          query: { menu_id: resolvedAction.menuId, ...workspaceContextQuery },
        });
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
          query: { menu_id: target.menu_id || undefined, ...workspaceContextQuery },
        });
        return;
      }
    }

    if (layout.kind === 'list' || layout.kind === 'ledger') {
      const resolvedAction = resolveVisibleActionTarget(target, sceneKey);
      if (resolvedAction) {
        await router.replace({
          path: `/a/${resolvedAction.actionId}`,
          query: { menu_id: resolvedAction.menuId, ...workspaceContextQuery },
        });
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
      if (isScenePlaceholderRoute()) {
        goWorkbench();
        return;
      }
    }

    setError(
      new Error(pageText('error_scene_target_unsupported', 'scene target unsupported')),
      pageText('error_scene_target_unsupported', 'scene target unsupported'),
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
</style>
