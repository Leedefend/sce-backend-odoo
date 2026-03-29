<template>
  <template v-for="shell in shells" :key="shell.key">
    <section :class="['contract-detail-shell', shell.shellClass]" data-component="DetailShellLayout">
      <div v-if="shell.title || shell.eyebrow || shell.summary" class="contract-detail-shell__head">
        <div class="contract-detail-shell__title-wrap">
          <span v-if="shell.eyebrow" class="contract-detail-shell__eyebrow">{{ shell.eyebrow }}</span>
          <h3 v-if="shell.title" class="contract-detail-shell__title">{{ shell.title }}</h3>
        </div>
        <span v-if="shell.summary" class="contract-detail-shell__summary">{{ shell.summary }}</span>
      </div>
      <div :class="['contract-detail-shell__body', { 'contract-detail-shell__body--stacked': shell.sections.length <= 1 }]">
        <section
          v-for="section in shell.sections"
          :key="section.key"
          :class="['contract-form-shell', section.shellClass, { 'contract-form-shell--nested': shell.sections.length > 1 }]"
        >
          <div v-if="section.eyebrow || section.summary" class="contract-form-shell__meta">
            <span v-if="section.eyebrow" class="contract-form-shell__eyebrow">{{ section.eyebrow }}</span>
            <span v-if="section.summary" class="contract-form-shell__summary">{{ section.summary }}</span>
          </div>
          <FormSectionTemplate
            :title="section.title"
            :hint="section.hint"
            :tone="section.tone"
            :columns="2"
            :fields="section.fields"
            @field-change="$emit('field-change', $event)"
          >
            <template v-if="showAdvancedToggle(section)" #action>
              <button class="chip-btn" :disabled="busy" @click="$emit('toggle-advanced')">
                {{ advancedExpanded ? '收起' : '展开' }}
              </button>
            </template>
            <template #readonly="{ field }">
              <FieldValue :value="field.value" :field="field.descriptor" />
            </template>
            <template #fallback="{ field }">
              <RelationFallbackRenderer :field="field" :adapter="relationFallbackAdapter" />
            </template>
          </FormSectionTemplate>
        </section>
      </div>
    </section>
  </template>
</template>

<script setup lang="ts">
import FieldValue from '../FieldValue.vue';
import FormSectionTemplate from './FormSection.vue';
import RelationFallbackRenderer from './RelationFallbackRenderer.vue';
import type { DetailShellView, DetailSectionView } from './detailLayout.types';
import type { FormSectionFieldChange } from './formSection.types';
import type { RelationFallbackAdapter } from './relationFallback.types';

const props = defineProps<{
  shells: DetailShellView[];
  busy: boolean;
  isProjectCreatePage: boolean;
  advancedExpanded: boolean;
  relationFallbackAdapter: RelationFallbackAdapter;
}>();

defineEmits<{
  (e: 'field-change', payload: FormSectionFieldChange): void;
  (e: 'toggle-advanced'): void;
}>();

function showAdvancedToggle(section: DetailSectionView) {
  return props.isProjectCreatePage && section.isAdvanced;
}
</script>

<style scoped>
.contract-detail-shell {
  grid-column: 1 / -1;
  border: 1px solid #d9e2ee;
  border-radius: 22px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  padding: 18px 20px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
}

.contract-detail-shell--sheet {
  border-color: #cfe0fb;
  background:
    linear-gradient(180deg, rgba(219, 234, 254, 0.22) 0%, rgba(255, 255, 255, 0) 72px),
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.contract-detail-shell--page {
  border-color: #ddd6fe;
  background:
    linear-gradient(180deg, rgba(237, 233, 254, 0.28) 0%, rgba(255, 255, 255, 0) 72px),
    linear-gradient(180deg, #ffffff 0%, #faf7ff 100%);
}

.contract-detail-shell__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.contract-detail-shell__title-wrap {
  display: grid;
  gap: 2px;
}

.contract-detail-shell__eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #64748b;
}

.contract-detail-shell__title {
  margin: 0;
  font-size: 18px;
  line-height: 1.25;
  color: #0f172a;
}

.contract-detail-shell__summary {
  font-size: 12px;
  color: #64748b;
}

.contract-detail-shell__body {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.contract-detail-shell__body--stacked {
  grid-template-columns: 1fr;
}

.contract-form-shell {
  grid-column: 1 / -1;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background: #fff;
  padding: 14px 16px 12px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.contract-form-shell--sheet {
  border-color: #dbeafe;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.contract-form-shell--group {
  border-color: #e2e8f0;
}

.contract-form-shell--page {
  border-color: #ddd6fe;
  background: linear-gradient(180deg, #ffffff 0%, #faf7ff 100%);
}

.contract-form-shell--nested {
  grid-column: auto;
  border-radius: 16px;
  border-color: #edf2f7;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.55);
  padding: 12px 14px 10px;
}

.contract-form-shell__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.contract-form-shell__eyebrow {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #475569;
}

.contract-form-shell__summary {
  font-size: 12px;
  color: #64748b;
}

.contract-form-shell--nested :deep(.template-form-section) {
  border-top-color: #edf2f7;
}

.contract-form-shell--nested :deep(.template-form-section--core) {
  border-top: 0;
}

.contract-form-shell--nested :deep(.template-form-section-title) {
  font-size: 13px;
  color: #1f2937;
}

.chip-btn {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  cursor: pointer;
}

@media (max-width: 860px) {
  .contract-detail-shell__body {
    grid-template-columns: 1fr;
  }
}
</style>
