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
      session.setActionMeta(result.meta);
      await router.replace(`/a/${result.meta.action_id}?menu_id=${menuId}`);
      return;
    }
    if (result.kind === 'group') {
      const label = result.node.title || result.node.name || result.node.label || 'This menu';
      info.value = `${label} is a group. Select a submenu to continue.`;
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
