<template><div v-bind="$attrs" class="sc-table-shell" tabindex="0" :aria-label="label"><table class="sc-product-table"><slot /></table></div></template>
<script setup lang="ts">defineOptions({ inheritAttrs: false }); withDefaults(defineProps<{ label?: string }>(), { label: '数据表格，可横向滚动查看' });</script>
