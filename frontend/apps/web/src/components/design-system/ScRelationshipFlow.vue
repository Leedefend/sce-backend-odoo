<template><ol class="sc-design-relationship-flow" :aria-label="label"><slot /></ol></template>
<script setup lang="ts">withDefaults(defineProps<{label?:string}>(),{label:'关联记录'});</script>
<style scoped>.sc-design-relationship-flow{display:flex;gap:var(--sc-product-space-2);margin:0;padding:0;list-style:none;overflow-x:auto}@media(max-width:600px){.sc-design-relationship-flow{flex-direction:column;overflow:visible}}</style>
