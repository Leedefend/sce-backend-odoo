<template>
  <RouterView v-slot="{ Component, route }">
    <AppShell v-if="route.meta?.layout === 'shell'">
      <component :is="Component" />
    </AppShell>
    <component v-else :is="Component" />
  </RouterView>
</template>

<script setup lang="ts">
import AppShell from './layouts/AppShell.vue';
</script>
