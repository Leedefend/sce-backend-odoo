<template><section class="sc-empty"><h2>{{ title }}</h2><p v-if="description">{{ description }}</p><div v-if="$slots.actions" class="sc-action-group"><slot name="actions" /></div></section></template>
<script setup lang="ts">defineProps<{ title:string; description?:string }>();</script>
<style scoped>.sc-empty h2,.sc-empty p{margin:0}.sc-empty h2{font-size:var(--sc-product-text-section)}.sc-empty .sc-action-group{justify-content:center}</style>
