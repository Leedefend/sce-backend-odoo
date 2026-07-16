<template>
  <article class="financial-workspace product-record" :data-workspace-kind="contract.kind" :data-identity-source="contract.source?.kind || ''">
    <nav v-if="contract.entry_actions?.length" class="product-record__entry-actions" aria-label="可发起业务">
      <button v-for="action in contract.entry_actions" :key="action.key" type="button" class="sc-btn sc-btn-primary" @click="openEntryAction(action.route)">{{ action.label }}</button>
    </nav>

    <ProductRecordStatus :state="contract.state" />
    <p v-if="contract.currency_risk?.mismatch" class="product-record__risk" role="status">
      币种风险：{{ contract.currency_risk.message || '关联记录币种不一致，系统未执行隐式换算。' }}
    </p>
    <ProductFactGrid
      :facts="businessFacts"
      group="business"
      :eyebrow="sectionCopy('facts', 'eyebrow', '关键业务事实')"
      :title="sectionCopy('facts', 'title', '业务概览')"
    />
    <ProductFactGrid
      :facts="moneyFacts"
      group="money"
      :eyebrow="sectionCopy('money', 'eyebrow', '金额事实')"
      :title="sectionCopy('money', 'title', '金额与币种')"
    />
    <ProductRelationshipFlow
      :relationships="contract.relationships"
      :eyebrow="sectionCopy('relationships', 'eyebrow', '上下游关系')"
      :title="sectionCopy('relationships', 'title', '业务关系链')"
      @open="openRelated"
    />
    <ProductBusinessSections
      :sections="contract.details"
      :eyebrow="sectionCopy('details', 'eyebrow', '业务明细')"
      :title="sectionCopy('details', 'title', '明细事实')"
    />
    <ProductAuditSection
      :facts="contract.audit"
      :eyebrow="sectionCopy('audit', 'eyebrow', '审计信息')"
      :title="sectionCopy('audit', 'title', '记录信息')"
    />
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { pickContractNavQuery } from '../../app/navigationContext';
import type { FinancialWorkspaceContract, WorkspaceRelatedRecord, WorkspaceRouteTarget } from '../../app/financialWorkspaceContract';
import ProductAuditSection from '../product-record/ProductAuditSection.vue';
import ProductBusinessSections from '../product-record/ProductBusinessSections.vue';
import ProductFactGrid from '../product-record/ProductFactGrid.vue';
import ProductRecordStatus from '../product-record/ProductRecordStatus.vue';
import ProductRelationshipFlow from '../product-record/ProductRelationshipFlow.vue';

const props = defineProps<{ contract: FinancialWorkspaceContract }>();
const route = useRoute();
const router = useRouter();
const businessFacts = computed(() => props.contract.facts.filter((fact) => fact.group !== 'money' && fact.kind !== 'money'));
const moneyFacts = computed(() => props.contract.facts.filter((fact) => fact.group === 'money' || fact.kind === 'money'));

function sectionCopy(section: string, key: 'eyebrow' | 'title', fallback: string) {
  return String(props.contract.presentation?.[section]?.[key] || fallback);
}

async function openRelated(item: WorkspaceRelatedRecord) {
  if (!item.route) return;
  await openTarget(item.route);
}

async function openEntryAction(target: WorkspaceRouteTarget) {
  await openTarget(target);
}

async function openTarget(target: WorkspaceRouteTarget) {
  await router.push({
    name: target.name,
    params: target.params,
    query: pickContractNavQuery(route.query as Record<string, unknown>, target.query || {}),
  });
}
</script>

<style scoped>
.product-record { display: grid; min-width: 0; max-width: 100%; gap: var(--sc-product-space-3); margin-bottom: var(--sc-product-space-3); }
.product-record__entry-actions { display: flex; justify-content: flex-end; gap: var(--sc-product-space-2); }
.product-record__risk { padding: var(--sc-product-space-2); margin: 0; border: 1px solid var(--sc-app-warning-border); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-warning-bg); color: var(--sc-app-warning-text); }
@media (max-width: 600px) { .product-record { gap: var(--sc-product-space-2); } .product-record__entry-actions { justify-content: stretch; } .product-record__entry-actions button { width: 100%; } }
</style>
