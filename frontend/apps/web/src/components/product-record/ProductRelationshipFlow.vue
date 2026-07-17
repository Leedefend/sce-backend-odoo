<template>
  <ScSection class="product-relations" :label="title">
    <header>
      <p>{{ eyebrow }}</p>
      <h2 id="product-relations-title">{{ title }}</h2>
    </header>
    <ScRelationshipFlow class="product-relations__flow" :label="title">
      <li v-for="relation in relationships" :key="relation.key">
      <ScPanel as="section" tone="subtle" :data-relation-key="relation.key" data-product-relationship>
        <div class="product-relations__heading"><h3>{{ relation.label }}</h3><span>{{ relation.records.length }} 条</span></div>
        <p v-if="!relation.records.length" class="product-relations__empty">{{ relation.empty_text }}</p>
        <ul v-else>
          <li v-for="item in relation.records" :key="`${item.model}-${item.id}`">
            <button v-if="item.route" type="button" @click="$emit('open', item)">
              <span><small>{{ item.object_label || relation.label }}</small><strong>{{ item.label }}</strong></span>
              <span class="product-relations__meta"><span v-if="item.status?.label">{{ item.status.label }}</span><ScIcon name="arrow-right" :size="16" /></span>
            </button>
            <div v-else class="product-relations__result">
              <small>{{ item.object_label || relation.label }}</small><strong>{{ item.label }}</strong>
              <span v-if="item.amount !== null && item.amount !== undefined">{{ formatWorkspaceMoney(item.amount, item.currency) }}</span>
              <time v-if="item.date">{{ formatDateTime(item.date) }}</time>
              <span v-if="!item.inline_only" class="product-relations__empty">无权查看关联记录</span>
            </div>
          </li>
        </ul>
      </ScPanel>
      </li>
    </ScRelationshipFlow>
  </ScSection>
</template>

<script setup lang="ts">
import ScIcon from '../design-system/ScIcon.vue';
import ScPanel from '../design-system/ScPanel.vue';
import ScRelationshipFlow from '../design-system/ScRelationshipFlow.vue';
import ScSection from '../design-system/ScSection.vue';
import { formatWorkspaceMoney, type WorkspaceRelationship, type WorkspaceRelatedRecord } from '../../app/financialWorkspaceContract';
defineProps<{ relationships: WorkspaceRelationship[]; eyebrow: string; title: string }>();
defineEmits<{ open: [item: WorkspaceRelatedRecord] }>();
function formatDateTime(value: unknown): string {
  const date = new Date(String(value || ''));
  return Number.isNaN(date.valueOf()) ? String(value || '') : new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}
</script>

<style scoped>
.product-relations { min-width: 0; padding: var(--sc-product-space-3); border: 1px solid var(--sc-app-border); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-panel); }
.product-relations > header { margin-bottom: var(--sc-product-space-2); }
.product-relations > header p { margin: 0 0 var(--sc-product-space-1); color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.product-relations h2, .product-relations h3 { margin: 0; }
.product-relations h2 { font-size: 18px; }
.product-relations__flow { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--sc-product-space-2); }
.product-relations__flow > li { min-width: 0; }
.product-relations__flow > li > section { min-width: 0; }
.product-relations__heading { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
.product-relations__heading h3 { font-size: 16px; }
.product-relations ul { display: grid; gap: 8px; padding: 0; margin: 0; list-style: none; }
.product-relations button, .product-relations__result { display: flex; width: 100%; box-sizing: border-box; align-items: center; justify-content: space-between; gap: 10px; padding: 12px; border: 0; border-radius: var(--sc-component-panel-radius); background: var(--sc-app-subtle-bg); color: inherit; text-align: left; }
.product-relations button { cursor: pointer; }
.product-relations button:hover, .product-relations button:focus-visible { outline: 2px solid var(--sc-semantic-surface-interactive); outline-offset: 2px; }
.product-relations button > span:first-child, .product-relations__result { min-width: 0; }
.product-relations small, .product-relations__empty { color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.product-relations strong { display: block; margin-top: 3px; overflow-wrap: anywhere; }
.product-relations__meta { display: flex; flex: 0 0 auto; gap: 8px; color: var(--sc-app-text-secondary); }
.product-relations__result { display: grid; justify-content: stretch; }
.product-relations__empty { margin: 0; }
@media (max-width: 600px) { .product-relations { padding: var(--sc-product-space-2); } .product-relations__flow { grid-template-columns: minmax(0, 1fr); } }
</style>
