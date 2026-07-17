<template>
  <ScPage class="page">
    <ScPageHeader :title="pageIdentity.title.value" />
    <ScErrorState
      :title="pageIdentity.title.value"
      :description="pageText('message', '当前角色无权访问此业务入口。请返回已授权的工作区。')"
    >
      <template #actions><ScButton @click="returnSafely">返回安全页面</ScButton></template>
    </ScErrorState>
  </ScPage>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import ScButton from '../components/design-system/ScButton.vue';
import ScErrorState from '../components/design-system/ScErrorState.vue';
import ScPage from '../components/design-system/ScPage.vue';
import ScPageHeader from '../components/design-system/ScPageHeader.vue';
import { usePageContract } from '../app/pageContract';
import { usePageIdentityRuntime } from '../app/pageIdentityRuntime';

const router = useRouter();
const pageIdentity = usePageIdentityRuntime();
const pageContract = usePageContract('access-denied');
const pageText = pageContract.text;

function returnSafely(): void {
  void router.push('/');
}
</script>
