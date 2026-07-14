<template>
  <section class="page sc-page">
    <StatusPanel
      :title="pageText('title', '无权访问')"
      :message="pageText('message', '当前角色无权访问此业务入口。请返回已授权的工作区。')"
      variant="error"
      :on-retry="returnSafely"
    />
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { usePageContract } from '../app/pageContract';

const router = useRouter();
const pageContract = usePageContract('access-denied');
const pageText = pageContract.text;

function returnSafely(): void {
  if (window.history.length > 1) router.back();
  else void router.push('/');
}
</script>
