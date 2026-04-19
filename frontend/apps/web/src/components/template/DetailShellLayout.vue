<template>
  <template v-for="shell in shells" :key="shell.key">
    <section :class="['contract-detail-shell', shell.shellClass, { 'contract-detail-shell--native': nativeLike }]" data-component="DetailShellLayout">
      <div v-if="!nativeLike && !shell.tabs?.length && (shell.title || shell.eyebrow || shell.summary)" class="contract-detail-shell__head">
        <div class="contract-detail-shell__title-wrap">
          <span v-if="shell.eyebrow" class="contract-detail-shell__eyebrow">{{ shell.eyebrow }}</span>
          <h3 v-if="shell.title" class="contract-detail-shell__title">{{ shell.title }}</h3>
        </div>
        <span v-if="shell.summary" class="contract-detail-shell__summary">{{ shell.summary }}</span>
      </div>
      <div v-if="shell.tabs?.length" :class="['contract-detail-tabs', { 'contract-detail-tabs--native': nativeLike }]">
        <div class="contract-detail-tabs__rail">
          <button
            v-for="tab in shell.tabs"
            :key="tab.key"
            class="contract-detail-tabs__tab"
            :class="{ 'contract-detail-tabs__tab--active': activeTabKey(shell) === tab.key }"
            type="button"
            @click="setActiveTab(shell.key, tab.key)"
          >
            {{ normalizeTabLabel(shell, tab.key, tab.label) }}
          </button>
        </div>
        <div class="contract-detail-tabs__panel">
          <section
            v-for="(section, sectionIndex) in activeTabSections(shell)"
            :key="section.key"
            :class="['contract-form-shell', section.shellClass, { 'contract-form-shell--native': nativeLike }]"
          >
            <div v-if="showTabSectionMeta(shell, section, sectionIndex)" class="contract-form-shell__meta">
              <span v-if="section.eyebrow" class="contract-form-shell__eyebrow">{{ section.eyebrow }}</span>
              <span v-if="section.summary" class="contract-form-shell__summary">{{ section.summary }}</span>
            </div>
            <FormSectionTemplate
              :title="tabSectionTitle(shell, section, sectionIndex)"
              :hint="tabSectionHint(shell, section, sectionIndex)"
              :tone="section.tone"
              :columns="resolveSectionColumns(section)"
              :fields="section.fields"
              :native-like="nativeLike"
              @field-change="$emit('field-change', $event)"
            >
              <template #readonly="{ field }">
                <FieldValue :value="field.value" :field="field.descriptor" />
              </template>
              <template #fallback="{ field }">
                <RelationFallbackRenderer :field="field" :adapter="relationFallbackAdapter" />
              </template>
            </FormSectionTemplate>
          </section>
        </div>
      </div>
      <div
        v-else
        :class="[
          'contract-detail-shell__body',
          {
            'contract-detail-shell__body--stacked': shell.sections.length <= 1,
            'contract-detail-shell__body--native': nativeLike,
          },
        ]"
      >
        <section
          v-for="(section, sectionIndex) in shell.sections"
          :key="section.key"
          :class="['contract-form-shell', section.shellClass, { 'contract-form-shell--nested': shell.sections.length > 1, 'contract-form-shell--native': nativeLike }]"
        >
          <div v-if="!nativeLike && (section.eyebrow || section.summary)" class="contract-form-shell__meta">
            <span v-if="section.eyebrow" class="contract-form-shell__eyebrow">{{ section.eyebrow }}</span>
            <span v-if="section.summary" class="contract-form-shell__summary">{{ section.summary }}</span>
          </div>
          <FormSectionTemplate
            :title="sectionTitle(section, sectionIndex)"
            :hint="section.hint"
            :tone="section.tone"
            :columns="resolveSectionColumns(section)"
            :fields="section.fields"
            :native-like="nativeLike"
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
import { reactive } from 'vue';
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
  nativeLike: boolean;
  advancedExpanded: boolean;
  relationFallbackAdapter: RelationFallbackAdapter;
}>();

defineEmits<{
  (e: 'field-change', payload: FormSectionFieldChange): void;
  (e: 'toggle-advanced'): void;
}>();

const tabState = reactive<Record<string, string>>({});

function showAdvancedToggle(section: DetailSectionView) {
  return props.isProjectCreatePage && section.isAdvanced;
}

function activeTabKey(shell: DetailShellView) {
  const fallback = shell.tabs?.[0]?.key || '';
  return tabState[shell.key] || fallback;
}

function setActiveTab(shellKey: string, tabKey: string) {
  tabState[shellKey] = tabKey;
}

function activeTabSections(shell: DetailShellView) {
  const activeKey = activeTabKey(shell);
  return shell.tabs?.find((tab) => tab.key === activeKey)?.sections || shell.tabs?.[0]?.sections || [];
}

