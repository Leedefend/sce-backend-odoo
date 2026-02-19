<template>
  <main class="page">
    <StatusPanel
      title="Legacy List Route"
      message="This route has been redirected to contract-driven ActionView."
      variant="info"
    />
  </main>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { ErrorCodes } from '../app/error_codes';

const route = useRoute();
const router = useRouter();

onMounted(() => {
  const actionId = Number(route.query.action_id || 0);
  if (Number.isFinite(actionId) && actionId > 0) {
    const query = route.query as Record<string, unknown>;
    router.replace({ name: 'action', params: { actionId }, query }).catch(() => {});
    return;
  }
  router
    .replace({
      name: 'workbench',
      query: { reason: ErrorCodes.ACT_UNSUPPORTED_TYPE, diag: 'legacy_route_missing_action_id' },
    })
    .catch(() => {});
});
</script>

<style scoped>
.page {
  padding: 12px;
}
</style>
