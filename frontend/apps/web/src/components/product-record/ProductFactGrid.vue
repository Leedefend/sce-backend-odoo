<template>
  <section v-if="facts.length" class="product-facts" :data-fact-group="group" :aria-labelledby="titleId">
    <header>
      <p>{{ eyebrow }}</p>
      <h2 :id="titleId">{{ title }}</h2>
    </header>
    <dl>
      <div v-for="fact in facts" :key="fact.key" :data-fact-key="fact.key" :data-product-money-fact="fact.kind === 'money' || undefined">
        <dt>{{ fact.label }}</dt>
        <dd :class="{ 'product-facts__money': fact.kind === 'money' }">{{ formatFact(fact) }}</dd>
      </div>
    </dl>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatWorkspaceMoney, type WorkspaceFact } from '../../app/financialWorkspaceContract';

const props = defineProps<{ facts: WorkspaceFact[]; group: 'business' | 'money'; eyebrow: string; title: string }>();
const titleId = computed(() => `product-${props.group}-facts-title`);

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '未提供';
  return String(value);
}

function formatDateTime(value: unknown): string {
  const text = String(value || '').trim();
  if (!text) return '未提供';
  const date = new Date(text);
  return Number.isNaN(date.valueOf()) ? text : new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function formatFact(fact: WorkspaceFact): string {
  if (fact.kind === 'money') return formatWorkspaceMoney(fact.value, fact.currency);
  if (fact.kind === 'datetime') return formatDateTime(fact.value);
  return displayValue(fact.value);
}
</script>

<style scoped>
.product-facts { min-width: 0; padding: var(--sc-product-space-3); border: 1px solid var(--sc-app-border); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-panel); }
.product-facts header { margin-bottom: var(--sc-product-space-2); }
.product-facts header p { margin: 0 0 var(--sc-product-space-1); color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.product-facts h2 { margin: 0; font-size: 18px; }
.product-facts dl { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: var(--sc-product-space-2); margin: 0; }
.product-facts dl > div { min-width: 0; padding: var(--sc-product-space-2); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-subtle-bg); }
.product-facts dt { color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.product-facts dd { margin: var(--sc-product-space-1) 0 0; overflow-wrap: anywhere; }
.product-facts__money { font-size: 18px; font-variant-numeric: tabular-nums; font-weight: 700; text-align: right; }
@media (max-width: 600px) { .product-facts { padding: var(--sc-product-space-2); } .product-facts dl { grid-template-columns: minmax(0, 1fr); } }
</style>
