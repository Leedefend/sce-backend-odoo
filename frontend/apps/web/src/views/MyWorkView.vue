<template>
  <section class="my-work-page" data-my-work-renderer="product-workspace">
    <StatusPanel v-if="loading" title="正在加载工作事项" message="正在读取当前账号可处理的业务事项。" variant="info" busy />
    <StatusPanel
      v-else-if="errorMessage"
      title="工作事项加载失败"
      :message="errorMessage"
      variant="error"
      :on-retry="load"
    />
    <MyWorkApprovalWorkspace
      v-else-if="workspace"
      :workspace="workspace"
      @refresh="load"
    />
    <StatusPanel
      v-else
      title="当前没有工作事项"
      message="当前账号与业务范围内没有需要处理的事项。"
      variant="info"
      :on-retry="load"
      retry-label="刷新"
    />
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { fetchMyWorkSummary, type ProductMyWorkWorkspace } from '../api/myWork';
import { currentContextEpoch, isCurrentContextEpoch } from '../app/contextEpoch';
import MyWorkApprovalWorkspace from '../components/business/MyWorkApprovalWorkspace.vue';
import StatusPanel from '../components/StatusPanel.vue';
import { useSessionStore } from '../stores/session';

const session = useSessionStore();
const workspace = ref<ProductMyWorkWorkspace | null>(null);
const loading = ref(false);
const errorMessage = ref('');
let requestSequence = 0;

async function load() {
  const sequence = ++requestSequence;
  const epoch = currentContextEpoch();
  if (!session.token) {
    workspace.value = null;
    loading.value = false;
    errorMessage.value = '';
    return;
  }
  loading.value = true;
  errorMessage.value = '';
  workspace.value = null;
  try {
    const result = await fetchMyWorkSummary(80, 80, {
      page: 1,
      pageSize: 80,
      sortBy: 'write_date',
      sortDir: 'desc',
    });
    if (sequence !== requestSequence || !isCurrentContextEpoch(epoch) || !session.token) return;
    workspace.value = result.product_workspace || null;
  } catch {
    if (sequence !== requestSequence || !isCurrentContextEpoch(epoch) || !session.token) return;
    errorMessage.value = '当前无法读取工作事项，请检查网络后重试。';
  } finally {
    if (sequence === requestSequence && isCurrentContextEpoch(epoch)) loading.value = false;
  }
}

watch(
  [
    () => session.token,
    () => session.projectContext?.company_id,
    () => session.projectContext?.selected?.id,
    () => session.roleSurface?.role_code,
  ],
  () => { void load(); },
  { immediate: true },
);
</script>

<style scoped>
.my-work-page {
  display: grid;
  gap: var(--sc-product-space-3);
}
</style>
