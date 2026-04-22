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
  border: 1px solid var(--ui-color-border-strong);
  border-radius: var(--ui-radius-md);
  background:
    linear-gradient(180deg, rgba(240, 246, 250, 0.42), rgba(255, 255, 255, 0) 76px),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 245, 239, 0.94) 100%);
  padding: var(--ui-space-4);
  box-shadow: var(--ui-shadow-sm);
}

.contract-detail-shell--native {
  border: 0;
  border-radius: 0;
  background: #fff;
  padding: 0;
  box-shadow: none;
}

.contract-detail-shell--sheet {
  border-color: rgba(61, 120, 159, 0.18);
  background:
    linear-gradient(180deg, rgba(219, 234, 244, 0.42) 0%, rgba(255, 255, 255, 0) 68px),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(240, 246, 250, 0.62) 100%);
}

.contract-detail-shell--page {
  border-color: rgba(61, 120, 159, 0.14);
  background:
    linear-gradient(180deg, rgba(244, 241, 235, 0.82) 0%, rgba(255, 255, 255, 0) 68px),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 245, 239, 0.94) 100%);
}

.contract-detail-shell__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--ui-space-3);
  margin-bottom: var(--ui-space-3);
  padding-bottom: var(--ui-space-3);
  border-bottom: 1px solid var(--ui-color-border);
}

.contract-detail-shell__title-wrap {
  display: grid;
  gap: 2px;
}

.contract-detail-shell__eyebrow {
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-bold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ui-color-ink-soft);
}

.contract-detail-shell__title {
  margin: 0;
  font-size: var(--ui-font-size-xl);
  line-height: 1.25;
  color: var(--ui-color-ink-strong);
}

.contract-detail-shell__summary {
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-muted);
}

.contract-detail-shell__body {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--ui-space-3);
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
  gap: var(--ui-space-3);
}

.contract-detail-tabs__rail {
  display: flex;
  flex-wrap: wrap;
  gap: var(--ui-space-2);
  padding: var(--ui-space-1);
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-sm);
  background: rgba(248, 245, 239, 0.84);
}

.contract-detail-tabs__tab {
  border: 1px solid transparent;
  background: transparent;
  color: var(--ui-color-ink-muted);
  border-radius: var(--ui-radius-pill);
  padding: 7px 12px;
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-semibold);
  cursor: pointer;
}

.contract-detail-tabs__tab--active {
  border-color: rgba(61, 120, 159, 0.2);
  background: rgba(255, 255, 255, 0.98);
  color: var(--ui-color-ink-strong);
  box-shadow: var(--ui-shadow-xs);
}

.contract-detail-tabs--native .contract-detail-tabs__rail {
  border: 0;
  border-bottom: 1px solid var(--ui-color-border);
  border-radius: 0;
  background: transparent;
  padding: 0 0 6px;
}

.contract-detail-tabs--native .contract-detail-tabs__tab {
  border: 0;
  border-bottom: 2px solid transparent;
  border-radius: 0;
  background: transparent;
  color: var(--ui-color-ink-muted);
  padding: 6px 8px;
  font-weight: var(--ui-font-weight-medium);
}

.contract-detail-tabs--native .contract-detail-tabs__tab--active {
  border-color: var(--ui-color-primary-700);
  background: transparent;
  color: var(--ui-color-ink-strong);
}

.contract-detail-tabs__panel {
  display: grid;
  gap: var(--ui-space-1);
}

.contract-form-shell {
  grid-column: 1 / -1;
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-sm);
  background: rgba(255, 255, 255, 0.94);
  padding: var(--ui-space-4);
  box-shadow: var(--ui-shadow-xs);
}

.contract-form-shell--native {
  border: 0;
  border-radius: 0;
  background: #fff;
  box-shadow: none;
  padding: 4px 0;
}

.contract-form-shell--sheet {
  border-color: rgba(61, 120, 159, 0.18);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(240, 246, 250, 0.6) 100%);
}

.contract-form-shell--group {
  border-color: var(--ui-color-border);
}

.contract-form-shell--page {
  border-color: rgba(61, 120, 159, 0.12);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 245, 239, 0.9) 100%);
}

.contract-form-shell--nested {
  grid-column: auto;
  border-radius: var(--ui-radius-sm);
  border-color: var(--ui-color-border);
  background: rgba(248, 245, 239, 0.78);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.55);
  padding: var(--ui-space-3);
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
  gap: var(--ui-space-2);
  margin-bottom: var(--ui-space-3);
}

.contract-form-shell__eyebrow {
  display: inline-flex;
  align-items: center;
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-bold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ui-color-ink-muted);
}

.contract-form-shell__summary {
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-soft);
}

.contract-form-shell--nested :deep(.template-form-section) {
  border-top-color: var(--ui-color-border-muted);
}

.contract-form-shell--nested :deep(.template-form-section--core) {
  border-top: 0;
}

.contract-form-shell--nested :deep(.template-form-section-title) {
  font-size: 13px;
  color: var(--ui-color-ink);
}

.chip-btn {
  padding: 4px 8px;
  border-radius: var(--ui-radius-pill);
  border: 1px solid var(--ui-color-border);
  background: rgba(255, 255, 255, 0.92);
  color: var(--ui-color-ink);
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-medium);
  cursor: pointer;
}

@media (max-width: 860px) {
  .contract-detail-shell__body {
    grid-template-columns: 1fr;
  }
}
</style>
