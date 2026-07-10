<template>
  <header class="header sc-product-page-header">
    <div>
      <h2 class="title">{{ title }}</h2>
      <p class="subtitle">{{ subtitle }}</p>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  subtitle: string;
}>();
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--sc-app-panel);
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: var(--sc-app-shadow);
}

.title {
  margin: 0;
  font-size: 20px;
}

.subtitle {
  margin: 6px 0 0;
  color: var(--sc-semantic-text-muted);
  font-size: 13px;
}
</style>
