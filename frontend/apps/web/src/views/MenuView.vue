<template>
  <section class="menu-view">
    <StatusPanel v-if="loading" title="Resolving menu..." variant="info" />
    <StatusPanel
      v-else-if="error"
      title="Menu resolve failed"
      :message="error"
      variant="error"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { resolveMenuAction } from '../app/resolvers/menuResolver';
import StatusPanel from '../components/StatusPanel.vue';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const error = ref('');
const loading = ref(true);

onMounted(async () => {
  try {
    const menuId = Number(route.params.menuId);
    if (!menuId) {
      throw new Error('invalid menu id');
    }
    const meta = resolveMenuAction(session.menuTree, menuId);
    session.setActionMeta(meta);
    await router.replace(`/a/${meta.action_id}?menu_id=${menuId}`);
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'resolve menu failed';
  } finally {
    loading.value = false;
  }
});
</script>
<style scoped>
.menu-view {
  padding: 12px;
}
</style>
