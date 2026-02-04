<template>
  <section class="scene">
    <StatusPanel v-if="status === 'loading'" title="Resolving scene..." variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      title="Scene resolve failed"
      :message="error?.message"
      :trace-id="error?.traceId"
      :error-code="error?.code"
      :hint="error?.hint"
      variant="error"
    />
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { getSceneByKey } from '../app/resolvers/sceneRegistry';
import { useSessionStore } from '../stores/session';
import { findActionNodeByModel } from '../app/menu';
import { evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { ErrorCodes } from '../app/error_codes';
import { useStatus } from '../composables/useStatus';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const status = ref<'loading' | 'error' | 'idle'>('loading');
const { error, clearError, setError } = useStatus();

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

  const target = scene.target || {};
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

  setError(new Error('scene target unsupported'), 'scene target unsupported');
  status.value = 'error';
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
