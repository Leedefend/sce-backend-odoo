<template>
  <main class="page sc-page sc-product-workspace-stack" data-product-page-mode="list">
    <StatusPanel
      title="列表入口已升级"
      message="正在切换到新的列表页面。"
      variant="info"
    />
  </main>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { ErrorCodes } from '../app/error_codes';

const route = useRoute();
const router = useRouter();

onMounted(() => {
  const actionId = Number(route.query.action_id || 0);
  if (Number.isFinite(actionId) && actionId > 0) {
    const query = route.query as LocationQueryRaw;
    router.replace({ name: 'action', params: { actionId }, query }).catch(() => {});
    return;
  }
  router
    .replace({
      name: 'workbench',
      query: { reason: ErrorCodes.CONTRACT_CONTEXT_MISSING, diag: 'legacy_route_missing_action_id' },
    })
    .catch(() => {});
});
</script>

<style scoped>
.page {
  padding: 12px;
}
</style>
