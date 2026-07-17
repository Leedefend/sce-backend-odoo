<template><button type="button" class="sc-btn sc-btn-ghost sc-icon-button" :aria-label="label" :title="label" :disabled="disabled"><span aria-hidden="true"><slot /></span></button></template>
<script setup lang="ts">defineProps<{ label: string; disabled?: boolean }>();</script>
<style scoped>.sc-icon-button{inline-size:var(--sc-product-control-height);padding:0;display:inline-grid;place-items:center}</style>
