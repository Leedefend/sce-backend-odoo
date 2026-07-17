<template>
  <div
    :class="['template-layout-shell', 'sc-page-frame', contentLayoutModeClass(resolvedContentLayout)]"
    data-component="LayoutShell"
    data-workspace-frame="business"
    :data-content-layout-mode="resolvedContentLayout"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  contentLayoutModeClass,
  normalizeContentLayoutMode,
  type ContentLayoutMode,
} from '../design-system/pageWidth';

const props = withDefaults(defineProps<{
  contentLayout?: ContentLayoutMode;
}>(), {
  contentLayout: 'record-grid',
});

const resolvedContentLayout = computed(() => normalizeContentLayoutMode(props.contentLayout));
</script>

<style scoped>
.template-layout-shell {
  display: grid;
  gap: 8px;
  padding-bottom: calc(var(--sc-page-padding) + var(--sc-product-space-3));
}
</style>
