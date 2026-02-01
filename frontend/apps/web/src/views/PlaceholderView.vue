<template>
  <main class="page">
    <section class="card">
      <h1>Dynamic View Placeholder</h1>
      <p>Route: {{ route.path }}</p>
      <p>Params: {{ route.params }}</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();
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
