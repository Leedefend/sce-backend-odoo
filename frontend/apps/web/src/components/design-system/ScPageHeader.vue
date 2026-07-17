<template>
  <header class="sc-design-page-header" data-workspace-page-header>
    <div><p v-if="eyebrow" class="sc-muted">{{ eyebrow }}</p><h1>{{ title }}</h1><p v-if="subtitle" class="sc-muted">{{ subtitle }}</p></div>
    <div v-if="$slots.actions" class="sc-action-group"><slot name="actions" /></div>
  </header>
</template>
<script setup lang="ts">defineProps<{ title: string; subtitle?: string; eyebrow?: string }>();</script>
<style scoped>.sc-design-page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:var(--sc-product-space-3)}.sc-design-page-header h1,.sc-design-page-header p{margin:0}.sc-design-page-header h1{font-size:var(--sc-product-text-title);line-height:1.25}.sc-design-page-header p+ h1,.sc-design-page-header h1+ p{margin-top:var(--sc-product-space-1)}@media(max-width:640px){.sc-design-page-header{flex-direction:column}}</style>