function activeTabLabel(shell: DetailShellView) {
  const activeKey = activeTabKey(shell);
  return normalizeTabLabel(shell, activeKey, shell.tabs?.find((tab) => tab.key === activeKey)?.label || shell.tabs?.[0]?.label || '');
}

function tabSectionTitle(shell: DetailShellView, section: DetailSectionView, sectionIndex: number) {
  const title = normalizeSectionTitle(String(section.title || '').trim());
  if (props.nativeLike && !title) return '';
  if (props.nativeLike && isFieldDerivedTitle(title, section)) return '';
  if (!title) return fallbackSectionTitle(sectionIndex, section);
  if (title === activeTabLabel(shell)) return '';
  if (section.fields.length <= 2 && section.fields[0]?.label === title) return '';
  return title;
}

function tabSectionHint(shell: DetailShellView, section: DetailSectionView, sectionIndex: number) {
  const hint = String(section.hint || '').trim();
  if (!hint) return '';
  const title = tabSectionTitle(shell, section, sectionIndex);
  if (!title) return '';
  if (hint.toLowerCase() === title.toLowerCase()) return '';
  return hint;
}

function showTabSectionMeta(shell: DetailShellView, section: DetailSectionView, sectionIndex: number) {
  if (props.nativeLike) return false;
  return Boolean(tabSectionTitle(shell, section, sectionIndex) && (section.eyebrow || section.summary));
}

function sectionTitle(section: DetailSectionView, sectionIndex: number) {
  const title = normalizeSectionTitle(String(section.title || '').trim());
  if (props.nativeLike && !title) return '';
  if (props.nativeLike && isFieldDerivedTitle(title, section)) return '';
  if (!title) return fallbackSectionTitle(sectionIndex, section);
  return title;
}

function normalizeSectionTitle(rawTitle: string) {
  if (isGenericSectionTitle(rawTitle)) return '';
  return rawTitle;
}

function isGenericSectionTitle(rawTitle: string): boolean {
  const title = String(rawTitle || '').trim();
  if (!title) return true;
  const lowered = title.toLowerCase();
  if (['主体信息', '信息分组', '分组', '核心信息'].includes(title)) return true;
  if (lowered === 'group' || lowered === 'sheet' || lowered === 'page' || lowered === 'notebook') return true;
  if (title.includes('_')) return true;
  if (/^[a-z0-9.:-]+$/i.test(title)) return true;
  return false;
}

function fallbackSectionTitle(sectionIndex: number, section?: DetailSectionView): string {
  if (props.nativeLike) return '';
  const semanticTitle = resolveSemanticSectionTitle(section);
  if (semanticTitle) return semanticTitle;
  const firstFieldLabel = String(section?.fields?.[0]?.label || '').trim();
  if (firstFieldLabel && !isGenericSectionTitle(firstFieldLabel)) {
    return `${firstFieldLabel}信息`;
  }
  return `信息分组 ${sectionIndex + 1}`;
}

function resolveSemanticSectionTitle(section?: DetailSectionView): string {
  const fieldNames = (section?.fields || []).map((field) => String(field.name || '').trim()).filter(Boolean);
  if (!fieldNames.length) return '';
  const hasAny = (candidates: string[]) => candidates.some((name) => fieldNames.includes(name));
  if (hasAny(['name', 'is_favorite', 'label_tasks'])) return '主体信息';
  if (hasAny(['user_id', 'manager_id', 'owner_id', 'date_start', 'date'])) return '管理信息';
  if (hasAny(['description'])) return '描述';
  if (hasAny(['privacy_visibility', 'allow_rating', 'alias_contact', 'alias_name', 'alias_email'])) return '设置';
  if (hasAny(['task_ids', 'collaborator_ids', 'analytic_account_id'])) return '协作 / 系统';
  return '';
}

function normalizeTabLabel(shell: DetailShellView, tabKey: string, rawLabel: string): string {
  const label = String(rawLabel || '').trim();
  const tab = shell.tabs?.find((item) => item.key === tabKey);
  if (props.nativeLike && tab && tab.sections.some((section) => isFieldDerivedTitle(label, section))) {
    return resolveSemanticTabLabel(shell, tabKey) || fallbackTabLabel(shell.tabs?.findIndex((item) => item.key === tabKey) ?? 0);
  }
  if (label && !isGenericTabLabel(label)) return label;
  const semanticLabel = resolveSemanticTabLabel(shell, tabKey);
  if (semanticLabel) return semanticLabel;
  const index = shell.tabs?.findIndex((tab) => tab.key === tabKey) ?? -1;
  return fallbackTabLabel(index >= 0 ? index : 0);
}

function isGenericTabLabel(rawLabel: string): boolean {
  const label = String(rawLabel || '').trim().toLowerCase();
  if (!label) return true;
  return ['page', 'tab', 'notebook', '默认', 'default'].includes(label);
}

