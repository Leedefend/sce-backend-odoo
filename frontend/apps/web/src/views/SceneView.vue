<template>
  <section class="scene">
    <StatusPanel v-if="status === 'loading'" title="Resolving scene..." variant="info" />
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

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const status = ref<'loading' | 'error' | 'idle'>('loading');
const { error, clearError, setError } = useStatus();
const errorCopy = ref(resolveErrorCopy(null, 'Scene resolve failed'));
const CORE_SCENE_FALLBACK = new Set(['projects.list', 'projects.ledger', 'projects.intake']);

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
    errorCopy.value = resolveErrorCopy(error.value, 'Scene resolve failed');
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
  if (layout.kind === 'workspace') {
    if (CORE_SCENE_FALLBACK.has(sceneKey)) {
      await router.replace('/s/projects.list');
      return;
    }
    await router.replace({ name: 'workbench', query: { scene: sceneKey || undefined } });
    return;
  }

  if (layout.kind === 'record') {
    if (target.model) {
      const node = findActionNodeByModel(session.menuTree, target.model);
      const menuId = node?.menu_id ?? node?.id;
      const actionId = node?.meta?.action_id;
      const recordId = resolveRecordId(target.record_id ?? route.params.id);
      if (recordId) {
        await router.replace({
          path: `/r/${target.model}/${recordId}`,
          query: { menu_id: menuId || undefined, action_id: actionId || undefined },
        });
        return;
      }
      if (actionId) {
        await router.replace({
          path: `/a/${actionId}`,
          query: { menu_id: menuId || undefined },
        });
        return;
      }
    }
    if (target.action_id) {
      await router.replace({
        path: `/a/${target.action_id}`,
        query: { menu_id: target.menu_id || undefined },
      });
      return;
    }
  }

  if (layout.kind === 'list' || layout.kind === 'ledger') {
    if (target.action_id) {
      await router.replace({
        path: `/a/${target.action_id}`,
        query: { menu_id: target.menu_id || undefined },
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
          query: { menu_id: menuId || undefined },
        });
        return;
      }
      if (target.record_id) {
        const recordId = resolveRecordId(target.record_id);
        if (recordId) {
          await router.replace({
            path: `/r/${target.model}/${recordId}`,
            query: { menu_id: menuId || undefined, action_id: actionId || undefined },
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
    await router.replace(target.route);
    return;
  }

  const menuHint = Number(route.query.menu_id || 0) || undefined;
  if (menuHint) {
    await router.replace({ path: `/m/${menuHint}` });
    return;
  }
  const sceneNode = findActionNodeBySceneKey(session.menuTree, sceneKey);
  if (sceneNode?.meta?.action_id) {
    await router.replace({
      path: `/a/${sceneNode.meta.action_id}`,
      query: { menu_id: sceneNode.menu_id || sceneNode.id || undefined },
    });
    return;
  }
  if (sceneNode?.menu_id || sceneNode?.id) {
    await router.replace({ path: `/m/${sceneNode.menu_id || sceneNode.id}` });
    return;
  }
  if (CORE_SCENE_FALLBACK.has(sceneKey)) {
    await router.replace('/s/projects.list');
    return;
  }

  setError(new Error('scene target unsupported'), 'scene target unsupported', ErrorCodes.SCENE_KIND_UNSUPPORTED);
  errorCopy.value = resolveErrorCopy(error.value, 'Scene resolve failed');
  status.value = 'error';
}

function findActionNodeBySceneKey(nodes: Array<Record<string, any>>, sceneKey: string) {
  if (!sceneKey) return null;
  const walk = (items: Array<Record<string, any>>): Record<string, any> | null => {
    for (const node of items) {
      if (node?.scene_key === sceneKey || node?.meta?.scene_key === sceneKey) {
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
