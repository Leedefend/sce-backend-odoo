<template>
  <div
    :class="['template-layout-shell', 'sc-page-frame', pageWidthModeClass(resolvedWidthMode)]"
    data-component="LayoutShell"
    :data-page-width-mode="resolvedWidthMode"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  normalizePageWidthMode,
  pageWidthModeClass,
  type PageWidthMode,
} from '../design-system/pageWidth';

const props = withDefaults(defineProps<{
  widthMode?: PageWidthMode;
}>(), {
  widthMode: 'standard',
});

const resolvedWidthMode = computed(() => normalizePageWidthMode(props.widthMode));
</script>

<style scoped>
.template-layout-shell {
  display: grid;
  gap: 8px;
  padding-bottom: calc(var(--sc-page-padding) + var(--sc-product-space-3));
}
</style>
