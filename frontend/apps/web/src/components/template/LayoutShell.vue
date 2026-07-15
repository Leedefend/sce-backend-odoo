<template>
  <div :class="['template-layout-shell', { 'template-layout-shell--flow': flow }]" data-component="LayoutShell">
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  flow?: boolean;
}>(), {
  flow: false,
});
</script>

<style scoped>
.template-layout-shell {
  display: grid;
  gap: 8px;
  width: 100%;
  min-width: 0;
  padding-bottom: 24px;
}

.template-layout-shell--flow {
  max-width: min(1080px, 100%);
  margin: 0 auto;
  padding: 24px 32px;
  box-sizing: border-box;
}

@media (max-width: 860px) {
  .template-layout-shell--flow {
    padding: 14px 12px 20px;
  }
}
</style>
