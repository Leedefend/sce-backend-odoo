<template><component :is="as" :class="['sc-panel', `sc-design-panel--${tone}`]"><slot /></component></template>
<script setup lang="ts">withDefaults(defineProps<{ as?: string; tone?: 'default'|'subtle'|'raised' }>(), { as: 'section', tone: 'default' });</script>
<style scoped>.sc-panel{padding:calc(var(--sc-component-panel-padding) * 1px)}.sc-design-panel--subtle{background:var(--sc-app-subtle-bg);box-shadow:none}.sc-design-panel--raised{box-shadow:var(--sc-app-shadow-popover)}</style>
