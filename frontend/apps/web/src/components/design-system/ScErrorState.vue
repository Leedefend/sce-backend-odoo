<template><section class="sc-alert sc-alert-danger" role="alert"><h2>{{ title }}</h2><p>{{ description }}</p><slot name="actions" /></section></template>
<script setup lang="ts">defineProps<{ title:string; description:string }>();</script>
<style scoped>.sc-alert{display:grid;gap:var(--sc-product-space-2)}.sc-alert h2,.sc-alert p{margin:0}.sc-alert h2{font-size:var(--sc-product-text-section)}</style>
