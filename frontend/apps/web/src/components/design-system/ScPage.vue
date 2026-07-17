<template>
  <section
    :class="['sc-page', 'sc-page-frame', contentLayoutModeClass(resolvedContentLayout)]"
    data-workspace-frame="business"
    :data-content-layout-mode="resolvedContentLayout"
  >
    <slot />
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  contentLayoutModeClass,
  normalizeContentLayoutMode,
  type ContentLayoutMode,
} from './pageWidth';

const props = withDefaults(defineProps<{
  contentLayout?: ContentLayoutMode;
}>(), {
  contentLayout: 'record-grid',
});

const resolvedContentLayout = computed(() => normalizeContentLayoutMode(props.contentLayout));
</script>
