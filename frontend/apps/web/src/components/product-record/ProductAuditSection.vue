<template>
  <details v-if="facts.length" class="product-audit">
    <summary>{{ title }}</summary>
    <p>{{ eyebrow }}</p>
    <dl><div v-for="fact in facts" :key="fact.key"><dt>{{ fact.label }}</dt><dd>{{ factText(fact) }}</dd></div></dl>
  </details>
</template>

<script setup lang="ts">
import { formatWorkspaceMoney, type WorkspaceFact } from '../../app/financialWorkspaceContract';
defineProps<{ facts: WorkspaceFact[]; eyebrow: string; title: string }>();
function factText(fact: WorkspaceFact): string {
  if (fact.kind === 'money') return formatWorkspaceMoney(fact.value, fact.currency);
  if (fact.value === null || fact.value === undefined || fact.value === '') return '未提供';
  if (fact.kind === 'datetime') {
    const date = new Date(String(fact.value));
    if (!Number.isNaN(date.valueOf())) return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
  }
  return String(fact.value);
}
</script>

<style scoped>
.product-audit { padding: var(--sc-product-space-2) var(--sc-product-space-3); border: 1px solid var(--sc-app-border); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-panel); }
.product-audit summary { cursor: pointer; font-weight: 600; }
.product-audit > p { margin: var(--sc-product-space-2) 0; color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.product-audit dl { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: var(--sc-product-space-2); margin: 0; }
.product-audit dt { color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.product-audit dd { margin: 3px 0 0; overflow-wrap: anywhere; }
@media (max-width: 600px) { .product-audit { padding: var(--sc-product-space-2); } .product-audit dl { grid-template-columns: minmax(0, 1fr); } }
</style>
