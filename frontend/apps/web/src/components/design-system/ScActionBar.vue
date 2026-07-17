<template><div class="sc-action-group sc-design-action-bar" role="group" :aria-label="label"><slot /></div></template>
<script setup lang="ts">withDefaults(defineProps<{label?:string}>(),{label:'页面操作'});</script>
