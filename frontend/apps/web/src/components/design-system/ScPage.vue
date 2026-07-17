<template>
  <section
    :class="['sc-page', 'sc-page-frame', pageWidthModeClass(resolvedWidthMode)]"
    :data-page-width-mode="resolvedWidthMode"
  >
    <slot />
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  normalizePageWidthMode,
  pageWidthModeClass,
  type PageWidthMode,
} from './pageWidth';

const props = withDefaults(defineProps<{
  widthMode?: PageWidthMode;
}>(), {
  widthMode: 'standard',
});

const resolvedWidthMode = computed(() => normalizePageWidthMode(props.widthMode));
</script>
