<template>
  <svg
    class="sc-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path :d="pathData" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  name: 'arrow-right' | 'chevron-right' | 'close' | 'menu' | 'star' | 'star-outline';
  size?: 16 | 20 | 24;
}>(), { size: 20 });

const paths = {
  'arrow-right': 'M5 12h14m-6-6 6 6-6 6',
  'chevron-right': 'm9 18 6-6-6-6',
  close: 'M6 6l12 12M18 6 6 18',
  menu: 'M4 7h16M4 12h16M4 17h16',
  star: 'm12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-2.9-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3Z',
  'star-outline': 'm12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-2.9-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3Z',
} as const;

const pathData = computed(() => paths[props.name]);
</script>

<style scoped>
.sc-icon { display: inline-block; flex: 0 0 auto; }
</style>
