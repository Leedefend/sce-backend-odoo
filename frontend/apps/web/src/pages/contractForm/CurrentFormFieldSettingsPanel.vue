<template>
  <section class="contract-form-settings">
    <header class="contract-form-settings-head">
      <div>
        <h4>当前页面字段配置</h4>
        <p>{{ scope.summary }}</p>
      </div>
      <span class="contract-form-settings-field-count">字段 {{ fieldCount }}</span>
    </header>
    <div class="contract-form-design-strip" aria-label="页面设计步骤">
      <div>
        <span>当前页面</span>
        <strong>{{ scope.scope }}</strong>
      </div>
      <div>
        <span>可配置项</span>
        <strong>字段名称、顺序、显示隐藏、新增字段</strong>
      </div>
      <div>
        <span>影响范围</span>
        <strong>{{ scope.saveTarget }}</strong>
      </div>
    </div>
    <section v-if="activeTab === 'fields'" class="contract-form-settings-fields">
      <header class="contract-form-settings-section-head">
        <div>
          <strong>字段配置</strong>
          <span>按旧表单分区点选字段，或按住字段拖拽调整顺序和分组。</span>
        </div>
        <div class="contract-form-settings-section-actions">
          <button
            class="ghost small contract-field-central-create"
            type="button"
            :disabled="busy"
            @click="$emit('open-custom-field-create')"
          >
            新增字段
          </button>
          <button
            v-if="suggestedHiddenCount"
            class="ghost small"
            type="button"
            :disabled="busy"
            @click="$emit('hide-suggested-internal-fields')"
          >
            隐藏系统字段 {{ suggestedHiddenCount }}
          </button>
        </div>
      </header>
      <div class="contract-form-designer-control-grid">
        <aside class="contract-form-designer-sidebar" aria-label="表单设计器导航">
          <header class="contract-form-designer-sidebar-head">
            <div>
              <span>字段目录</span>
              <strong>{{ fieldCount }} 个字段</strong>
            </div>
            <em>{{ groupNavigatorItems.length }} 个分组</em>
          </header>
          <section class="contract-form-field-search" aria-label="字段快速查找">
            <label>
              <span>查找字段</span>
              <input
                :value="fieldSearchText"
                type="search"
                placeholder="搜索字段名称"
                :disabled="busy"
                @input="$emit('update:fieldSearchText', inputValue($event))"
              />
            </label>
            <div class="contract-form-field-search-summary">
              <span>匹配 {{ filteredFieldRows.length }} / {{ fieldCount }}</span>
              <button
                v-if="fieldSearchText"
                class="link-button"
                type="button"
                :disabled="busy"
                @click="$emit('update:fieldSearchText', '')"
              >
                清空
              </button>
            </div>
            <div v-if="filteredFieldRows.length" class="contract-form-field-search-results">
              <button
                v-for="item in filteredFieldRows.slice(0, 8)"
                :key="`form-field-search-${item.fieldKey}`"
                type="button"
                class="contract-form-field-search-item"
                :class="{ 'contract-form-field-search-item--active': item.fieldKey === selectedFieldKey }"
                :disabled="busy"
                @click="$emit('select-field', item.fieldKey)"
              >
                <span>{{ item.label }}</span>
                <em>{{ item.groupTitle }}</em>
              </button>
            </div>
            <p v-else class="contract-form-field-search-empty">没有匹配字段</p>
          </section>
          <section class="contract-form-field-navigator" aria-label="字段分组导航">
            <header>
              <strong>分组导航</strong>
              <span>点选分组定位画布</span>
            </header>
            <button
              v-for="item in groupNavigatorItems"
              :key="item.title"
              type="button"
              class="contract-form-field-nav-item"
              :class="{ 'contract-form-field-nav-item--active': item.active }"
              @click="$emit('select-group', item.title)"
            >
              <span>{{ item.title }}</span>
              <em>{{ item.count }}</em>
            </button>
          </section>
          <section class="contract-form-layout-tools" aria-label="表单布局配置">
            <header>
              <strong>页面布局</strong>
              <span>控制当前表单画布的整体列数。</span>
            </header>
            <label>
              <span>页面列数</span>
              <select :value="layoutColumns" :disabled="busy" @change="$emit('layout-columns-change', $event)">
                <option :value="1">1 栏</option>
                <option :value="2">2 栏</option>
                <option :value="3">3 栏</option>
              </select>
            </label>
          </section>
        </aside>
        <aside class="contract-form-inspector" aria-label="字段属性检查器">
          <section class="contract-field-selection-panel">
            <div v-if="selectedFieldRow" class="contract-field-selection-card">
              <div class="contract-field-selection-main">
                <span>已选字段</span>
                <strong>{{ selectedFieldRow.label }}</strong>
                <small>{{ selectedFieldGroupTitle }}</small>
              </div>
              <div class="contract-field-selection-tools">
                <section class="contract-field-inspector-section">
                  <header>
                    <strong>基础属性</strong>
                  </header>
                  <label class="contract-field-label-edit">
                    <span>字段显示名称</span>
                    <input
                      type="text"
                      :value="selectedFieldRow.label"
                      :disabled="busy"
                      @change="$emit('selected-field-label-change', $event)"
                      @keydown.enter.prevent="$emit('selected-field-label-change', $event)"
                    />
                  </label>
                  <div class="contract-field-governance-actions" role="radiogroup" :aria-label="`${selectedFieldRow.label}字段显示`">
                    <label
                      v-for="action in selectedFieldRow.actions"
                      :key="`${selectedFieldRow.fieldKey}-${action.key}`"
                      class="contract-field-governance-action"
                      :title="action.title"
                    >
                      <input
                        type="radio"
                        :name="`contract-field-governance-selected-${selectedFieldRow.fieldKey}`"
                        :value="action.value"
                        :checked="Boolean(action.checked)"
                        :disabled="Boolean(action.disabled)"
                        @change="$emit('selected-field-visibility-change', action.value)"
                      />
                      <span>{{ action.label }}</span>
                    </label>
                  </div>
                </section>
                <section class="contract-field-inspector-section">
                  <header>
                    <strong>布局与分组</strong>
                  </header>
                  <label class="contract-field-group-move">
                    <span>移动到分组</span>
                    <select
                      :value="selectedFieldGroupTitle"
                      :disabled="busy || groupOptions.length < 2"
                      @change="$emit('selected-field-group-move-change', $event)"
                    >
                      <option
                        v-for="groupTitle in groupOptions"
                        :key="`selected-field-group-${groupTitle}`"
                        :value="groupTitle"
                      >
                        {{ groupTitle }}
                      </option>
                    </select>
                  </label>
                  <label class="contract-field-group-rename">
                    <span>分组名称</span>
                    <input
                      :value="selectedFieldGroupTitleEdit"
                      type="text"
                      :disabled="busy || !selectedFieldGroupTitle"
                      @input="$emit('update:selectedFieldGroupTitleEdit', inputValue($event))"
                      @change="$emit('selected-group-title-change', $event)"
                      @keydown.enter.prevent="$emit('selected-group-title-change', $event)"
                    />
                  </label>
                  <div class="contract-field-group-visibility" role="radiogroup" :aria-label="`${selectedFieldGroupTitle}分组显示`">
                    <span>分组显示</span>
                    <label>
                      <input
                        type="radio"
                        :name="`contract-field-group-visible-${selectedFieldGroupTitle}`"
                        value="show"
                        :checked="selectedGroupVisible"
                        :disabled="busy || !selectedFieldGroupTitle"
                        @change="$emit('selected-group-visibility-change', 'show')"
                      />
                      <span>显示</span>
                    </label>
                    <label>
                      <input
                        type="radio"
                        :name="`contract-field-group-visible-${selectedFieldGroupTitle}`"
                        value="hide"
                        :checked="!selectedGroupVisible"
                        :disabled="busy || !selectedFieldGroupTitle"
                        @change="$emit('selected-group-visibility-change', 'hide')"
                      />
                      <span>隐藏</span>
                    </label>
                  </div>
                  <label class="contract-field-group-columns">
                    <span>分组列数</span>
                    <select
                      :value="selectedGroupColumns"
                      :disabled="busy || !selectedFieldGroupTitle"
                      @change="$emit('selected-group-columns-change', $event)"
                    >
                      <option :value="1">1 栏</option>
                      <option :value="2">2 栏</option>
                      <option :value="3">3 栏</option>
                    </select>
                  </label>
                  <label class="contract-field-size-control">
                    <span>字段尺寸</span>
                    <select
                      :value="selectedFieldSize"
                      :disabled="busy || !selectedFieldKey"
                      @change="$emit('selected-field-size-change', $event)"
                    >
                      <option value="normal">标准</option>
                      <option value="wide">加宽</option>
                      <option value="full">整行</option>
                      <option value="large">大输入框</option>
                    </select>
                  </label>
                </section>
                <section class="contract-field-inspector-section">
                  <header>
                    <strong>位置调整</strong>
                  </header>
                  <div class="contract-field-position-move">
                    <label>
                      <span>移动位置</span>
                      <select
                        :value="orderTargetKey"
                        :disabled="busy || orderTargetOptions.length === 0"
                        @change="$emit('update:orderTargetKey', inputValue($event))"
                      >
                        <option
                          v-for="option in orderTargetOptions"
                          :key="`selected-field-order-target-${option.fieldKey}`"
                          :value="option.fieldKey"
                        >
                          {{ option.label }}
                        </option>
                      </select>
                    </label>
                    <label>
                      <span>放置方式</span>
                      <select
                        :value="orderPlacement"
                        :disabled="busy || orderTargetOptions.length === 0"
                        @change="$emit('update:orderPlacement', inputValue($event) as 'before' | 'after')"
                      >
                        <option value="before">移到其前</option>
                        <option value="after">移到其后</option>
                      </select>
                    </label>
                    <button
                      class="ghost small"
                      type="button"
                      :disabled="busy || !orderTargetKey"
                      @click="$emit('move-selected-field')"
                    >
                      移动
                    </button>
                  </div>
                </section>
              </div>
            </div>
            <div v-else class="contract-field-selection-empty">
              <strong>选择字段后开始配置</strong>
              <span>在下方表单点选字段后，可在这里调整显示、隐藏、顺序和分组。</span>
            </div>
          </section>
          <section class="contract-form-operation-log" aria-label="本次操作记录">
            <header>
              <div>
                <strong>本次操作记录</strong>
                <span>{{ operatorName }}</span>
              </div>
              <button
                class="ghost small"
                type="button"
                :disabled="!operationLog.length"
                @click="$emit('clear-operation-log')"
              >
                清空记录
              </button>
            </header>
            <ol v-if="operationLog.length" class="contract-form-operation-log-list">
              <li v-for="entry in operationLog.slice(0, 8)" :key="entry.id">
                <time>{{ formatOperationTime(entry.at) }}</time>
                <strong>{{ entry.action }}</strong>
                <span
                  class="contract-form-operation-log-status"
                  :class="`contract-form-operation-log-status--${entry.status}`"
                >
                  {{ operationStatusLabel(entry.status) }}
                </span>
                <span>{{ formatOperationSummary(entry.summary) }}</span>
              </li>
            </ol>
            <p v-else class="contract-form-operation-log-empty">暂无操作记录</p>
          </section>
        </aside>
      </div>
    </section>
    <div class="contract-field-governance-footer">
      <span v-if="hasDraftChanges" class="contract-field-governance-dirty">表单设置已调整，保存后生效</span>
      <span
        v-if="auditSummary"
        class="contract-field-governance-audit"
        :class="{ 'contract-field-governance-audit--warning': auditResult?.hasConflict }"
      >{{ auditSummary }}</span>
      <button class="ghost" type="button" :disabled="busy || auditBusy" @click="$emit('audit')">
        {{ auditBusy ? '检查中...' : (auditResult ? '重新检查' : '检查效果') }}
      </button>
      <button class="chip-btn" type="button" :disabled="busy" @click="$emit('preview')">
        {{ hasDraftChanges ? '保存并预览' : '预览当前页面' }}
      </button>
      <button class="ghost" type="button" :disabled="busy || !hasDraftChanges" @click="$emit('save')">保存表单设置</button>
      <button class="ghost" type="button" :disabled="busy" @click="$emit('return-to-workbench')">返回工作台</button>
      <button class="ghost" type="button" :disabled="busy || !hasDraftChanges" @click="$emit('reset')">放弃调整</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type {
  ContractFieldGovernanceRow,
  FormConfigAuditResult,
  FormConfigOperationLogEntry,
  LowCodeFieldSize,
} from './types';

