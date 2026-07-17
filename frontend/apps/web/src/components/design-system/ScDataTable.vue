<template><div v-bind="$attrs" class="sc-table-shell" tabindex="0" :aria-label="label"><table class="sc-product-table" :style="tableStyle"><slot /></table></div></template>
<script setup lang="ts">
import type { CSSProperties } from 'vue';

defineOptions({ inheritAttrs: false });
withDefaults(defineProps<{ label?: string; tableStyle?: CSSProperties }>(), {
  label: '数据表格，可横向滚动查看',
  tableStyle: undefined,
});
</script>