function resolveSemanticTabLabel(shell: DetailShellView, tabKey: string): string {
  const tab = shell.tabs?.find((item) => item.key === tabKey);
  if (!tab || !Array.isArray(tab.sections)) return '';
  for (const section of tab.sections) {
    const semanticTitle = resolveSemanticSectionTitle(section);
    if (semanticTitle && semanticTitle !== '主体信息' && semanticTitle !== '管理信息') return semanticTitle;
    const sectionTitle = String(section.title || '').trim();
    if (props.nativeLike && isFieldDerivedTitle(sectionTitle, section)) continue;
    if (sectionTitle && !isGenericSectionTitle(sectionTitle)) return sectionTitle;
  }
  return '';
}

function isFieldDerivedTitle(titleRaw: string, section?: DetailSectionView): boolean {
  const title = String(titleRaw || '').trim();
  const firstFieldLabel = String(section?.fields?.[0]?.label || '').trim();
  if (!title || !firstFieldLabel) return false;
  if (title === firstFieldLabel) return true;
  if (title === `${firstFieldLabel}信息`) return true;
  return section?.fields?.length === 1 && title.includes(firstFieldLabel);
}

function fallbackTabLabel(tabIndex: number): string {
  return `页签 ${tabIndex + 1}`;
}

function resolveSectionColumns(section: DetailSectionView): 1 | 2 {
  return section.columns === 1 ? 1 : 2;
}
</script>

<style scoped>
.contract-detail-shell {
  grid-column: 1 / -1;
  border: 1px solid rgba(203, 213, 225, 0.95);
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  padding: 16px 18px;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
}

.contract-detail-shell--native {
  border: 0;
  border-radius: 0;
  background: #fff;
  padding: 0;
  box-shadow: none;
}

.contract-detail-shell--sheet {
  border-color: #dbeafe;
  background:
    linear-gradient(180deg, rgba(219, 234, 254, 0.18) 0%, rgba(255, 255, 255, 0) 68px),
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.contract-detail-shell--page {
  border-color: #e9d5ff;
  background:
    linear-gradient(180deg, rgba(237, 233, 254, 0.18) 0%, rgba(255, 255, 255, 0) 68px),
    linear-gradient(180deg, #ffffff 0%, #faf7ff 100%);
}

.contract-detail-shell__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
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
  font-size: 17px;
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
  gap: 14px;
}

.contract-detail-shell__body--stacked {
  grid-template-columns: 1fr;
}

.contract-detail-shell__body--native {
  grid-template-columns: 1fr;
  gap: 0;
}

.contract-detail-tabs {
  display: grid;
  gap: 14px;
}

.contract-detail-tabs__rail {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px;
  border: 1px solid rgba(203, 213, 225, 0.72);
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.92);
}

.contract-detail-tabs__tab {
  border: 1px solid transparent;
  background: transparent;
  color: #334155;
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.contract-detail-tabs__tab--active {
  border-color: rgba(191, 219, 254, 0.9);
  background: #fff;
  color: #0f172a;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
}

.contract-detail-tabs--native .contract-detail-tabs__rail {
  border: 0;
  border-bottom: 1px solid #e5e7eb;
  border-radius: 0;
  background: transparent;
  padding: 0 0 6px;
}

.contract-detail-tabs--native .contract-detail-tabs__tab {
  border: 0;
  border-bottom: 2px solid transparent;
  border-radius: 0;
  background: transparent;
  color: #4b5563;
  padding: 6px 8px;
  font-weight: 500;
}

.contract-detail-tabs--native .contract-detail-tabs__tab--active {
  border-color: #6b7280;
  background: transparent;
  color: #111827;
}

.contract-detail-tabs__panel {
  display: grid;
  gap: 4px;
}

.contract-form-shell {
  grid-column: 1 / -1;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 14px;
  background: #fff;
  padding: 14px 16px 12px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
}

.contract-form-shell--native {
  border: 0;
  border-radius: 0;
  background: #fff;
  box-shadow: none;
  padding: 4px 0;
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
  border-radius: 12px;
  border-color: #e2e8f0;
  background: rgba(248, 250, 252, 0.92);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.55);
  padding: 12px 14px 10px;
}

.contract-form-shell--native.contract-form-shell--nested {
  border: 0;
  border-radius: 0;
  background: #fff;
  box-shadow: none;
  padding: 4px 0;
}

.contract-form-shell--native :deep(.template-form-section-grid) {
  row-gap: 6px;
  column-gap: 32px;
}

.contract-form-shell--native :deep(.template-form-section-head) {
  margin-bottom: 4px;
}

.contract-form-shell--native :deep(.template-form-section-title) {
  font-size: 13px;
  font-weight: 500;
}

.contract-form-shell--native :deep(.label) {
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 2px;
}

.contract-form-shell--native :deep(.input) {
  height: 28px;
  min-height: 28px;
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 13px;
}

.contract-form-shell--native :deep(.readonly-value) {
  min-height: 28px;
  font-size: 13px;
}

.contract-form-shell__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
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