type FormFieldConfigScope = {
  summary: string;
  scope: string;
  saveTarget: string;
};

type FormDesignerGroupNavigatorItem = {
  title: string;
  count: number;
  active: boolean;
};

type FormDesignerFieldSearchRow = {
  fieldKey: string;
  label: string;
  groupTitle: string;
};

type FormDesignerOrderTargetOption = {
  fieldKey: string;
  label: string;
};

defineProps<{
  scope: FormFieldConfigScope;
  fieldCount: number;
  activeTab: string;
  busy: boolean;
  suggestedHiddenCount: number;
  fieldSearchText: string;
  filteredFieldRows: FormDesignerFieldSearchRow[];
  groupNavigatorItems: FormDesignerGroupNavigatorItem[];
  selectedFieldKey: string;
  layoutColumns: number;
  selectedFieldRow?: ContractFieldGovernanceRow;
  selectedFieldGroupTitle: string;
  groupOptions: string[];
  selectedFieldGroupTitleEdit: string;
  selectedGroupVisible: boolean;
  selectedGroupColumns: number;
  selectedFieldSize: LowCodeFieldSize;
  orderTargetKey: string;
  orderPlacement: 'before' | 'after';
  orderTargetOptions: FormDesignerOrderTargetOption[];
  operatorName: string;
  operationLog: FormConfigOperationLogEntry[];
  hasDraftChanges: boolean;
  auditSummary: string;
  auditResult?: FormConfigAuditResult | null;
  auditBusy: boolean;
  formatOperationTime: (at: string) => string;
  operationStatusLabel: (status: FormConfigOperationLogEntry['status']) => string;
  formatOperationSummary: (summary: string) => string;
}>();

defineEmits<{
  'open-custom-field-create': [];
  'hide-suggested-internal-fields': [];
  'update:fieldSearchText': [value: string];
  'select-field': [fieldKey: string];
  'select-group': [title: string];
  'layout-columns-change': [event: Event];
  'selected-field-label-change': [event: Event];
  'selected-field-visibility-change': [value: string];
  'selected-field-group-move-change': [event: Event];
  'update:selectedFieldGroupTitleEdit': [value: string];
  'selected-group-title-change': [event: Event];
  'selected-group-visibility-change': [value: 'show' | 'hide'];
  'selected-group-columns-change': [event: Event];
  'selected-field-size-change': [event: Event];
  'update:orderTargetKey': [value: string];
  'update:orderPlacement': [value: 'before' | 'after'];
  'move-selected-field': [];
  'clear-operation-log': [];
  audit: [];
  preview: [];
  save: [];
  'return-to-workbench': [];
  reset: [];
}>();

function inputValue(event: Event) {
  return String((event.target as HTMLInputElement | HTMLSelectElement).value || '');
}
</script>

<style src="./CurrentFormFieldSettingsPanel.css"></style>
