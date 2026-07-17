<template><span class="sc-design-money"><span v-if="label" class="sc-visually-hidden">{{ label }}：</span>{{ display }}</span></template>
<script setup lang="ts">defineProps<{ display: string; label?: string }>();</script>
<style scoped>.sc-design-money{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}</style>
