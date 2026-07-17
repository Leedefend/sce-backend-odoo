<template><section class="sc-design-audit-trail" :aria-label="label"><dl><slot /></dl></section></template>
<script setup lang="ts">withDefaults(defineProps<{label?:string}>(),{label:'审计信息'});</script>
<style scoped>.sc-design-audit-trail dl{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--sc-product-space-2);margin:0;color:var(--sc-app-text-secondary)}@media(max-width:600px){.sc-design-audit-trail dl{grid-template-columns:1fr}}</style>
