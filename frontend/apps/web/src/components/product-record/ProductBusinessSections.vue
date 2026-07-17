<template>
  <ScPanel v-if="sections.length" class="product-sections" aria-labelledby="product-details-title">
    <header><p>{{ eyebrow }}</p><h2 id="product-details-title">{{ title }}</h2></header>
    <section v-for="section in sections" :key="section.key">
      <h3>{{ section.label }}</h3>
      <p v-if="!section.rows.length" class="product-sections__empty">{{ section.empty_text }}</p>
      <div v-else class="product-sections__table" tabindex="0" :aria-label="`${section.label}，可横向滚动查看`">
        <ScDataTable>
          <thead><tr><th v-for="cell in section.rows[0]?.cells || []" :key="cell.key" scope="col">{{ cell.label }}</th></tr></thead>
          <tbody><tr v-for="row in section.rows" :key="row.key"><td v-for="cell in row.cells" :key="cell.key">{{ cellText(cell) }}</td></tr></tbody>
        </ScDataTable>
      </div>
    </section>
  </ScPanel>
</template>

<script setup lang="ts">
import ScDataTable from '../design-system/ScDataTable.vue';
import ScPanel from '../design-system/ScPanel.vue';
import { formatWorkspaceMoney, type WorkspaceDetailCell, type WorkspaceDetailSection } from '../../app/financialWorkspaceContract';
defineProps<{ sections: WorkspaceDetailSection[]; eyebrow: string; title: string }>();
function cellText(cell: WorkspaceDetailCell): string {
  if (cell.kind === 'money') return formatWorkspaceMoney(cell.value, cell.currency);
  if (cell.value === null || cell.value === undefined || cell.value === '') return '未提供';
  return String(cell.value);
}
</script>

<style scoped>
.product-sections { min-width: 0; padding: var(--sc-product-space-3); border: 1px solid var(--sc-app-border); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-panel); }
.product-sections > header { margin-bottom: var(--sc-product-space-2); }
.product-sections header p { margin: 0 0 var(--sc-product-space-1); color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.product-sections h2, .product-sections h3 { margin: 0; }
.product-sections h2 { font-size: 18px; }
.product-sections h3 { margin-bottom: var(--sc-product-space-2); font-size: 16px; }
.product-sections > section + section { margin-top: var(--sc-product-space-3); }
.product-sections__table { width: 100%; overflow-x: auto; outline-offset: 3px; }
.product-sections table { width: 100%; min-width: 520px; border-collapse: collapse; }
.product-sections th, .product-sections td { padding: var(--sc-product-space-2); border-bottom: 1px solid var(--sc-app-border); text-align: left; }
.product-sections td:has(+ td), .product-sections td:last-child { font-variant-numeric: tabular-nums; }
.product-sections__empty { color: var(--sc-app-text-secondary); }
@media (max-width: 600px) { .product-sections { padding: var(--sc-product-space-2); } }
</style>
