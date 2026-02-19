<template>
  <section class="scene">
    <StatusPanel v-if="status === 'loading'" title="正在加载场景..." variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="error?.traceId"
      :error-code="error?.code"
      :reason-code="error?.reasonCode"
      :error-category="error?.errorCategory"
      :retryable="error?.retryable"
      :hint="errorCopy.hint"
      :suggested-action="error?.suggestedAction"
      variant="error"
    />
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { getSceneByKey, resolveSceneLayout } from '../app/resolvers/sceneRegistry';
import { useSessionStore } from '../stores/session';
import { config } from '../config';
import { findActionNodeByModel } from '../app/menu';
import { evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { ErrorCodes } from '../app/error_codes';
import { resolveErrorCopy, useStatus } from '../composables/useStatus';
import { trackSceneOpen } from '../api/usage';
import { readWorkspaceContext } from '../app/workspaceContext';
import { normalizeLegacyWorkbenchPath } from '../app/routeQuery';
import type { NavNode } from '@sc/schema';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const status = ref<'loading' | 'error' | 'idle'>('loading');
const { error, clearError, setError } = useStatus();
const errorCopy = ref(resolveErrorCopy(null, '场景加载失败'));

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
}

function isPortalPath(url: string) {
  return url.startsWith('/portal/');
}

function resolvePortalBridgeBase() {
  try {
    const base = new URL(config.apiBaseUrl);
    if (base.hostname === 'localhost') {
      base.hostname = '127.0.0.1';
    }
    return base.toString();
  } catch {
    return config.apiBaseUrl;
  }
}

function buildPortalBridgeUrl(url: string) {
  const nextPath = url.startsWith('/') ? url : `/${url}`;
  const bridge = new URL('/portal/bridge', resolvePortalBridgeBase());
  bridge.searchParams.set('next', nextPath);
  if (session.token) {
    bridge.searchParams.set('token', session.token);
  }
  if (config.odooDb) {
    bridge.searchParams.set('db', config.odooDb);
  }
  return bridge.toString();
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

async function resolveScene() {
  status.value = 'loading';
  clearError();
  const sceneKey = String(route.meta?.sceneKey || route.params.sceneKey || '');
  const scene = getSceneByKey(sceneKey);
  if (!scene) {
    setError(new Error(`scene not found: ${sceneKey}`), 'scene not found');
    errorCopy.value = resolveErrorCopy(error.value, '场景加载失败');
    status.value = 'error';
    return;
  }

  const policy = evaluateCapabilityPolicy({ required: scene.capabilities || [], available: session.capabilities });
  if (policy.state !== 'enabled') {
    await router.replace({
      name: 'workbench',
      query: { reason: ErrorCodes.CAPABILITY_MISSING },
    });
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
        window.location.assign(buildPortalBridgeUrl(normalizedRoute));
        return;
      }
      if (normalizedRoute !== route.fullPath) {
        await router.replace({ path: normalizedRoute, query: workspaceContextQuery });
        return;
      }
    }
  }

  if (layout.kind === 'record') {
    if (typeof target.menu_xmlid === 'string' && target.menu_xmlid.trim()) {
      const menuNode = findActionNodeByMenuXmlid(session.menuTree, target.menu_xmlid);
      if (menuNode?.meta?.action_id) {
        await router.replace({
          path: `/a/${menuNode.meta.action_id}`,
          query: { menu_id: menuNode.menu_id || menuNode.id || undefined, ...workspaceContextQuery },
        });
        return;
      }
      if (menuNode?.menu_id || menuNode?.id) {
        await router.replace({
          path: `/m/${menuNode.menu_id || menuNode.id}`,
          query: workspaceContextQuery,
        });
        return;
      }
    }
    if (target.model) {
      const node = findActionNodeByModel(session.menuTree, target.model);
      const menuId = node?.menu_id ?? node?.id;
      const actionId = node?.meta?.action_id;
      const recordId = resolveRecordId(target.record_id ?? route.params.id);
      if (recordId) {
        await router.replace({
          path: `/r/${target.model}/${recordId}`,
          query: { menu_id: menuId || undefined, action_id: actionId || undefined, ...workspaceContextQuery },
        });
        return;
      }
      if (actionId) {
        await router.replace({
          path: `/a/${actionId}`,
          query: { menu_id: menuId || undefined, ...workspaceContextQuery },
        });
        return;
      }
    }
    if (target.action_id) {
      await router.replace({
        path: `/a/${target.action_id}`,
        query: { menu_id: target.menu_id || undefined, ...workspaceContextQuery },
      });
      return;
    }
  }

  if (layout.kind === 'list' || layout.kind === 'ledger') {
    if (target.action_id) {
      await router.replace({
        path: `/a/${target.action_id}`,
        query: { menu_id: target.menu_id || undefined, ...workspaceContextQuery },
      });
      return;
    }
    if (target.model) {
      const node = findActionNodeByModel(session.menuTree, target.model);
      const menuId = node?.menu_id ?? node?.id;
      const actionId = node?.meta?.action_id;
      if (actionId) {
        await router.replace({
          path: `/a/${actionId}`,
          query: { menu_id: menuId || undefined, ...workspaceContextQuery },
        });
        return;
      }
      if (target.record_id) {
        const recordId = resolveRecordId(target.record_id);
        if (recordId) {
          await router.replace({
            path: `/r/${target.model}/${recordId}`,
            query: { menu_id: menuId || undefined, action_id: actionId || undefined, ...workspaceContextQuery },
          });
          return;
        }
      }
    }
  }

  if (target.route) {
    if (isPortalPath(target.route)) {
      window.location.assign(buildPortalBridgeUrl(target.route));
      return;
    }
    await router.replace({ path: target.route, query: workspaceContextQuery });
    return;
  }

  const sceneNode = findActionNodeBySceneKey(session.menuTree, sceneKey);
  if (sceneNode?.meta?.action_id) {
    await router.replace({
      path: `/a/${sceneNode.meta.action_id}`,
      query: { menu_id: sceneNode.menu_id || sceneNode.id || undefined, ...workspaceContextQuery },
    });
    return;
  }
  if (sceneNode?.menu_id || sceneNode?.id) {
    await router.replace({ path: `/m/${sceneNode.menu_id || sceneNode.id}`, query: workspaceContextQuery });
    return;
  }
  setError(new Error('scene target unsupported'), 'scene target unsupported', ErrorCodes.SCENE_KIND_UNSUPPORTED);
  errorCopy.value = resolveErrorCopy(error.value, '场景加载失败');
  status.value = 'error';
}

function findActionNodeBySceneKey(nodes: NavNode[], sceneKey: string): NavNode | null {
  if (!sceneKey) return null;
  const walk = (items: NavNode[]): NavNode | null => {
    for (const node of items) {
      const sceneNode = node as NavNode & { scene_key?: string };
      if (sceneNode.scene_key === sceneKey || node.meta?.scene_key === sceneKey) {
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
