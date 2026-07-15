<template>
  <article class="financial-workspace" :data-workspace-kind="contract.kind" :data-identity-source="contract.source?.kind || ''">
    <section class="financial-workspace__section" aria-labelledby="workspace-facts-title">
      <div class="financial-workspace__section-heading">
        <div>
          <p class="financial-workspace__eyebrow">关键事实摘要</p>
          <h2 id="workspace-facts-title">金额与业务信息</h2>
        </div>
        <span class="financial-workspace__status" :data-state="contract.state.value">
          <span aria-hidden="true">●</span>
          状态：{{ contract.state.label || '未标注' }}
        </span>
      </div>
      <p v-if="contract.currency_risk?.mismatch" class="financial-workspace__risk" role="status">
        币种风险：{{ contract.currency_risk.message || '关联记录币种不一致，系统未执行隐式换算。' }}
      </p>
      <dl class="financial-workspace__facts">
        <div v-for="fact in contract.facts" :key="fact.key" class="financial-workspace__fact" :data-fact-key="fact.key">
          <dt>{{ fact.label }}</dt>
          <dd :class="{ 'financial-workspace__money': fact.kind === 'money' }">{{ factText(fact) }}</dd>
        </div>
      </dl>
    </section>

    <section class="financial-workspace__section" aria-labelledby="workspace-relations-title">
      <div class="financial-workspace__section-heading">
        <div>
          <p class="financial-workspace__eyebrow">上下游关系</p>
          <h2 id="workspace-relations-title">业务关系链</h2>
        </div>
      </div>
      <div class="financial-workspace__relations">
        <section v-for="relation in contract.relationships" :key="relation.key" class="financial-workspace__relation" :data-relation-key="relation.key">
          <div class="financial-workspace__relation-title">
            <h3>{{ relation.label }}</h3>
            <span>{{ relation.records.length }} 条</span>
          </div>
          <p v-if="!relation.records.length" class="financial-workspace__empty">{{ relation.empty_text }}</p>
          <ul v-else>
            <li v-for="item in relation.records" :key="`${item.model}-${item.id}`">
              <button v-if="item.route" type="button" class="financial-workspace__link" @click="openRelated(item)">
                <span>{{ item.label }}</span>
                <span aria-hidden="true">→</span>
              </button>
              <div v-else class="financial-workspace__inline-result">
                <strong>{{ item.label }}</strong>
                <span v-if="item.amount !== null && item.amount !== undefined">{{ formatWorkspaceMoney(item.amount, item.currency) }}</span>
                <time v-if="item.date">{{ formatDateTime(item.date) }}</time>
                <span v-if="!item.inline_only" class="financial-workspace__restricted">当前权限下仅可查看关系名称</span>
              </div>
            </li>
          </ul>
        </section>
      </div>
    </section>

    <section v-if="contract.details.length" class="financial-workspace__section" aria-labelledby="workspace-details-title">
      <div class="financial-workspace__section-heading">
        <div>
          <p class="financial-workspace__eyebrow">业务明细</p>
          <h2 id="workspace-details-title">明细事实</h2>
        </div>
      </div>
      <section v-for="section in contract.details" :key="section.key" class="financial-workspace__detail">
        <h3>{{ section.label }}</h3>
        <p v-if="!section.rows.length" class="financial-workspace__empty">{{ section.empty_text }}</p>
        <div v-else class="financial-workspace__table-wrap">
          <table>
            <thead>
              <tr><th v-for="cell in section.rows[0]?.cells || []" :key="cell.key">{{ cell.label }}</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in section.rows" :key="row.key">
                <td v-for="cell in row.cells" :key="cell.key">{{ detailCellText(cell) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </section>

    <section class="financial-workspace__section financial-workspace__audit" aria-labelledby="workspace-audit-title">
      <div class="financial-workspace__section-heading">
        <div>
          <p class="financial-workspace__eyebrow">审计信息</p>
          <h2 id="workspace-audit-title">记录信息</h2>
        </div>
      </div>
      <dl>
        <div v-for="fact in contract.audit" :key="fact.key">
          <dt>{{ fact.label }}</dt>
          <dd>{{ factText(fact) }}</dd>
        </div>
      </dl>
    </section>
  </article>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { pickContractNavQuery } from '../../app/navigationContext';
import {
  formatWorkspaceMoney,
  type FinancialWorkspaceContract,
  type WorkspaceFact,
  type WorkspaceDetailCell,
  type WorkspaceRelatedRecord,
} from '../../app/financialWorkspaceContract';

defineProps<{ contract: FinancialWorkspaceContract }>();

const route = useRoute();
const router = useRouter();

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—';
  return String(value);
}

function formatDateTime(value: unknown): string {
  const text = String(value || '').trim();
  if (!text) return '—';
  const date = new Date(text);
  return Number.isNaN(date.valueOf()) ? text : new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function factText(fact: WorkspaceFact): string {
  if (fact.kind === 'money') return formatWorkspaceMoney(fact.value, fact.currency);
  if (fact.kind === 'datetime') return formatDateTime(fact.value);
  return displayValue(fact.value);
}

function detailCellText(cell: WorkspaceDetailCell): string {
  return cell.kind === 'money' ? formatWorkspaceMoney(cell.value, cell.currency) : displayValue(cell.value);
}

async function openRelated(item: WorkspaceRelatedRecord) {
  if (!item.route) return;
  await router.push({
    name: item.route.name,
    params: item.route.params,
    query: pickContractNavQuery(route.query as Record<string, unknown>, item.route.query || {}),
  });
}
</script>

<style scoped>
.financial-workspace { display: grid; min-width: 0; max-width: 100%; gap: var(--sc-product-space-3); margin-bottom: var(--sc-product-space-3); }
.financial-workspace__section { min-width: 0; max-width: 100%; box-sizing: border-box; padding: var(--sc-product-space-3); border: 1px solid var(--sc-app-border); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-panel); }
.financial-workspace__section-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--sc-product-space-2); margin-bottom: var(--sc-product-space-2); }
.financial-workspace__section h2, .financial-workspace__section h3, .financial-workspace__section p { margin: 0; }
.financial-workspace__section h2 { font-size: 18px; }
.financial-workspace__eyebrow { margin-bottom: var(--sc-product-space-1) !important; color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.financial-workspace__status { display: inline-flex; gap: var(--sc-product-space-1); align-items: center; padding: var(--sc-product-space-1) var(--sc-product-space-2); border-radius: var(--sc-component-badge-radius); background: var(--sc-app-subtle-bg); font-weight: 600; white-space: nowrap; }
.financial-workspace__risk { padding: var(--sc-product-space-2); margin-bottom: var(--sc-product-space-2) !important; border: 1px solid var(--sc-app-warning-border); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-warning-bg); color: var(--sc-app-warning-text); }
.financial-workspace__facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: var(--sc-product-space-2); margin: 0; }
.financial-workspace__fact { min-width: 0; padding: var(--sc-product-space-2); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-subtle-bg); }
.financial-workspace__fact dt, .financial-workspace__audit dt { color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.financial-workspace__fact dd, .financial-workspace__audit dd { margin: var(--sc-product-space-1) 0 0; overflow-wrap: anywhere; }
.financial-workspace__money { font-size: 18px; font-variant-numeric: tabular-nums; font-weight: 700; }
.financial-workspace__relations { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--sc-product-space-2); }
.financial-workspace__relation { min-width: 0; padding: var(--sc-product-space-2); border: 1px solid var(--sc-app-border); border-radius: var(--sc-component-panel-radius); }
.financial-workspace__relation-title { display: flex; justify-content: space-between; gap: var(--sc-product-space-1); margin-bottom: var(--sc-product-space-1); }
.financial-workspace__relation ul { display: grid; gap: var(--sc-product-space-1); padding: 0; margin: 0; list-style: none; }
.financial-workspace__link { display: flex; width: 100%; align-items: center; justify-content: space-between; gap: var(--sc-product-space-1); padding: var(--sc-product-space-2); border: 0; border-radius: var(--sc-component-panel-radius); color: var(--sc-semantic-surface-interactive); background: var(--sc-app-subtle-bg); text-align: left; cursor: pointer; }
.financial-workspace__link:hover, .financial-workspace__link:focus-visible { text-decoration: underline; outline: 2px solid var(--sc-semantic-surface-interactive); outline-offset: 2px; }
.financial-workspace__inline-result { display: grid; gap: var(--sc-product-space-1); padding: var(--sc-product-space-2); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-subtle-bg); }
.financial-workspace__restricted, .financial-workspace__empty { color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.financial-workspace__detail { min-width: 0; max-width: 100%; }
.financial-workspace__detail + .financial-workspace__detail { margin-top: var(--sc-product-space-2); }
.financial-workspace__table-wrap { width: 100%; min-width: 0; max-width: 100%; overflow-x: auto; margin-top: var(--sc-product-space-2); }
.financial-workspace table { width: 100%; min-width: 520px; border-collapse: collapse; }
.financial-workspace th, .financial-workspace td { padding: var(--sc-product-space-2); border-bottom: 1px solid var(--sc-app-border); text-align: left; }
.financial-workspace__audit dl { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: var(--sc-product-space-2); margin: 0; }
@media (max-width: 600px) {
  .financial-workspace { gap: var(--sc-product-space-2); }
  .financial-workspace__section { padding: var(--sc-product-space-2); }
  .financial-workspace__section-heading { align-items: stretch; flex-direction: column; }
  .financial-workspace__status { align-self: flex-start; white-space: normal; }
  .financial-workspace__facts, .financial-workspace__relations, .financial-workspace__audit dl { grid-template-columns: minmax(0, 1fr); }
}
</style>
