<template>
  <section class="page sc-page">
    <StatusPanel
      title="记录不存在"
      message="该页面或记录不存在，可能已被删除或链接已经失效。"
      variant="error"
      :on-retry="returnSafely"
    />
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';

const router = useRouter();

function returnSafely(): void {
  if (window.history.length > 1) router.back();
  else void router.push('/');
}
</script>
