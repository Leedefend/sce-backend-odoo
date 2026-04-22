<template>
  <main
    :class="[
      'template-layout-shell',
      {
        'template-layout-shell--flow': flow,
        'template-layout-shell--compact-worksurface': !flow,
      },
    ]"
    data-component="LayoutShell"
  >
    <slot />
  </main>
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
  gap: 6px;
  padding-bottom: 24px;
}

.template-layout-shell--compact-worksurface {
  gap: 4px;
  padding-bottom: 10px;
}

.template-layout-shell--flow {
  max-width: 1080px;
  margin: 0 auto;
  padding: 24px 32px;
}

.template-layout-shell--compact-worksurface.template-layout-shell--flow {
  padding: 12px 18px;
}

@media (max-width: 860px) {
  .template-layout-shell--flow {
    padding: 14px 12px 20px;
  }

  .template-layout-shell--compact-worksurface.template-layout-shell--flow {
    padding: 6px 6px 12px;
  }
}
</style>
