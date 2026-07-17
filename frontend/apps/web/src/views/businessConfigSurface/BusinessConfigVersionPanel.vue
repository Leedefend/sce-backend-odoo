<template>
  <section class="version-panel">
    <div class="edit-panel-head">
      <div>
        <h2>{{ title }}</h2>
        <p>{{ description }}</p>
      </div>
      <ScButton type="button" class="ghost small" :disabled="loading" @click="$emit('close')">
        收起版本记录
      </ScButton>
    </div>
    <div class="version-guide">
      <strong>{{ guide.title }}</strong>
      <span>{{ guide.body }}</span>
    </div>
    <div v-if="!contracts.length" class="empty-state">{{ emptyText }}</div>
    <div v-else class="version-list">
      <article v-for="contract in contracts" :key="contract.id" class="version-card">
        <div class="version-card-head">
          <div class="version-card-title">
            <strong>{{ viewTypeLabel(contract.view_type) }}</strong>
            <span>{{ contractDisplayName(contract) }}</span>
            <em>{{ contractImpactText(contract) }}</em>
          </div>
          <div class="version-card-actions">
            <span class="version-current-badge">当前生效 v{{ contract.version_no }}</span>
            <ScButton
              type="button"
              class="ghost small"
              :disabled="loading || saving || contract.versions.length < 2"
              @click="$emit('rollback', contract)"
            >
              {{ rollbackButtonLabel(contract) }}
            </ScButton>
          </div>
        </div>
        <div class="version-summary">
          <span>表单字段 {{ contract.summary.form_field_count }}</span>
          <span>列表列 {{ contract.summary.list_column_count }}</span>
          <span>筛选 {{ contract.summary.search_filter_count }}</span>
          <span>分组 {{ contract.summary.search_group_by_count }}</span>
          <span v-if="contract.summary.analysis_item_count">分析项 {{ contract.summary.analysis_item_count }}</span>
        </div>
        <div class="version-decision-note">
          <span>{{ contractDecisionText(contract) }}</span>
        </div>
        <div v-if="contract.summary.analysis_items?.length" class="analysis-summary-list">
          <span v-for="item in contract.summary.analysis_items.slice(0, 12)" :key="item">{{ analysisItemLabel(item) }}</span>
        </div>
        <div class="version-rows">
          <div
            v-for="version in contract.versions"
            :key="version.id"
            class="version-row"
            :class="{ 'version-row--current': version.version_no === contract.version_no }"
          >
            <span class="version-row-no">v{{ version.version_no }}</span>
            <span>{{ version.version_no === contract.version_no ? '当前生效' : versionStatusLabel(version.status) }}</span>
            <span>保存人 {{ version.created_by || '-' }}</span>
            <span>{{ versionSummaryText(version.summary) }}</span>
            <span class="version-row-delta">{{ versionDeltaText(contract.summary, version.summary, version.version_no === contract.version_no) }}</span>
            <ScButton
              type="button"
              class="link-button"
              :disabled="loading || saving || version.version_no === contract.version_no"
              @click="$emit('rollback', contract, version.version_no)"
            >
              {{ version.version_no === contract.version_no ? '当前生效版本' : '恢复到此版本配置' }}
            </ScButton>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { BusinessConfigContractVersionsPayload } from '../../api/businessConfig';
import ScButton from '../../components/design-system/ScButton.vue';

type Contract = BusinessConfigContractVersionsPayload['contracts'][number];
type Summary = Contract['summary'];

defineProps<{
  title: string;
  description: string;
  guide: { title: string; body: string };
  emptyText: string;
  contracts: Contract[];
  loading: boolean;
  saving: boolean;
  viewTypeLabel: (viewType: string) => string;
  contractDisplayName: (contract: Contract) => string;
  contractImpactText: (contract: Contract) => string;
  rollbackButtonLabel: (contract: Contract) => string;
  contractDecisionText: (contract: Contract) => string;
  analysisItemLabel: (item: string) => string;
  versionStatusLabel: (status: string) => string;
  versionSummaryText: (summary: Summary) => string;
  versionDeltaText: (current: Summary, target: Summary, isCurrent: boolean) => string;
}>();

defineEmits<{
  close: [];
  rollback: [contract: Contract, versionNo?: number];
}>();
</script>
