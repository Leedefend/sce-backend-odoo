<template>
  <section class="page sc-page">
    <StatusPanel
      :title="pageIdentity.title.value"
      hide-title
      :message="pageText('message', '该页面或记录不存在，可能已被删除或链接已经失效。')"
      variant="error"
      :on-retry="returnSafely"
    />
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { usePageContract } from '../app/pageContract';
import { usePageIdentityRuntime } from '../app/pageIdentityRuntime';

const router = useRouter();
const pageIdentity = usePageIdentityRuntime();
const pageText = usePageContract('not-found').text;

function returnSafely(): void {
  if (window.history.length > 1) router.back();
  else void router.push('/');
}
</script>
