<template>
  <section class="menu-view">
    <StatusPanel v-if="loading" title="Resolving menu..." variant="info" />
    <StatusPanel
      v-else-if="info"
      title="Menu group"
      :message="info"
      variant="info"
    />
    <StatusPanel
      v-else-if="error"
      title="Menu resolve failed"
      :message="error"
      variant="error"
    />
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { resolveMenuAction } from '../app/resolvers/menuResolver';
import StatusPanel from '../components/StatusPanel.vue';
import { ErrorCodes } from '../app/error_codes';
import { evaluateCapabilityPolicy } from '../app/capabilityPolicy';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const error = ref('');
const info = ref('');
const loading = ref(true);

async function resolve() {
  loading.value = true;
  error.value = '';
  info.value = '';
  try {
    const menuId = Number(route.params.menuId);
    if (!menuId) {
      throw new Error('invalid menu id');
    }
    const result = resolveMenuAction(session.menuTree, menuId);
    if (result.kind === 'leaf') {
      const policy = evaluateCapabilityPolicy({ source: result.node?.meta, available: session.capabilities });
      if (policy.state !== 'enabled') {
        await router.replace({
          name: 'workbench',
          query: {
            menu_id: menuId,
            action_id: result.meta.action_id,
            reason: ErrorCodes.CAPABILITY_MISSING,
            missing: policy.missing.join(','),
          },
        });
        return;
      }
      session.setActionMeta(result.meta);
      await router.replace(`/a/${result.meta.action_id}?menu_id=${menuId}`);
      return;
    }
    if (result.kind === 'group' || result.reason === 'menu has no action') {
      const label = result.node?.title || result.node?.name || result.node?.label || 'This menu';
      await router.replace({
        name: 'workbench',
        query: { menu_id: menuId, reason: ErrorCodes.NAV_MENU_NO_ACTION, label },
      });
      return;
    }
    error.value = result.reason || 'resolve menu failed';
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'resolve menu failed';
  } finally {
    loading.value = false;
  }
}

watch(
  () => route.params.menuId,
  () => {
    resolve();
  },
  { immediate: true }
);
</script>
<style scoped>
.menu-view {
  padding: 12px;
}
</style>
