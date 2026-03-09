<template>
  <main class="page">
    <section v-if="pageSectionEnabled('card', true)" class="card" :style="pageSectionStyle('card')">
      <h1>{{ pageText('title', 'Dynamic View Placeholder') }}</h1>
      <p>{{ pageText('route_label', 'Route') }}: {{ route.path }}</p>
      <p>{{ pageText('params_label', 'Params') }}: {{ route.params }}</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';
import { usePageContract } from '../app/pageContract';

const route = useRoute();
const pageContract = usePageContract('placeholder');
const pageText = pageContract.text;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
</script>

<style scoped>
.page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #f8fafc;
  font-family: "IBM Plex Sans", system-ui, sans-serif;
}

.card {
  width: min(520px, 92vw);
  background: white;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
}
</style>
