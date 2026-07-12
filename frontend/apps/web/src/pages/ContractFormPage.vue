/* eslint-disable @typescript-eslint/no-unused-vars, no-extra-boolean-cast, vue/attributes-order */
<template>
  <LayoutShell
    :flow="isProjectIntakeCreateMode"
    :class="['sc-page', { 'contract-form-native-shell': useNativeFormTree }]"
    data-product-page-mode="form"
    :data-v2-shadow-store="String(v2ShadowStoreReady)"
    :data-v2-shadow-widgets="String(v2ShadowWidgetCount)"
    :data-v2-shadow-actions="String(v2ShadowActionCount)"
    :data-v2-shadow-button-statuses="String(v2ShadowButtonStatusCount)"
    :data-v2-shadow-field-codes="String(v2ShadowFieldCodeCount)"
    :data-v2-shadow-field-overlap="String(v2ShadowLegacyFieldOverlapCount)"
    :data-v2-shadow-field-missing="v2ShadowLegacyFieldMissingPreview"
    :data-v2-shadow-layout-source="v2ShadowLayoutSourceKind"
    :data-v2-shadow-global-source="v2ShadowGlobalSourceKind"
    :data-v2-shadow-source-context="v2ShadowSourceContextKind"
    :data-v2-shadow-status-fields="String(v2ShadowStatusFieldCount)"
    :data-v2-shadow-value-fields="String(v2ShadowValueFieldCount)"
    :data-v2-shadow-main-data-fields="String(v2ShadowMainDataFieldCount)"
    :data-v2-shadow-readonly-values="String(v2ShadowReadonlyValueCount)"
    :data-v2-shadow-value-source="v2ShadowValueSourceKind"
    :data-v2-shadow-error="v2ContractDecodeError || '-'"
  >
    <PageHeaderTemplate
      :title="pageDisplayTitle"
      :subtitle="pageDisplaySubtitle || undefined"
      :hide-title="suppressPageHeaderTitle"
    >
      <template #meta>
        <p v-if="showHud" class="meta">model={{ model }} · id={{ recordIdDisplay }} · action={{ actionId || '-' }}</p>
        <p v-if="showHud && contractMetaLine" class="meta">{{ contractMetaLine }}</p>
      </template>
      <template #status>
        <template v-if="isProjectIntakeCreateMode">
          <p class="header-status-item">当前进度：{{ intakeRequiredSummary }}</p>
          <p class="header-status-item" :class="{ 'header-status-item--danger': intakeMissingSummary !== '无' }">缺少：{{ intakeMissingSummary }}</p>
        </template>
        <section v-else-if="nativeStatusbar.visible" class="native-statusbar native-statusbar--header" aria-label="项目状态">
          <button
            v-for="item in nativeStatusbar.states"
            :key="String(item.value)"
            type="button"
            class="native-statusbar-step"
            :class="{
              'native-statusbar-step--active': nativeStatusbar.current === String(item.value),
              'native-statusbar-step--done': nativeStatusbar.reachedValues.includes(String(item.value)),
            }"
            :disabled="busy || nativeStatusbar.readonly"
            @click="setStatusbarValue(String(item.value))"
          >
            {{ item.label }}
          </button>
        </section>
      </template>
      <template #actions>
        <span class="contract-header-action-label">办理操作</span>
        <button
          v-if="showReturnToBusinessConfigAction"
          class="sc-btn sc-btn-ghost sc-btn-sm"
          :disabled="busy"
          @click="returnToBusinessConfigDesigner"
        >
          返回工作台
        </button>
        <button
          v-if="showDraftSaveAction"
          class="sc-btn sc-btn-ghost sc-btn-sm"
          :disabled="draftSaveDisabled"
          @click="() => saveRecord()"
        >
          {{ draftSaveButtonLabel }}
        </button>
        <button
          v-if="showPrimaryBusinessFormAction"
          class="sc-btn sc-btn-primary sc-btn-sm"
          :disabled="primaryFormActionDisabled"
          @click="runPrimaryFormAction"
        >
          {{ submitButtonLabel }}
        </button>
        <button
          v-for="action in headerBusinessActionsVisible"
          :key="`hdr-${action.key}`"
          :class="headerActionButtonClass(action)"
          :disabled="busy || !action.enabled"
          :title="action.hint"
          @click="runAction(action)"
        >
          {{ action.label }}
        </button>
        <span v-if="headerConfigActionsVisible.length" class="contract-header-action-separator" aria-hidden="true" />
        <button
          v-for="action in headerConfigActionsVisible"
          :key="`hdr-config-${action.key}`"
          class="sc-btn sc-btn-ghost sc-btn-sm contract-header-config-action"
          :disabled="busy || !action.enabled"
          :title="action.hint"
          @click="runAction(action)"
        >
          {{ action.label }}
        </button>
        <button v-if="showDiscardAction" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy" @click="discardChanges">{{ formUiLabel('discard') }}</button>
        <button v-if="showDebugActionsVisible && !isProjectIntakeCreateMode" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy || !contract" @click="copyContractJson">复制配置</button>
        <button v-if="showDebugActionsVisible && !isProjectIntakeCreateMode" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy || !contract" @click="exportContractJson">导出配置</button>
        <button v-if="showDebugActionsVisible && !isProjectIntakeCreateMode" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy" @click="reload">{{ formUiLabel('reload') }}</button>
      </template>
    </PageHeaderTemplate>

    <StatusPanel v-if="renderErrorMessage" title="页面打开失败" :message="renderErrorMessage" variant="error" :on-retry="reload" />
    <StatusPanel v-else-if="status === 'loading'" title="正在加载页面..." variant="info" />
    <StatusPanel v-else-if="status === 'error'" title="页面加载失败" :message="errorMessage" variant="error" :on-retry="reload" />

    <section v-else :class="['card', 'sc-panel', 'sc-product-main-surface', { 'card--flow': isProjectIntakeCreateMode }]">
      <section v-if="warnings.length && !isProjectIntakeCreateMode" class="block warn">
        <h3>提示信息</h3>
        <ul>
          <li v-for="item in warnings" :key="item">{{ item }}</li>
        </ul>
      </section>
      <section v-if="workflowEvidenceGateRows.length && !isProjectIntakeCreateMode" class="block workflow-evidence-block">
        <h3>办理前置条件</h3>
        <ul class="workflow-evidence-list">
          <li
            v-for="item in workflowEvidenceGateRows"
            :key="item.reasonCode"
            :class="{ 'workflow-evidence-list__item--block': item.blocking }"
          >
            {{ item.message }}
          </li>
        </ul>
      </section>
      <section v-if="strictContractMissingSummary && !isProjectIntakeCreateMode" class="block contract-missing-block">
        <h3>配置状态提示</h3>
        <p class="contract-missing-summary">{{ strictContractMissingSummary }}</p>
        <p v-if="strictContractDefaultsSummary" class="contract-missing-defaults">{{ strictContractDefaultsSummary }}</p>
      </section>

      <section v-if="workflowTransitions.length && !isProjectIntakeCreateMode && !useNativeFormTree" class="block">
        <h3>流程操作</h3>
        <div class="chips">
          <button
            v-for="item in workflowTransitions"
            :key="item.key"
            class="chip-btn"
            :disabled="busy || !item.action"
            :title="item.notes || ''"
            @click="item.action && runAction(item.action)"
          >
            {{ item.label }}
          </button>
        </div>
      </section>

      <section v-if="showSearchFilters && searchFilters.length && !isProjectIntakeCreateMode" class="block">
        <h3>快捷筛选</h3>
        <div class="chips">
          <button
            v-for="item in searchFilters"
            :key="`flt-${item.key}`"
            class="chip-btn"
            :class="{ active: activeFilterKey === item.key }"
            :disabled="busy || !item.key"
            @click="openFilter(item.key)"
          >
            {{ item.label }}
          </button>
        </div>
      </section>

      <section class="form-grid" :class="{ 'form-grid--designer-workspace': showCurrentFormFieldConfigScope }">
        <StatusPanel
          v-if="sceneValidationPanel"
          title="表单校验失败"
          :message="sceneValidationPanel.message"
          :error-code="sceneValidationPanel.code"
          :reason-code="sceneValidationPanel.code"
          :hint="sceneValidationPanel.hint"
          :suggested-action="sceneValidationPanel.suggestedAction"
          variant="error"
        />
        <p v-if="nonSceneValidationErrors.length" class="validation-error">
          {{ nonSceneValidationErrors.join('；') }}
        </p>
        <p v-if="onchangeWarnings.length" class="validation-warn">
          {{ onchangeWarnings.map((item) => item.message || item.title || '').filter(Boolean).join('；') }}
        </p>
        <p v-if="submissionFeedback" class="submission-feedback" :class="`submission-feedback--${submissionFeedback.kind}`">
          {{ submissionFeedback.message }}
        </p>
        <SceneBlocksRenderer
          v-if="showSceneBlocksDebug && sceneReadyFormSurface.sceneBlocks.length"
          :blocks="sceneReadyFormSurface.sceneBlocks"
          @action="handleSceneBlockAction"
        />
        <section v-if="showCurrentFormFieldConfigScope" class="contract-form-settings">
          <header class="contract-form-settings-head">
            <div>
              <h4>当前页面字段配置</h4>
              <p>{{ formFieldConfigScope.summary }}</p>
            </div>
            <span class="contract-form-settings-field-count">字段 {{ currentFormDesignFieldCount }}</span>
          </header>
          <div class="contract-form-design-strip" aria-label="页面设计步骤">
            <div>
              <span>当前页面</span>
              <strong>{{ formFieldConfigScope.scope }}</strong>
            </div>
            <div>
              <span>可配置项</span>
              <strong>字段名称、顺序、显示隐藏、新增字段</strong>
            </div>
            <div>
              <span>影响范围</span>
              <strong>{{ formFieldConfigScope.saveTarget }}</strong>
            </div>
          </div>
          <section v-if="formSettingsActiveTab === 'fields'" class="contract-form-settings-fields">
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
                  @click="openCentralCustomFieldCreate"
                >
                  新增字段
                </button>
                <button
                  v-if="suggestedHiddenFieldRows.length"
                  class="ghost small"
                  type="button"
                  :disabled="busy"
                  @click="hideSuggestedInternalFields"
                >
                  隐藏系统字段 {{ suggestedHiddenFieldRows.length }}
                </button>
              </div>
            </header>
            <div class="contract-form-designer-control-grid">
              <aside class="contract-form-designer-sidebar" aria-label="表单设计器导航">
                <header class="contract-form-designer-sidebar-head">
                  <div>
                    <span>字段目录</span>
                    <strong>{{ currentFormDesignFieldCount }} 个字段</strong>
                  </div>
                  <em>{{ formDesignerGroupNavigatorItems.length }} 个分组</em>
                </header>
                <section class="contract-form-field-search" aria-label="字段快速查找">
                  <label>
                    <span>查找字段</span>
                    <input
                      v-model="formDesignerFieldSearchText"
                      type="search"
                      placeholder="搜索字段名称"
                      :disabled="busy"
                    />
                  </label>
                  <div class="contract-form-field-search-summary">
                    <span>匹配 {{ formDesignerFilteredFieldRows.length }} / {{ currentFormDesignFieldCount }}</span>
                    <button
                      v-if="formDesignerFieldSearchText"
                      class="link-button"
                      type="button"
                      :disabled="busy"
                      @click="formDesignerFieldSearchText = ''"
                    >
                      清空
                    </button>
                  </div>
                  <div v-if="formDesignerFilteredFieldRows.length" class="contract-form-field-search-results">
                    <button
                      v-for="item in formDesignerFilteredFieldRows.slice(0, 8)"
                      :key="`form-field-search-${item.fieldKey}`"
                      type="button"
                      class="contract-form-field-search-item"
                      :class="{ 'contract-form-field-search-item--active': item.fieldKey === selectedFormSettingsFieldKey }"
                      :disabled="busy"
                      @click="selectFormDesignerField(item.fieldKey)"
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
                    v-for="item in formDesignerGroupNavigatorItems"
                    :key="item.title"
                    type="button"
                    class="contract-form-field-nav-item"
                    :class="{ 'contract-form-field-nav-item--active': item.active }"
                    @click="selectFormDesignerGroup(item.title)"
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
                    <select :value="formLayoutColumnsDraft" :disabled="busy" @change="onFormLayoutColumnsChange">
                      <option :value="1">1 栏</option>
                      <option :value="2">2 栏</option>
                      <option :value="3">3 栏</option>
                    </select>
                  </label>
                </section>
              </aside>
              <aside class="contract-form-inspector" aria-label="字段属性检查器">
                <section class="contract-field-selection-panel">
                  <div v-if="selectedFormSettingsFieldRow" class="contract-field-selection-card">
                    <div class="contract-field-selection-main">
                      <span>已选字段</span>
                      <strong>{{ selectedFormSettingsFieldRow.label }}</strong>
                      <small>{{ selectedFormSettingsFieldGroupTitle }}</small>
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
                            :value="selectedFormSettingsFieldRow.label"
                            :disabled="busy"
                            @change="onSelectedFormSettingsFieldLabelChange"
                            @keydown.enter.prevent="onSelectedFormSettingsFieldLabelChange"
                          />
                        </label>
                        <div class="contract-field-governance-actions" role="radiogroup" :aria-label="`${selectedFormSettingsFieldRow.label}字段显示`">
                          <label
                            v-for="action in selectedFormSettingsFieldRow.actions"
                            :key="`${selectedFormSettingsFieldRow.fieldKey}-${action.key}`"
                            class="contract-field-governance-action"
                            :title="action.title"
                          >
                            <input
                              type="radio"
                              :name="`contract-field-governance-selected-${selectedFormSettingsFieldRow.fieldKey}`"
                              :value="action.value"
                              :checked="Boolean(action.checked)"
                              :disabled="Boolean(action.disabled)"
                              @change="onSelectedFormSettingsFieldVisibilityChange(action.value)"
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
                            :value="selectedFormSettingsFieldGroupTitle"
                            :disabled="busy || currentFormGroupOptions.length < 2"
                            @change="onSelectedFormSettingsFieldGroupMoveChange"
                          >
                            <option
                              v-for="groupTitle in currentFormGroupOptions"
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
                            v-model="selectedFormSettingsFieldGroupTitleEdit"
                            type="text"
                            :disabled="busy || !selectedFormSettingsFieldGroupTitle"
                            @change="onSelectedFormSettingsGroupTitleChange"
                            @keydown.enter.prevent="onSelectedFormSettingsGroupTitleChange"
                          />
                        </label>
                        <div class="contract-field-group-visibility" role="radiogroup" :aria-label="`${selectedFormSettingsFieldGroupTitle}分组显示`">
                          <span>分组显示</span>
                          <label>
                            <input
                              type="radio"
                              :name="`contract-field-group-visible-${selectedFormSettingsFieldGroupTitle}`"
                              value="show"
                              :checked="selectedFormSettingsGroupVisible"
                              :disabled="busy || !selectedFormSettingsFieldGroupTitle"
                              @change="onSelectedFormSettingsGroupVisibilityChange('show')"
                            />
                            <span>显示</span>
                          </label>
                          <label>
                            <input
                              type="radio"
                              :name="`contract-field-group-visible-${selectedFormSettingsFieldGroupTitle}`"
                              value="hide"
                              :checked="!selectedFormSettingsGroupVisible"
                              :disabled="busy || !selectedFormSettingsFieldGroupTitle"
                              @change="onSelectedFormSettingsGroupVisibilityChange('hide')"
                            />
                            <span>隐藏</span>
                          </label>
                        </div>
                        <label class="contract-field-group-columns">
                          <span>分组列数</span>
                          <select
                            :value="selectedFormSettingsGroupColumns"
                            :disabled="busy || !selectedFormSettingsFieldGroupTitle"
                            @change="onSelectedFormSettingsGroupColumnsChange"
                          >
                            <option :value="1">1 栏</option>
                            <option :value="2">2 栏</option>
                            <option :value="3">3 栏</option>
                          </select>
                        </label>
                        <label class="contract-field-size-control">
                          <span>字段尺寸</span>
                          <select
                            :value="selectedFormSettingsFieldSize"
                            :disabled="busy || !selectedFormSettingsFieldKey"
                            @change="onSelectedFormSettingsFieldSizeChange"
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
                              v-model="selectedFormSettingsOrderTargetKey"
                              :disabled="busy || selectedFormSettingsOrderTargetOptions.length === 0"
                            >
                              <option
                                v-for="option in selectedFormSettingsOrderTargetOptions"
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
                              v-model="selectedFormSettingsOrderPlacement"
                              :disabled="busy || selectedFormSettingsOrderTargetOptions.length === 0"
                            >
                              <option value="before">移到其前</option>
                              <option value="after">移到其后</option>
                            </select>
                          </label>
                          <button
                            class="ghost small"
                            type="button"
                            :disabled="busy || !selectedFormSettingsOrderTargetKey"
                            @click="moveSelectedFormSettingsFieldToOrderTarget"
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
                      <span>{{ formConfigOperatorName }}</span>
                    </div>
                    <button
                      class="ghost small"
                      type="button"
                      :disabled="!formConfigOperationLog.length"
                      @click="clearFormConfigOperationLog"
                    >
                      清空记录
                    </button>
                  </header>
                  <ol v-if="formConfigOperationLog.length" class="contract-form-operation-log-list">
                    <li v-for="entry in formConfigOperationLog.slice(0, 8)" :key="entry.id">
                      <time>{{ formatFormConfigOperationTime(entry.at) }}</time>
                      <strong>{{ entry.action }}</strong>
                      <span
                        class="contract-form-operation-log-status"
                        :class="`contract-form-operation-log-status--${entry.status}`"
                      >
                        {{ formConfigOperationStatusLabel(entry.status) }}
                      </span>
                      <span>{{ formatFormConfigOperationSummary(entry.summary) }}</span>
                    </li>
                  </ol>
                  <p v-else class="contract-form-operation-log-empty">暂无操作记录</p>
                </section>
              </aside>
            </div>
          </section>
          <div class="contract-field-governance-footer">
            <span v-if="hasCurrentFormFieldDraftChanges" class="contract-field-governance-dirty">表单设置已调整，保存后生效</span>
            <span
              v-if="formConfigAuditSummary"
              class="contract-field-governance-audit"
              :class="{ 'contract-field-governance-audit--warning': formConfigAuditResult?.hasConflict }"
            >{{ formConfigAuditSummary }}</span>
            <button class="ghost" type="button" :disabled="busy || formConfigAuditBusy" @click="auditCurrentFormConfiguration">
              {{ formConfigAuditBusy ? '检查中...' : (formConfigAuditResult ? '重新检查' : '检查效果') }}
            </button>
            <button class="chip-btn" type="button" :disabled="busy" @click="previewCurrentFormConfiguration">
              {{ hasCurrentFormFieldDraftChanges ? '保存并预览' : '预览当前页面' }}
            </button>
            <button class="ghost" type="button" :disabled="busy || !hasCurrentFormFieldDraftChanges" @click="saveContractFieldOrder">保存表单设置</button>
            <button class="ghost" type="button" :disabled="busy" @click="returnToBusinessConfigDesigner">返回工作台</button>
            <button class="ghost" type="button" :disabled="busy || !hasCurrentFormFieldDraftChanges" @click="resetContractFieldOrder">放弃调整</button>
          </div>
        </section>
        <section v-if="showNativeDefaultSectionTitle" class="native-default-section-head">
          <h3>基本信息</h3>
        </section>
        <section
          v-if="useNativeFormTree"
          class="contract-form-canvas-shell"
          :class="{ 'contract-form-designer-canvas': showCurrentFormFieldConfigScope }"
          aria-label="表单配置画布"
        >
          <header v-if="showCurrentFormFieldConfigScope" class="contract-form-canvas-head">
            <div>
              <strong>表单画布</strong>
              <span>{{ selectedFormSettingsFieldRow ? `正在编辑：${selectedFormSettingsFieldRow.label}` : '点选字段后在右侧调整属性' }}</span>
            </div>
            <em>{{ nativeFormRootColumns }} 栏布局</em>
          </header>
          <NativeFormTreeRenderer
            :key="nativeLayoutVisibilityRevision"
            class="contract-form-canvas-body"
            :nodes="nativeFormLayoutNodes"
            :field-schemas-for-nodes="nativeFieldSchemasForNodes"
            :is-node-visible="isNativeLayoutNodeVisible"
            :button-label-resolver="resolveNativeButtonLabel"
            :native-action-handler="runNativeLayoutAction"
            :native-action-state-resolver="resolveNativeActionState"
            :relation-adapter="relationFieldAdapter"
            :field-actions="isContractFieldOrderEditable ? formSettingsFieldActions : contractFieldActions"
            :field-order-editable="isContractFieldOrderEditable"
            :field-order-index="contractInlineFieldOrderIndex"
            :field-order-count="fieldOrderDraft.length"
            :field-order-dragging-key="draggingFieldKey"
            :field-order-drop-target-key="dropTargetFieldKey"
            :field-order-drop-placement="dropTargetPlacement"
            :field-config-editable="isContractFieldOrderEditable"
            :field-selection-mode="isContractFieldOrderEditable"
            :selected-field-key="selectedFormSettingsFieldKey"
            :columns="nativeFormRootColumns"
            @field-change="onTemplateFieldChange"
            @field-action="onContractFieldAction"
            @field-order-move="onContractInlineFieldOrderMove"
            @field-order-drag-start="onContractInlineFieldOrderDragStart"
            @field-order-drag-over="onContractInlineFieldOrderDragOver"
            @field-order-drag-leave="onContractInlineFieldOrderDragLeave"
            @field-order-drop="onContractInlineFieldOrderDrop"
            @field-order-group-drop="onContractInlineFieldOrderGroupDrop"
            @field-order-drag-end="onContractInlineFieldOrderDragEnd"
            @field-label-change="onContractInlineFieldLabelChange"
            @field-add-after="onContractInlineFieldAddAfter"
            @field-select="onFormSettingsFieldSelect"
            @group-rename="onContractInlineGroupRename"
            @group-add-field="onContractInlineGroupAddField"
            @native-action="runNativeLayoutAction"
          >
            <template #readonly="{ field }">
              <span class="contract-readonly-value">
                <FieldValue :value="field.value" :field="field.descriptor" />
              </span>
            </template>
            <template #chatter>
              <section v-if="(nativeChatterActions.length || nativeAttachments) && !isProjectIntakeCreateMode" class="block native-chatter-block">
              <h3>{{ nativeCollaborationTitle }}</h3>
              <p v-if="nativeCollaborationUnavailableMessage" class="native-chatter-empty">{{ nativeCollaborationUnavailableMessage }}</p>
              <div v-else class="chips">
                <button
                  v-for="action in nativeChatterActions"
                  :key="`chatter-${action.key}`"
                  class="chip-btn"
                  type="button"
                  :disabled="busy || chatterPosting || !action.enabled"
                  :title="action.hint"
                  @click="openNativeChatterAction(action)"
                >
                  {{ action.label }}
                </button>
              </div>
              <section v-if="!nativeCollaborationUnavailableMessage && activeChatterMode" class="native-chatter-compose">
                <template v-if="activeChatterIsActivity">
                  <label class="native-chatter-field">
                    <span>{{ activityAssigneeLabel }}</span>
                    <select class="input" :value="activityAssigneeId || ''" :disabled="chatterPosting || collaborationUsersLoading" @change="selectActivityAssignee">
                      <option value="">当前用户</option>
                      <option v-for="user in activityAssigneeOptions" :key="`activity-user-${user.id}`" :value="user.id">
                        {{ collaborationUserLabel(user) }}
                      </option>
                    </select>
                  </label>
                  <label class="native-chatter-field">
                    <span>{{ activitySummaryLabel }}</span>
                    <input
                      v-model="activitySummary"
                      class="input"
                      type="text"
                      :placeholder="activitySummaryPlaceholder"
                      :disabled="chatterPosting"
                    />
                  </label>
                  <label class="native-chatter-field">
                    <span>{{ activityDeadlineLabel }}</span>
                    <input v-model="activityDeadline" class="input" type="date" :disabled="chatterPosting" />
                  </label>
                  <label class="native-chatter-field">
                    <span>{{ activityNoteLabel }}</span>
                    <textarea
                      v-model="activityNote"
                      class="native-chatter-input"
                      :placeholder="activityNotePlaceholder"
                      :disabled="chatterPosting"
                    />
                  </label>
                </template>
                <template v-else>
                  <label class="native-chatter-field">
                    <span>提醒对象</span>
                    <input
                      v-model="collaborationUserQuery"
                      class="input"
                      type="text"
                      :disabled="chatterPosting || collaborationUsersLoading"
                      placeholder="搜索姓名或账号"
                      @input="() => loadCollaborationUsers(collaborationUserQuery)"
                    />
                  </label>
                  <div v-if="selectedMentionUsers.length" class="native-collab-selected">
                    <button
                      v-for="user in selectedMentionUsers"
                      :key="`mention-selected-${user.id}`"
                      class="chip-btn"
                      type="button"
                      :disabled="chatterPosting"
                      @click="removeMentionUser(user.id)"
                    >
                      @{{ collaborationUserLabel(user) }} ×
                    </button>
                  </div>
                  <div v-if="collaborationUserChoices.length" class="native-collab-options">
                    <button
                      v-for="user in collaborationUserChoices.slice(0, 6)"
                      :key="`mention-choice-${user.id}`"
                      class="ghost mini"
                      type="button"
                      :disabled="chatterPosting"
                      @click="selectMentionUser(user)"
                    >
                      @{{ collaborationUserLabel(user) }}
                    </button>
                  </div>
                  <textarea
                    v-model="chatterDraft"
                    class="native-chatter-input"
                    :placeholder="activeChatterPlaceholder"
                    :disabled="chatterPosting"
                  />
                </template>
                <div class="native-chatter-compose-actions">
                  <button class="primary" type="button" :disabled="isNativeChatterSubmitDisabled" @click="sendNativeChatter">
                    {{ chatterPosting ? activeChatterPostingLabel : activeChatterSubmitLabel }}
                  </button>
                  <button class="ghost" type="button" :disabled="chatterPosting" @click="closeNativeChatterComposer">取消</button>
                </div>
              </section>
              <p v-if="chatterError" class="validation-error native-chatter-message">{{ chatterError }}</p>
              <section v-if="nativeAttachments" class="native-attachment-tools">
                <label class="chip-btn native-attachment-upload">
                  {{ attachmentUploading ? nativeAttachmentUploadingLabel : nativeAttachmentUploadLabel }}
                  <input type="file" :disabled="attachmentUploading" @change="onNativeAttachmentSelected" />
                </label>
                <p v-if="attachmentError" class="validation-error native-chatter-message">{{ attachmentError }}</p>
              </section>
              <ul v-if="pendingNativeAttachments.length" class="native-pending-attachments">
                <li v-for="item in pendingNativeAttachments" :key="item.key">
                  <span>{{ item.name }}</span>
                  <button class="ghost native-attachment-download" type="button" :disabled="attachmentUploading" @click="removePendingNativeAttachment(item.key)">移除</button>
                </li>
              </ul>
              <ul v-if="!nativeCollaborationUnavailableMessage && chatterTimeline.length" class="native-chatter-timeline">
                <li v-for="entry in chatterTimeline" :key="entry.key" class="native-chatter-entry">
                  <span class="native-chatter-type">{{ entry.typeLabel }}</span>
                  <span class="native-chatter-body">{{ entry.type === 'activity' ? entry.title : (entry.body || entry.title) }}</span>
                  <span class="native-chatter-meta">{{ entry.meta }}</span>
                  <div v-if="entry.type === 'activity'" class="native-chatter-entry-actions">
                    <button
                      v-if="entry.activity?.can_complete"
                      class="ghost native-chatter-entry-action"
                      type="button"
                      :disabled="isActivityUpdating(entry)"
                      @click="updateNativeActivity(entry, 'done')"
                    >
                      完成
                    </button>
                    <button
                      v-if="entry.activity?.can_cancel"
                      class="ghost native-chatter-entry-action"
                      type="button"
                      :disabled="isActivityUpdating(entry)"
                      @click="updateNativeActivity(entry, 'cancel')"
                    >
                      取消
                    </button>
                  </div>
                  <button
                    v-if="entry.type === 'attachment' && entry.attachment"
                    class="ghost native-attachment-download"
                    type="button"
                    @click="openNativeAttachment(entry.attachment)"
                  >
                    {{ nativeAttachmentViewLabel }}
                  </button>
                </li>
              </ul>
            </section>
            </template>
          </NativeFormTreeRenderer>
        </section>
        <section v-if="activeContractModeActions.length" class="contract-mode-actions">
          <button
            v-for="action in activeContractModeActions"
            :key="`mode-${action.key}`"
            type="button"
            class="chip-btn"
            :disabled="busy"
            @click="openContractModeAction(action.raw)"
          >
            {{ action.label }}
          </button>
          <p v-if="contractModeFeedback" class="contract-mode-feedback">{{ contractModeFeedback }}</p>
        </section>
        <form
          v-if="contractPromptRule"
          class="contract-mode-prompt"
          @submit.prevent="submitContractPromptAction"
        >
          <label
            v-for="field in contractPromptFields"
            :key="`contract-prompt-${field.name}`"
            class="contract-mode-prompt-field"
          >
            <span>{{ field.label }}</span>
            <select
              v-if="field.options.length"
              v-model="contractPromptValues[field.name]"
              :required="field.required"
              :disabled="busy"
            >
              <option value=""></option>
              <option v-for="option in field.options" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
            <input
              v-else
              v-model="contractPromptValues[field.name]"
              :required="field.required"
              :disabled="busy"
            />
          </label>
          <button type="submit" class="chip-btn" :disabled="busy">确定</button>
          <button type="button" class="ghost" :disabled="busy" @click="closeContractPromptAction">取消</button>
        </form>
        <div
          v-if="lowCodeFieldCreateDialog.open"
          class="contract-field-create-backdrop"
          role="presentation"
          @click.self="closeInlineCustomFieldCreate"
          @keydown.esc="closeInlineCustomFieldCreate"
        >
          <form
            class="contract-field-create-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="contract-field-create-title"
            @submit.prevent="submitInlineCustomFieldCreate"
          >
            <header class="contract-field-create-head">
              <h3 id="contract-field-create-title">新增字段</h3>
              <button type="button" class="contract-field-create-close" :disabled="busy" aria-label="取消新增字段" @click="closeInlineCustomFieldCreate">x</button>
            </header>
            <label class="contract-mode-prompt-field">
              <span>字段标题</span>
              <input ref="lowCodeFieldCreateLabelRef" v-model="lowCodeFieldCreateDialog.label" required :disabled="busy" />
            </label>
            <label class="contract-mode-prompt-field">
              <span>字段类型</span>
              <select v-model="lowCodeFieldCreateDialog.ttype" required :disabled="busy">
                <option value="char">单行文本</option>
                <option value="text">多行文本</option>
                <option value="integer">整数</option>
                <option value="float">小数</option>
                <option value="boolean">是/否</option>
                <option value="date">日期</option>
                <option value="datetime">日期时间</option>
                <option value="html">富文本</option>
              </select>
            </label>
            <footer class="contract-field-create-actions">
              <button type="submit" class="chip-btn" :disabled="busy">创建字段</button>
              <button type="button" class="ghost" :disabled="busy" @click="closeInlineCustomFieldCreate">取消</button>
            </footer>
          </form>
        </div>
        <ul v-if="lowCodePrecheckWarnings.length" class="contract-lowcode-warnings">
          <li v-for="(warning, index) in lowCodePrecheckWarnings" :key="`lowcode-warning-${index}`">{{ warning }}</li>
        </ul>
        <div v-if="hasAdvancedFields && !isProjectIntakeCreateMode && !useNativeFormTree" class="layout-divider advanced-toggle">
          <button class="chip-btn" :disabled="busy" @click="advancedExpanded = !advancedExpanded">
            {{ advancedExpanded ? '收起高级信息' : '展开高级信息' }}
          </button>
        </div>

      </section>

      <PageFooterTemplate v-if="isProjectIntakeCreateMode" hint="填写完成后点击“创建项目”">
        <template #default>
          <button class="ghost" :disabled="busy" @click="cancelIntake">取消</button>
          <button class="primary" :disabled="isIntakeCreateDisabled" @click="() => saveRecord()">
            {{ intakeCreateButtonLabel }}
          </button>
        </template>
      </PageFooterTemplate>

      <section v-if="bodyActions.length && !isProjectIntakeCreateMode && !useNativeFormTree" class="block">
        <h3>可执行操作</h3>
        <div class="chips">
          <button
            v-for="action in bodyActions"
            :key="`body-${action.key}`"
            class="chip-btn"
            :disabled="busy || !action.enabled"
            :title="action.hint"
            @click="runAction(action)"
          >
            {{ action.label }}<template v-if="showHud"> · {{ action.kind }}</template>
          </button>
        </div>
      </section>

      <section v-if="(nativeChatterActions.length || nativeAttachments) && !isProjectIntakeCreateMode && !hasNativeChatterNode" class="block native-chatter-block">
        <h3>{{ nativeCollaborationTitle }}</h3>
        <p v-if="nativeCollaborationUnavailableMessage" class="native-chatter-empty">{{ nativeCollaborationUnavailableMessage }}</p>
        <div v-else class="chips">
          <button
            v-for="action in nativeChatterActions"
            :key="`chatter-${action.key}`"
            class="chip-btn"
            type="button"
            :disabled="busy || chatterPosting || !action.enabled"
            :title="action.hint"
            @click="openNativeChatterAction(action)"
          >
            {{ action.label }}
          </button>
        </div>
        <section v-if="!nativeCollaborationUnavailableMessage && activeChatterMode" class="native-chatter-compose">
          <template v-if="activeChatterIsActivity">
            <label class="native-chatter-field">
              <span>{{ activityAssigneeLabel }}</span>
              <select class="input" :value="activityAssigneeId || ''" :disabled="chatterPosting || collaborationUsersLoading" @change="selectActivityAssignee">
                <option value="">当前用户</option>
                <option v-for="user in activityAssigneeOptions" :key="`activity-user-fallback-${user.id}`" :value="user.id">
                  {{ collaborationUserLabel(user) }}
                </option>
              </select>
            </label>
            <label class="native-chatter-field">
              <span>{{ activitySummaryLabel }}</span>
              <input
                v-model="activitySummary"
                class="input"
                type="text"
                :placeholder="activitySummaryPlaceholder"
                :disabled="chatterPosting"
              />
            </label>
            <label class="native-chatter-field">
              <span>{{ activityDeadlineLabel }}</span>
              <input v-model="activityDeadline" class="input" type="date" :disabled="chatterPosting" />
            </label>
            <label class="native-chatter-field">
              <span>{{ activityNoteLabel }}</span>
              <textarea
                v-model="activityNote"
                class="native-chatter-input"
                :placeholder="activityNotePlaceholder"
                :disabled="chatterPosting"
              />
            </label>
          </template>
          <template v-else>
            <label class="native-chatter-field">
              <span>提醒对象</span>
              <input
                v-model="collaborationUserQuery"
                class="input"
                type="text"
                :disabled="chatterPosting || collaborationUsersLoading"
                placeholder="搜索姓名或账号"
                @input="() => loadCollaborationUsers(collaborationUserQuery)"
              />
            </label>
            <div v-if="selectedMentionUsers.length" class="native-collab-selected">
              <button
                v-for="user in selectedMentionUsers"
                :key="`mention-selected-fallback-${user.id}`"
                class="chip-btn"
                type="button"
                :disabled="chatterPosting"
                @click="removeMentionUser(user.id)"
              >
                @{{ collaborationUserLabel(user) }} ×
              </button>
            </div>
            <div v-if="collaborationUserChoices.length" class="native-collab-options">
              <button
                v-for="user in collaborationUserChoices.slice(0, 6)"
                :key="`mention-choice-fallback-${user.id}`"
                class="ghost mini"
                type="button"
                :disabled="chatterPosting"
                @click="selectMentionUser(user)"
              >
                @{{ collaborationUserLabel(user) }}
              </button>
            </div>
            <textarea
              v-model="chatterDraft"
              class="native-chatter-input"
              :placeholder="activeChatterPlaceholder"
              :disabled="chatterPosting"
            />
          </template>
          <div class="native-chatter-compose-actions">
            <button class="primary" type="button" :disabled="isNativeChatterSubmitDisabled" @click="sendNativeChatter">
              {{ chatterPosting ? activeChatterPostingLabel : activeChatterSubmitLabel }}
            </button>
            <button class="ghost" type="button" :disabled="chatterPosting" @click="closeNativeChatterComposer">取消</button>
          </div>
        </section>
        <p v-if="chatterError" class="validation-error native-chatter-message">{{ chatterError }}</p>
        <section v-if="nativeAttachments" class="native-attachment-tools">
          <label class="chip-btn native-attachment-upload">
            {{ attachmentUploading ? nativeAttachmentUploadingLabel : nativeAttachmentUploadLabel }}
            <input type="file" :disabled="attachmentUploading" @change="onNativeAttachmentSelected" />
          </label>
          <p v-if="attachmentError" class="validation-error native-chatter-message">{{ attachmentError }}</p>
        </section>
        <ul v-if="pendingNativeAttachments.length" class="native-pending-attachments">
          <li v-for="item in pendingNativeAttachments" :key="item.key">
            <span>{{ item.name }}</span>
            <button class="ghost native-attachment-download" type="button" :disabled="attachmentUploading" @click="removePendingNativeAttachment(item.key)">移除</button>
          </li>
        </ul>
        <ul v-if="!nativeCollaborationUnavailableMessage && chatterTimeline.length" class="native-chatter-timeline">
          <li v-for="entry in chatterTimeline" :key="entry.key" class="native-chatter-entry">
            <span class="native-chatter-type">{{ entry.typeLabel }}</span>
            <span class="native-chatter-body">{{ entry.type === 'activity' ? entry.title : (entry.body || entry.title) }}</span>
            <span class="native-chatter-meta">{{ entry.meta }}</span>
            <div v-if="entry.type === 'activity'" class="native-chatter-entry-actions">
              <button
                v-if="entry.activity?.can_complete"
                class="ghost native-chatter-entry-action"
                type="button"
                :disabled="isActivityUpdating(entry)"
                @click="updateNativeActivity(entry, 'done')"
              >
                完成
              </button>
              <button
                v-if="entry.activity?.can_cancel"
                class="ghost native-chatter-entry-action"
                type="button"
                :disabled="isActivityUpdating(entry)"
                @click="updateNativeActivity(entry, 'cancel')"
              >
                取消
              </button>
            </div>
            <button
              v-if="entry.type === 'attachment' && entry.attachment"
              class="ghost native-attachment-download"
              type="button"
              @click="openNativeAttachment(entry.attachment)"
            >
              {{ nativeAttachmentViewLabel }}
            </button>
          </li>
        </ul>
      </section>
    </section>

    <DevContextPanel
      :visible="showHud"
      title="表单上下文"
      :entries="hudEntries"
    />
    <ProductConfirmDialog
      :open="actionSafetyConfirm.state.open"
      :title="actionSafetyConfirm.state.title"
      :message="actionSafetyConfirm.state.message"
      :confirm-label="actionSafetyConfirm.state.confirmLabel"
      :cancel-label="actionSafetyConfirm.state.cancelLabel"
      :tone="actionSafetyConfirm.state.tone"
      @confirm="actionSafetyConfirm.confirm"
      @cancel="actionSafetyConfirm.cancel"
    />
    <ProductInputDialog
      :open="actionInputDialog.state.open"
      :title="actionInputDialog.state.title"
      :label="actionInputDialog.state.label"
      :placeholder="actionInputDialog.state.placeholder"
      :value="actionInputDialog.state.value"
      :confirm-label="actionInputDialog.state.confirmLabel"
      :cancel-label="actionInputDialog.state.cancelLabel"
      :required="actionInputDialog.state.required"
      @confirm="actionInputDialog.confirm"
      @cancel="actionInputDialog.cancel"
    />

    <div
      v-if="relationSearchDialog.open"
      class="relation-dialog-backdrop"
      role="dialog"
      aria-modal="true"
      @keydown.esc="closeRelationSearchDialog"
    >
      <section class="relation-dialog">
        <header class="relation-dialog-head">
          <h3>{{ relationSearchDialog.title }}</h3>
          <button class="relation-dialog-close" type="button" :disabled="busy" :aria-label="relationSearchDialog.labels.close || '关闭'" @click="closeRelationSearchDialog">×</button>
        </header>
        <div class="relation-dialog-search">
          <input
            ref="relationSearchInputRef"
            class="input"
            type="text"
            :value="relationSearchDialog.keyword"
            :placeholder="relationSearchDialog.labels.search_placeholder || '输入名称搜索'"
            @input="setRelationSearchKeyword(($event.target as HTMLInputElement).value)"
            @keydown.enter.prevent="runRelationSearch"
          />
          <button class="chip-btn" type="button" :disabled="relationSearchDialog.loading" @click="runRelationSearch">{{ relationSearchDialog.labels.search || '搜索' }}</button>
        </div>
        <p v-if="relationSearchDialog.error" class="validation-error">{{ relationSearchDialog.error }}</p>
        <div class="relation-dialog-table-wrap">
          <table class="relation-dialog-table">
            <thead>
              <tr>
                <th class="relation-dialog-select-col"></th>
                <th v-for="column in relationSearchDialog.columns" :key="column.name">
                  {{ column.label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in relationSearchDialog.rows"
                :key="`rel-${row.id}`"
                :class="{ 'relation-dialog-row--active': relationSearchDialog.selectedId === row.id }"
                @click="selectRelationSearchRow(row)"
                @dblclick="confirmRelationSearchSelection(row)"
              >
                <td class="relation-dialog-select-col">
                  <input
                    type="radio"
                    name="relation-search-select"
                    :checked="relationSearchDialog.selectedId === row.id"
                    @change="selectRelationSearchRow(row)"
                  />
                </td>
                <td v-for="column in relationSearchDialog.columns" :key="`${row.id}-${column.name}`">
                  {{ relationSearchCell(row, column.name) }}
                </td>
              </tr>
            </tbody>
          </table>
          <p v-if="!relationSearchDialog.loading && !relationSearchDialog.rows.length" class="relation-dialog-empty">
            {{ relationSearchDialog.labels.empty || '未找到匹配记录' }}
          </p>
        </div>
        <footer class="relation-dialog-footer">
          <span class="relation-dialog-count">{{ relationRecordCountLabel }}</span>
          <span class="relation-dialog-footer-spacer"></span>
          <button
            class="primary"
            type="button"
            :disabled="busy || relationSearchDialog.loading || !relationSearchDialog.selectedId"
            @click="() => confirmRelationSearchSelection()"
          >
            {{ relationSearchDialog.labels.select || '选择' }}
          </button>
          <button
            v-if="relationSearchDialog.createMode !== 'none'"
            class="ghost"
            type="button"
            :disabled="busy || relationSearchDialog.loading"
            @click="createRelationFromSearchDialog"
          >
            {{ relationSearchDialog.labels.create || '新建' }}
          </button>
          <button class="ghost" type="button" :disabled="busy" @click="closeRelationSearchDialog">{{ relationSearchDialog.labels.cancel || '取消' }}</button>
        </footer>
      </section>
    </div>
    <AttachmentViewer ref="attachmentViewerRef" />
  </LayoutShell>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onBeforeUnmount, onDeactivated, onErrorCaptured, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import FieldValue from '../components/FieldValue.vue';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import ProductConfirmDialog from '../components/ProductConfirmDialog.vue';
import ProductInputDialog from '../components/ProductInputDialog.vue';
import AttachmentViewer from '../components/attachment/AttachmentViewer.vue';
import LayoutShell from '../components/template/LayoutShell.vue';
import PageHeaderTemplate from '../components/template/PageHeader.vue';
import NativeFormTreeRenderer, { type NativeFormLayoutNode } from '../components/template/NativeFormTreeRenderer.vue';
import SceneBlocksRenderer from '../components/scene/SceneBlocksRenderer.vue';
import PageFooterTemplate from '../components/template/PageFooter.vue';
import type {
  FormSectionFieldActionPayload,
  FormSectionFieldSchema,
  FormSectionFieldChange,
} from '../components/template/formSection.types';
import type { RelationFieldAdapter } from '../components/template/relationField.types';
import { createFormSectionFieldSchemaBuilder } from '../components/template/formSection.adapter';
import { resolveInputPlaceholder, resolveSelectPlaceholder } from '../components/template/placeholder.mapper';
import { resolveFieldSpanClass } from '../components/template/fieldSpan.mapper';
import { mapDescriptorSelectionOptions, mapRelationOptions } from '../components/template/option.mapper';
import { dispatchTemplateFieldChange } from '../components/template/fieldChange.dispatcher';
import { isHudEnabled, isSceneBlocksDebugEnabled } from '../config/debug';
import { config } from '../config';
import { useProductConfirmDialog } from '../composables/useProductConfirmDialog';
import { useProductInputDialog } from '../composables/useProductInputDialog';
import { intentRequest } from '../api/intents';
import { loadActionContractRaw, loadModelContractRaw } from '../api/contract';
import { ApiError } from '../api/client';
import { executeButton } from '../api/executeButton';
import {
  fetchChatterTimeline,
  postChatterMessage,
  scheduleChatterActivity,
  searchCollaborationUsers,
  updateChatterActivity,
  type ChatterTimelineEntry,
  type CollaborationUserOption,
} from '../api/chatter';
import { fileToBase64, uploadFile } from '../api/files';
import { triggerOnchange } from '../api/onchange';
import type { OnchangeLinePatch } from '../api/onchange';
import type { ActionContract, FieldDescriptor } from '@sc/schema';
import { useSessionStore } from '../stores/session';
import { ErrorCodes } from '../app/error_codes';
import {
  detectObjectMethodFromActionKey,
  normalizeActionKind,
  parseMaybeJsonRecord,
  toPositiveInt,
} from '../app/contractRuntime';
import { validateContractFormData } from '../app/contractValidation';
import { resolveActionIdFromContext } from '../app/actionContext';
import { findActionMeta, findActionMetaByMenu, findMenuNode } from '../app/menu';
import { pickContractNavQuery } from '../app/navigationContext';
import { buildCanonicalSceneRouteTarget, buildEntryTargetRouteTarget } from '../app/routeQuery';
import { readWorkspaceContext } from '../app/workspaceContext';
import { collectPolicyValidationErrors, evaluateActionPolicy, evaluateFieldPolicy } from '../app/contractPolicies';
import { buildRuntimeFieldStates } from '../app/modifierEngine';
import { buildX2ManyCommands } from '../app/x2manyCommands';
import { resolveSceneValidationSuggestedAction } from '../app/sceneValidationRecoveryStrategy';
import { findSceneReadyEntry, resolveFormSceneReady } from '../app/resolvers/sceneReadyResolver';
import { normalizeSceneActionProtocol } from '../app/sceneActionProtocol';
import { executeProjectionRefresh } from '../app/projectionRefreshRuntime';
import {
  createContractFormRecord,
  listContractFormRecords,
  readContractFormRecord,
  writeContractFormRecord,
} from '../app/runtime/contractFormDataRuntime';
import {
  collectContractV2ButtonStatusById,
  collectContractV2FieldStatusByCode,
  ContractV2DecodeError,
  createContractV2Store,
  decodeContractV2Snapshot,
  resolveContractV2ContainerTree,
  resolveContractV2FormStructureContract,
  resolveContractV2GlobalStatus,
  resolveContractV2MainData,
  resolveContractV2SourceContext,
  resolveContractV2ValueSource,
  type ContractV2Container,
  type ContractV2NormalizedStore,
  type ContractV2Widget,
} from '../app/contracts/v2';
import { executeSceneMutation } from '../app/sceneMutationRuntime';
import { isCoreSceneStrictMode } from '../app/contractStrictMode';
import {
  BUSINESS_CONFIG_ACTION_KEYS,
  BUSINESS_CONFIG_INTENTS,
  BUSINESS_CONFIG_MODES,
  BUSINESS_CONFIG_ROUTE_FLAGS,
  FORM_FIELD_CONFIG_INTENTS,
  isBusinessConfigMode,
  isBusinessConfigRuntimeModel,
} from '../app/businessConfigBoundaries';
import {
  collectUnifiedPageContractV2ButtonStatus,
  collectUnifiedPageContractV2FieldContainerStatus,
  collectUnifiedPageContractV2FieldStatus,
  collectUnifiedPageContractV2FieldWidgets,
  resolveUnifiedPageContractV2BusinessOperationProfile,
  resolveUnifiedPageContractV2FieldGroups,
  resolveUnifiedPageContractV2FormStructureContract,
  resolveUnifiedPageContractV2MainData,
  resolveUnifiedPageContractV2,
  resolveUnifiedPageContractV2GlobalStatus,
  resolveUnifiedPageContractV2SourceContext,
  resolveUnifiedPageContractV2VisibleFields,
} from '../app/contracts/unifiedPageContractV2';
import {
  actionResponseNavQuery as actionResponseNavQueryFromResult,
  actionResponseRouteTarget as actionResponseRouteTargetFromResult,
  normalizeActionSafety,
  normalizeActionLabel,
  normalizeRequiredParams,
  resolveV2ButtonStatus,
} from './contractForm/actionContract';
import { normalizeContractAccessPolicy } from './contractForm/accessPolicy';
import {
  cleanRelationDisplayLabel,
  fieldInputType,
  fieldType,
  fromDatetimeInputValue,
  lowCodeFieldSizeClass,
  normalizeLowCodeColumns,
  normalizeLowCodeFieldSize,
  normalizeRelationIds,
  parseMany2oneDisplay,
  sanitizeUiErrorMessage,
  toDateInputValue,
  toDatetimeInputValue,
  viewTypeDisplayLabel,
} from './contractForm/fieldUtils';
import {
  appendFormConfigOperationLogEntry,
  buildFormFieldConfigScope,
  buildFormConfigOperationLogStorageKey,
  buildCurrentFormGroupOptions,
  buildFormDesignerGroupNavigatorItems,
  buildFormDesignerSearchableFieldRows,
  createFormConfigOperationLogEntry,
  collectNativeFieldStructureGroups,
  extractLowCodeLayoutDraftState,
  filterFormDesignerFieldRows,
  formConfigOperationStatusLabel,
  fieldGroupTitleMatches,
  formatFormConfigAuditSummary,
  formatFormConfigOperationSummary as formatFormConfigOperationSummaryText,
  formatFormConfigOperationTime,
  collectNativeLayoutGroupTitles,
  fieldStructureTitle,
  inferLowCodeLayoutColumns,
  isReadableFieldGroupTitle,
  isSuggestedInternalFormField,
  layoutHasReadableFieldGroups,
  lowCodeFieldSizeLabel,
  mergeLowCodeLayoutWithRuntimeGroupShells,
  normalizeConfigPageLabel,
  normalizeFieldGroupTitle,
  normalizeFormConfigOperationLogEntries,
  readableFallbackFieldLabel,
  resolveSelectedFormSettingsFieldGroupTitle,
} from './contractForm/formConfigHelpers';
import {
  isMissingRequiredValue,
  isRequiredFieldEmptyByType,
  normalizeComparable,
  normalizeRouteDefault,
  parseNumeric,
  resolveNavigationUrl as resolveNavigationUrlFromOrigin,
} from './contractForm/valueUtils';
import { dictOrEmpty, mergeFieldLabelsFromSource } from './contractForm/recordUtils';
import {
  collectContractActionBadgeCountFieldNames,
  collectNativeFavoriteFieldNames,
  collectNativeLayoutBadgeCountFieldNames,
  collectNativeLayoutFieldNames,
  collectNativeVisibleSectionTitles,
  countNativeNodesByType,
  evaluateNativeModifierValue as evaluateNativeModifierValueWithResolver,
  findNativeFieldNode as findNativeFieldNodeInTree,
  isNativeFieldLayoutNode,
  isStaticTruthyModifier,
  nativeModifierValue,
  nativeFieldSubview as nativeFieldSubviewFromTree,
  nativeLayoutNodeType,
  nativeNodeFieldDescriptor as nativeNodeFieldDescriptorFromNode,
  nativeNodeFieldInfo,
  nativeNodeWidget,
  nativeNodeWidgetSemantics,
  normalizeNativeLayoutColumns,
  resolveNativeButtonLabel as resolveNativeButtonLabelFromNode,
  type NativeLayoutLikeNode,
} from './contractForm/nativeLayoutUtils';
import {
  formRuntimeCommandHintLabel,
  formRuntimeReasonLabel,
  formRuntimeRowStateLabel,
  buildOne2manyCommandValue as buildOne2manyCommandValueFromRows,
  isOne2manyEmptyValue,
  normalizeOne2manyColumnValue,
  one2manyCanCreateFromPolicies,
  one2manyColumnDisplayValue,
  one2manyColumnInputType,
  one2manyCreateLabelFromPolicies,
  one2manyDraftSummary,
  one2manyPrimaryColumnFromColumns,
  one2manyRowLabelFromPrimary,
  one2manyRowStateLabel,
  one2manySubviewPolicies,
  subviewColumnCount,
} from './contractForm/one2manyUtils';
import {
  relationEntry,
  dynamicDomainDependencyFields,
  fallbackRelationSearchColumns,
  hasAmbiguousRelationMatches,
  isBlockAllDomain,
  normalizeRelationSearchColumns,
  relationCreateMode,
  relationInlineCreate,
  relationModel as relationModelFromDescriptor,
  relationOptionFromRow,
  relationOrder,
  relationReadFields,
  relationSearchColumnsFromContract,
  relationSearchDialogContract,
  relationSearchReadFields,
  relationUiLabel,
  relationUiLabels,
  resolveRelationQuickFillOption,
  singleContainingRelationOption,
} from './contractForm/relationDescriptor';
import {
  isWorkflowTransitionMethod,
  normalizeWorkflowActionRows,
  normalizeWorkflowEvidenceGateRows,
  normalizeWorkflowPhaseStatusbar,
  workflowActionMethodAliases,
  workflowActionRowForMethod,
} from './contractForm/workflowContract';
import {
  formUiLabelFromLabels,
  formUiLabelsFromFormView,
  layoutContainsType,
} from './contractForm/uiLabels';
import {
  nativeActivityFieldLabel,
  nativeAttachmentContractOrNull,
  nativeAttachmentLabel,
  nativeAttachmentLabelsFromContract,
  nativeAttachmentMaxBytes as nativeAttachmentMaxBytesFromContract,
  nativeChatterActionsFromContract,
  resolveNativeAttachmentContract,
  resolveNativeChatterContract,
  resolveRuntimeCollaborationContract,
} from './contractForm/collaborationContract';
import {
  MANY2ONE_CREATE_OPTION,
  MANY2ONE_OPEN_RECORD_OPTION,
  MANY2ONE_SEARCH_MORE_OPTION,
  PROJECT_CONTEXT_CHANGED_EVENT,
  ContractAccessPolicyError,
  type BusyKind,
  type ContractAccessPolicy,
  type ContractAction,
  type ContractFieldGovernanceAction,
  type ContractFieldGovernanceRow,
  type ContractPromptField,
  type FormConfigAuditResult,
  type FormConfigOperationLogEntry,
  type LayoutNode,
  type LowCodeFieldSize,
  type NativeChatterAction,
  type NativeStatusbarVm,
  type One2ManyColumn,
  type One2ManyInlineRow,
  type RelationOption,
  type RelationSearchColumn,
  type RelationSearchRow,
  type RelationUiLabels,
  type StatusbarState,
  type UiStatus,
} from './contractForm/types';

async function collectActionParams(action: ContractAction): Promise<Record<string, unknown> | null> {
  const requiredParams = new Set((action.requiredParams || []).map((item) => item.toLowerCase()));
  if (!action.requiresReason && !requiredParams.has('reason')) return {};
  const reason = (await actionInputDialog.open({
    title: `${action.label || '操作'}原因`,
    label: '操作原因',
    placeholder: '请填写本次操作原因',
    confirmLabel: '继续',
    cancelLabel: '取消',
    required: true,
  }))?.trim() || '';
  if (!reason) {
    errorMessage.value = '请填写操作原因';
    status.value = 'error';
    return null;
  }
  return { reason };
}

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
}

const status = ref<UiStatus>('loading');
const isComponentActive = ref(true);
const instanceRouteIdentity = ref('');
const retainedRouteIdentity = ref('');
const renderErrorMessage = ref('');
const errorMessage = ref('');
const validationErrors = ref<string[]>([]);
const submissionFeedback = ref<{ kind: 'success' | 'warn' | 'error'; message: string } | null>(null);
const showOne2manyErrors = ref(false);
const busyKind = ref<BusyKind>(null);
const activeContractMode = ref('');
const formSettingsActiveTab = ref<'structure' | 'fields' | 'details' | 'actions'>('fields');
const contractModeFeedback = ref('');
const contractPromptRule = ref<Record<string, unknown> | null>(null);
const contractPromptValues = reactive<Record<string, string>>({});
const actionSafetyConfirm = useProductConfirmDialog();
const actionInputDialog = useProductInputDialog();
const contract = ref<ActionContract | null>(null);
const contractMeta = ref<Record<string, unknown> | null>(null);
const v2ContractStore = ref<ContractV2NormalizedStore | null>(null);
const v2ContractDecodeError = ref('');
const v2ShadowStoreReady = computed(() => Boolean(v2ContractStore.value));
const v2ShadowWidgetCount = computed(() => v2ContractStore.value?.widgetsById.size || 0);
const v2ShadowActionCount = computed(() => v2ContractStore.value?.actionsById.size || 0);
const v2ShadowButtonStatusCount = computed(() => v2ContractStore.value?.buttonStatusById.size || 0);

function formRouteIdentity() {
  const query = route.query as Record<string, unknown>;
  return [
    String(route.params.model || ''),
    String(route.params.id || ''),
    String(query.action_id || ''),
    String(query.menu_id || ''),
    String(query.view_id || query.viewId || ''),
    String(query.current_business_category_code || query.default_business_category_code || ''),
    String(query.allowed_business_category_codes || ''),
  ].join('|');
}
const v2ShadowFieldCodes = computed(() => Array.from(v2ContractStore.value?.widgetsByFieldCode.keys() || []));
const v2ShadowFieldCodeCount = computed(() => v2ShadowFieldCodes.value.length);
const v2ShadowLegacyFieldMissing = computed(() => {
  const legacyFields = contract.value?.fields || {};
  return v2ShadowFieldCodes.value.filter((fieldCode) => !(fieldCode in legacyFields));
});
const v2ShadowLegacyFieldOverlapCount = computed(() => v2ShadowFieldCodeCount.value - v2ShadowLegacyFieldMissing.value.length);
const v2ShadowLegacyFieldMissingPreview = computed(() => v2ShadowLegacyFieldMissing.value.slice(0, 8).join(',') || '-');
const v2ShadowFormStructureContract = computed(() => resolveContractV2FormStructureContract(v2ContractStore.value));
const v2ShadowFormStructureSlotCount = computed(() => {
  const slots = v2ShadowFormStructureContract.value.slots;
  return Array.isArray(slots) ? slots.length : 0;
});
const v2ShadowLayoutSourceKind = computed(() => {
  const containers = resolveContractV2ContainerTree(v2ContractStore.value);
  if (containers.length) return 'v2_store';
  return nativeFormLayoutNodes.value.length ? 'legacy_layout' : 'none';
});
const v2ShadowGlobalSourceKind = computed(() => (resolveContractV2GlobalStatus(v2ContractStore.value) ? 'v2_store' : 'legacy_resolver'));
const v2ShadowSourceContextKind = computed(() => (Object.keys(resolveContractV2SourceContext(v2ContractStore.value)).length ? 'v2_store' : 'legacy_resolver'));
const v2ShadowStatusFieldCount = computed(() => Object.keys(collectContractV2FieldStatusByCode(v2ContractStore.value)).length);
const v2ShadowValueSource = computed(() => resolveContractV2ValueSource(v2ContractStore.value));
const v2ShadowValueSourceKind = computed(() => v2ShadowValueSource.value.kind);
const v2ShadowValueFieldCount = computed(() => (
  v2ShadowFieldCodes.value.filter((fieldCode) => (
    Object.prototype.hasOwnProperty.call(v2ShadowValueSource.value.values, fieldCode)
  )).length
));
const v2ShadowMainDataFieldCount = computed(() => (
  v2ShadowFieldCodes.value.filter((fieldCode) => (
    Object.prototype.hasOwnProperty.call(resolveContractV2MainData(v2ContractStore.value), fieldCode)
  )).length
));
const v2ShadowReadonlyValueCount = computed(() => (
  layoutNodes.value.filter((node) => (
    node.kind === 'field'
    && node.readonly
    && Boolean(v2ContractStore.value?.widgetsByFieldCode.has(node.name))
    && Object.prototype.hasOwnProperty.call(v2ShadowValueSource.value.values, node.name)
  )).length
));
const activeFilterKey = ref('');
const originalValues = ref<Record<string, unknown>>({});
const recordVersionToken = ref('');
const formData = reactive<Record<string, unknown>>({});
const nativeLayoutVisibilityRevision = ref(0);
const advancedExpanded = ref(false);
const relationOptions = ref<Record<string, RelationOption[]>>({});
const relationFieldDescriptors = ref<Record<string, Record<string, FieldDescriptor>>>({});
const relationKeywords = reactive<Record<string, string>>({});
const invalidatedRelationKeywords = reactive<Record<string, string>>({});
const clearedDynamicRelationFields = reactive<Record<string, boolean>>({});
const relationSearchDialog = reactive<{
  open: boolean;
  fieldName: string;
  title: string;
  keyword: string;
  loading: boolean;
  error: string;
  options: RelationOption[];
  rows: RelationSearchRow[];
  columns: RelationSearchColumn[];
  selectedId: number | null;
  createMode: 'none' | 'quick' | 'page';
  labels: RelationUiLabels;
}>({
  open: false,
  fieldName: '',
  title: '',
  keyword: '',
  loading: false,
  error: '',
  options: [],
  rows: [],
  columns: [],
  selectedId: null,
  createMode: 'none',
  labels: {},
});
const relationSearchInputRef = ref<HTMLInputElement | null>(null);
const deniedRelationModels = new Set<string>();
const one2manyRows = reactive<Record<string, One2ManyInlineRow[]>>({});
const relationQueryTimers: Record<string, ReturnType<typeof setTimeout>> = {};
const onchangeModifiersPatch = ref<Record<string, Record<string, unknown>>>({});
const onchangeWarnings = ref<Array<{ title?: string; message?: string; reason_code?: string }>>([]);
const onchangeLinePatches = ref<OnchangeLinePatch[]>([]);
const changedFieldSet = new Set<string>();
const dirtyFieldSet = new Set<string>();
let onchangeTimer: ReturnType<typeof setTimeout> | null = null;
const applyingOnchangePatch = ref(false);
const activeChatterMode = ref('');
const activeChatterLabel = ref('');
const chatterDraft = ref('');
const activitySummary = ref('');
const activityDeadline = ref('');
const activityNote = ref('');
const collaborationUserQuery = ref('');
const collaborationUserOptions = ref<CollaborationUserOption[]>([]);
const collaborationUsersLoading = ref(false);
const selectedMentionUserIds = ref<number[]>([]);
const activityAssigneeId = ref(0);
const chatterPosting = ref(false);
const chatterLoading = ref(false);
const chatterError = ref('');
const chatterTimeline = ref<ChatterTimelineEntry[]>([]);
const activityUpdatingIds = ref<number[]>([]);
const attachmentUploading = ref(false);
const attachmentError = ref('');
const attachmentViewerRef = ref<InstanceType<typeof AttachmentViewer> | null>(null);
const pendingNativeAttachments = ref<Array<{ key: string; name: string; size: number; file: File }>>([]);
const nativeChatterAutoLoadKey = ref('');
let activeReloadToken = 0;
let activeReloadIdentity = '';
let activeReloadPromise: Promise<void> | null = null;

const model = computed(() => String(route.params.model || contract.value?.head?.model || contract.value?.model || ''));
const menuId = computed(() => Number(route.query.menu_id || 0) || 0);
const actionId = computed(() => {
  const rawRecordId = String(route.params.id || '').trim();
  const isCreateRoute = !rawRecordId || rawRecordId === 'new';
  const menuAction = findActionMetaByMenu(session.menuTree, menuId.value);
  return resolveActionIdFromContext({
    routeQuery: route.query as Record<string, unknown>,
    menuActionId: menuAction?.action_id,
    menuActionModel: menuAction?.model,
    currentActionId: isCreateRoute ? session.currentAction?.action_id : null,
    currentActionModel: session.currentAction?.model,
    model: model.value,
  });
});
const currentMenuTitle = computed(() => {
  const node = findMenuNode(session.menuTree, menuId.value);
  return String(node?.label || node?.name || node?.title || '').trim();
});
const recordId = computed(() => {
  const raw = String(route.params.id || '').trim();
  if (!raw || raw === 'new') return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
});
const recordIdDisplay = computed(() => (recordId.value ? String(recordId.value) : 'new'));
const showHud = computed(() => isHudEnabled(route));
const showSceneBlocksDebug = computed(() => isSceneBlocksDebugEnabled(route));
const requestedSurface = computed<'user' | 'native' | 'hud'>(() => {
  const raw = String(route.query.surface || '').trim().toLowerCase();
  if (raw === 'native' || raw === 'hud' || raw === 'user') return raw;
  if (showHud.value) return 'hud';
  return 'user';
});
const requestedSourceMode = computed(() => (
  requestedSurface.value === 'native' ? 'native_parser' : 'governance_pipeline'
));
const busy = computed(() => busyKind.value !== null);

function recordVersionPolicy() {
  const raw = (contract.value as Record<string, unknown> | null)?.record_version;
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  const policy = raw as Record<string, unknown>;
  if (policy.enabled !== true) return null;
  const tokenField = String(policy.token_field || '').trim();
  const requestParam = String(policy.request_param || '').trim();
  if (!tokenField || requestParam !== 'if_match') return null;
  return { tokenField };
}

const renderProfile = computed<'create' | 'edit' | 'readonly'>(() => {
  const storeSourceContext = resolveContractV2SourceContext(v2ContractStore.value);
  const sourceContext = Object.keys(storeSourceContext).length
    ? storeSourceContext
    : resolveUnifiedPageContractV2SourceContext(contract.value);
  const head = (contract.value?.head || {}) as Record<string, unknown>;
  const profile = String(sourceContext.renderProfile || contract.value?.render_profile || head.render_profile || '').trim().toLowerCase();
  if (profile === 'readonly') return 'readonly';
  if (profile === 'edit') return 'edit';
  if (profile === 'create') return 'create';
  if (!canSave.value) return 'readonly';
  return recordId.value ? 'edit' : 'create';
});

const rights = computed(() => {
  const globalStatus = resolveContractV2GlobalStatus(v2ContractStore.value) || resolveUnifiedPageContractV2GlobalStatus(contract.value);
  const pageAuth = String(globalStatus?.pageAuth || '').trim().toLowerCase();
  if (globalStatus?.pageVisible === false || pageAuth === 'none') {
    return { read: false, write: false, create: false, unlink: false };
  }
  const head = contract.value?.head?.permissions;
  const effective = contract.value?.permissions?.effective?.rights;
  const resolve = (key: 'read' | 'write' | 'create' | 'unlink') => {
    const a = head?.[key];
    if (typeof a === 'boolean') return a;
    const b = effective?.[key];
    if (typeof b === 'boolean') return b;
    return true;
  };
  return {
    read: resolve('read'),
    write: pageAuth === 'read' ? false : resolve('write'),
    create: pageAuth === 'read' ? false : resolve('create'),
    unlink: pageAuth === 'read' ? false : resolve('unlink'),
  };
});

const canSave = computed(() => (recordId.value ? rights.value.write : rights.value.create));
const relationRecordCountLabel = computed(() => {
  const template = relationSearchDialog.labels.record_count || '%s 条记录';
  const count = String(relationSearchDialog.rows.length);
  return template.includes('%s') ? template.replace('%s', count) : `${count} ${template}`.trim();
});
const isProjectQuickIntakeMode = computed(() => {
  if (String(model.value || '').trim() !== 'project.project') return false;
  if (recordId.value) return false;
  return String(route.query.intake_mode || '').trim().toLowerCase() === 'quick';
});
const isProjectStandardIntakeMode = computed(() => {
  if (String(model.value || '').trim() !== 'project.project') return false;
  if (recordId.value) return false;
  if (isProjectQuickIntakeMode.value) return false;
  if (String(route.query.intake_mode || '').trim().toLowerCase() === 'standard') return true;
  return String(route.query.scene_key || '').trim() === 'projects.intake';
});
const isProjectIntakeCreateMode = computed(() => isProjectQuickIntakeMode.value || isProjectStandardIntakeMode.value);
const intakeAutosaveKey = computed(() => {
  if (!isProjectIntakeCreateMode.value) return '';
  const mode = isProjectQuickIntakeMode.value ? 'quick' : 'standard';
  const userId = Number(session.user?.id || 0) || 0;
  return `sc:intake:autosave:project.project:${mode}:u${userId}`;
});
const quickRequiredReady = computed(() => {
  if (!isProjectQuickIntakeMode.value) return true;
  const projectName = String(formData.name || '').trim();
  const managerId = Number(formData.manager_id || 0);
  return Boolean(projectName) && Number.isFinite(managerId) && managerId > 0;
});
const standardCreateReady = computed(() => {
  if (!isProjectStandardIntakeMode.value) return true;
  const projectName = String(formData.name || '').trim();
  const managerId = Number(formData.manager_id || 0);
  return Boolean(projectName) && Number.isFinite(managerId) && managerId > 0;
});

function hasPendingInlineRelationChange() {
  return layoutNodes.value.some((node) => {
    if (node.kind !== 'field' || node.readonly) return false;
    const descriptor = contract.value?.fields?.[node.name];
    if (fieldType(descriptor) !== 'many2one') return false;
    const inline = relationInlineCreate(descriptor);
    if (!inline.enabled || !inline.createOnNoMatch) return false;
    const currentId = Number(formData[node.name] || 0);
    if (Number.isFinite(currentId) && currentId > 0) return false;
    return Boolean(relationKeyword(node.name).trim());
  });
}

function hasPendingMany2manyTagCreate() {
  return Object.entries(relationKeywords).some(([name, keyword]) => {
    if (!String(keyword || '').trim()) return false;
    if (!isFieldWritable(name)) return false;
    if (!Array.isArray(formData[name])) return false;
    const descriptor = contract.value?.fields?.[name];
    const inline = relationInlineCreate(descriptor);
    if (!inline.enabled || !inline.createOnNoMatch) return false;
    return Boolean(relationModel(name));
  });
}

function hasOne2manyDraftChanges() {
  return layoutNodes.value.some((node) => {
    if (node.kind !== 'field' || node.readonly) return false;
    const descriptor = contract.value?.fields?.[node.name];
    if (fieldType(descriptor) !== 'one2many') return false;
    return one2manyFieldRows(node.name).some((row) => row.isNew || row.dirty || row.removed);
  });
}

const hasChanges = computed(() => {
  if (hasPendingInlineRelationChange()) return true;
  if (hasPendingMany2manyTagCreate()) return true;
  if (hasOne2manyDraftChanges()) return true;
  const statusField = nativeStatusbar.value.field;
  if (
    statusField
    && !nativeStatusbar.value.readonly
    && comparableFieldValue(statusField, formData[statusField]) !== comparableFieldValue(statusField, originalValues.value[statusField])
  ) {
    return true;
  }
  const keys = Object.keys(formData);
  return keys.some((key) => {
    if (!isFieldWritable(key)) return false;
    return comparableFieldValue(key, formData[key]) !== comparableFieldValue(key, originalValues.value[key]);
  });
});
const writableFieldCount = computed(() =>
  layoutNodes.value.filter((node) => node.kind === 'field' && !node.readonly).length,
);
const changedFieldCount = computed(() =>
  Object.keys(formData).filter((key) => isFieldWritable(key) && comparableFieldValue(key, formData[key]) !== comparableFieldValue(key, originalValues.value[key])).length
    + (hasOne2manyDraftChanges() ? 1 : 0),
);

const intakeRequiredFields = computed(() => {
  if (!isProjectIntakeCreateMode.value) return [];
  return layoutNodes.value
    .filter((node) => node.kind === 'field' && node.required && isFieldVisible(node.name))
    .map((node) => ({ name: node.name, label: node.label || node.name }));
});

const intakeRequiredReadyCount = computed(() => {
  if (!isProjectIntakeCreateMode.value) return 0;
  return intakeRequiredFields.value.filter((field) => {
    const value = formData[field.name];
    if (value === null || value === undefined) return false;
    if (typeof value === 'string') return value.trim().length > 0;
    if (typeof value === 'number') return Number.isFinite(value) && value > 0;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === 'boolean') return true;
    return Boolean(value);
  }).length;
});

const intakeMissingRequiredLabels = computed(() => {
  if (!isProjectIntakeCreateMode.value) return [];
  return intakeRequiredFields.value
    .filter((field) => {
      const value = formData[field.name];
      if (value === null || value === undefined) return true;
      if (typeof value === 'string') return value.trim().length === 0;
      if (typeof value === 'number') return !Number.isFinite(value) || value <= 0;
      if (Array.isArray(value)) return value.length === 0;
      return false;
    })
    .map((field) => String(field.label || '').trim())
    .slice(0, 5);
});

const intakeRequiredSummary = computed(() => {
  if (!isProjectIntakeCreateMode.value) return '';
  const total = intakeRequiredFields.value.length;
  const done = intakeRequiredReadyCount.value;
  if (total <= 0) return '当前页面未提供必填字段约束。';
  return `${done}/${total}`;
});

const intakeMissingSummary = computed(() => {
  if (!isProjectIntakeCreateMode.value) return '';
  if (!intakeMissingRequiredLabels.value.length) return '无';
  return intakeMissingRequiredLabels.value.join('、');
});

const one2manyValidation = computed(() => collectOne2manyDraftValidation());

function isTechnicalViewTitle(value: string) {
  const normalized = String(value || '').trim();
  return /^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*){1,}\.(?:tree|list|form|kanban|search|graph|pivot|calendar|activity|gantt)$/i.test(normalized);
}

const pageTitle = computed(() => {
  const menuTitle = currentMenuTitle.value;
  if (menuTitle) return menuTitle;
  const title = String(contract.value?.head?.title || '').trim();
  if (title && !isTechnicalViewTitle(title)) return title;
  const recordTitle = String(formData.display_name || formData.name || '').trim();
  if (recordTitle) return recordTitle;
  return '业务表单';
});

const currentBusinessCategoryLabel = computed(() => {
  const contractRecord = dictOrEmpty(contract.value);
  const head = dictOrEmpty(contractRecord.head);
  const headContext = head.context && typeof head.context === 'object'
    ? head.context as Record<string, unknown>
    : {};
  const contractContext = contractRecord.context && typeof contractRecord.context === 'object'
    ? contractRecord.context as Record<string, unknown>
    : {};
  return String(
    route.query.current_business_category_label
    || route.query.default_business_category_label
    || headContext.current_business_category_label
    || headContext.default_business_category_label
    || contractContext.current_business_category_label
    || contractContext.default_business_category_label
    || relationKeywords.business_category_id
    || '',
  ).trim();
});

const currentBusinessCategoryCode = computed(() => {
  const contractRecord = dictOrEmpty(contract.value);
  const head = dictOrEmpty(contractRecord.head);
  const headContext = head.context && typeof head.context === 'object'
    ? head.context as Record<string, unknown>
    : {};
  const contractContext = contractRecord.context && typeof contractRecord.context === 'object'
    ? contractRecord.context as Record<string, unknown>
    : {};
  return String(
    route.query.current_business_category_code
    || route.query.default_business_category_code
    || headContext.current_business_category_code
    || headContext.default_business_category_code
    || contractContext.current_business_category_code
    || contractContext.default_business_category_code
    || '',
  ).trim();
});

const pageDisplayTitle = computed(() => {
  if (isProjectIntakeCreateMode.value) return '创建项目';
  const businessTitle = currentBusinessCategoryLabel.value || pageTitle.value;
  if (businessTitle) {
    if (recordId.value) return businessTitle;
    return businessTitle.startsWith('新建') ? businessTitle : `新建${businessTitle}`;
  }
  return pageTitle.value;
});

const pageDisplaySubtitle = computed(() => {
  if (isProjectIntakeCreateMode.value) {
    return '填写核心信息即可完成项目立项';
  }
  if (currentBusinessCategoryLabel.value && pageTitle.value !== currentBusinessCategoryLabel.value) {
    return pageTitle.value;
  }
  const recordTitle = String(formData.display_name || formData.name || '').trim();
  if (recordTitle && recordTitle !== pageDisplayTitle.value) return recordTitle;
  return recordId.value ? `记录 #${recordId.value}` : '';
});

const activityPageTitle = computed(() => {
  const recordTitle = String(formData.display_name || formData.name || '').trim();
  if (recordId.value && recordTitle) return recordTitle;
  return pageDisplayTitle.value;
});

watch(
  activityPageTitle,
  (title) => {
    if (!isComponentActive.value) return;
    session.updateActiveActivityTitle(title);
  },
  { immediate: true },
);

const suppressPageHeaderTitle = computed(() => useNativeFormTree.value && !isProjectIntakeCreateMode.value);

const intakeCreateButtonLabel = computed(() => {
  if (!isProjectIntakeCreateMode.value) return '创建项目';
  return busy.value && busyKind.value === 'save' ? '创建中…' : '创建项目';
});

const submitButtonLabel = computed(() => {
  const footerAction = primaryCreateFooterAction.value;
  if (busy.value && busyKind.value === 'save' && !primarySubmitAction.value) {
    if (isProjectQuickIntakeMode.value) return '创建中...';
    return !recordId.value && footerAction ? '处理中...' : (!recordId.value ? '提交中...' : formUiLabel('saving'));
  }
  if (busy.value && busyKind.value === 'action' && (primarySubmitAction.value || footerAction)) {
    return footerAction ? '处理中...' : '提交中...';
  }
  if (footerAction) return footerAction.label;
  if (primarySubmitAction.value) {
    return '提交';
  }
  if (isProjectQuickIntakeMode.value && !recordId.value) {
    return '创建并进入项目驾驶舱';
  }
  if (!recordId.value && !isProjectIntakeCreateMode.value) {
    return '提交';
  }
  return formUiLabel('save');
});
const showPrimaryBusinessFormAction = computed(() => !showCurrentFormFieldConfigScope.value && !isProjectIntakeCreateMode.value);
const showDraftSaveAction = computed(() => showPrimaryBusinessFormAction.value && !recordId.value && canSave.value && !primaryCreateFooterAction.value);
const draftSaveButtonLabel = computed(() => (busy.value && busyKind.value === 'save' ? formUiLabel('saving') : '保存草稿'));
const showDiscardAction = computed(() => !isProjectIntakeCreateMode.value && Boolean(recordId.value) && hasChanges.value);

const headerActionsVisible = computed(() => {
  if (isProjectIntakeCreateMode.value) return [];
  const filterPrimarySubmit = (actions: ContractAction[]) => actions.filter((action) => !isUnifiedSubmitAction(action));
  if (useNativeFormTree.value) {
    return filterPrimarySubmit(headerActions.value.filter((action) => action.sourceWidgetId === 'page.header'));
  }
  return filterPrimarySubmit(headerActions.value);
});

function isHeaderConfigAction(action: ContractAction) {
  const label = String(action.label || '').trim();
  const key = String(action.key || '').trim().toLowerCase();
  const source = String(action.sourceWidgetId || '').trim().toLowerCase();
  return label.includes('设置') || key.includes('setting') || key.includes('config') || source.includes('setting') || source.includes('config');
}

const headerBusinessActionsVisible = computed(() => {
  if (showCurrentFormFieldConfigScope.value) return [];
  return headerActionsVisible.value.filter((action) => !isHeaderConfigAction(action));
});
const headerConfigActionsVisible = computed(() => headerActionsVisible.value.filter((action) => isHeaderConfigAction(action) && action.enabled));

function headerActionButtonClass(action: ContractAction) {
  return ['sc-btn', 'sc-btn-sm', action.semantic === 'primary_action' && !isHeaderConfigAction(action) ? 'sc-btn-primary' : 'sc-btn-ghost'];
}

function contractV2ActionRules() {
  const v2ActionRules = resolveUnifiedPageContractV2(contract.value)?.actionContract;
  const v2ActionRuleList = parseMaybeJsonRecord(v2ActionRules).actionRuleList;
  return Array.isArray(v2ActionRuleList)
    ? v2ActionRuleList.filter((row): row is Record<string, unknown> => Boolean(row && typeof row === 'object' && !Array.isArray(row)))
    : [];
}

function ruleClientMode(rule: Record<string, unknown>) {
  const target = parseMaybeJsonRecord(rule.target);
  return String(target.mode || target.client_mode || rule.mode || rule.client_mode || '').trim();
}

function ruleKey(rule: Record<string, unknown>) {
  return String(rule.actionKey || rule.key || rule.actionId || '').trim();
}

function ruleControl(rule: Record<string, unknown>) {
  const target = parseMaybeJsonRecord(rule.target);
  return parseMaybeJsonRecord(target.control || target.ui_control || rule.control || rule.ui_control);
}

function rulePromptFields(rule: Record<string, unknown>): ContractPromptField[] {
  const target = parseMaybeJsonRecord(rule.target);
  const promptSchema = parseMaybeJsonRecord(target.prompt_schema || target.promptSchema || rule.prompt_schema || rule.promptSchema);
  const fields = Array.isArray(promptSchema.fields) ? promptSchema.fields : [];
  return fields
    .map((raw) => {
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
      const field = raw as Record<string, unknown>;
      const name = String(field.name || '').trim();
      if (!name) return null;
      const options = Array.isArray(field.options)
        ? field.options
          .map((item) => parseMaybeJsonRecord(item))
          .map((row) => ({
            value: String(row.value || '').trim(),
            label: String(row.label || row.value || '').trim(),
          }))
          .filter((row) => row.value)
        : [];
      return {
        name,
        label: String(field.label || name).trim(),
        required: field.required !== false,
        defaultValue: String(field.default || '').trim(),
        options,
      };
    })
    .filter((field): field is ContractPromptField => Boolean(field));
}

function contractFieldActions(field: FormSectionFieldSchema) {
  const mode = activeContractMode.value;
  if (!mode) return [];
  const fieldWidgetId = `field.${String(field.name || '').trim()}`;
  const fieldKey = String(field.name || '').trim();
  return contractV2ActionRules()
    .filter((rule) => {
      const triggerType = String(rule.triggerType || rule.trigger_type || '').trim();
      if (triggerType && !['change', 'select', 'click'].includes(triggerType)) return false;
      const sourceWidgetId = String(rule.sourceWidgetId || rule.source_widget_id || '').trim();
      const targetIds = Array.isArray(rule.targetIds || rule.target_ids) ? (rule.targetIds || rule.target_ids) as unknown[] : [];
      if (sourceWidgetId !== fieldWidgetId && !targetIds.map((item) => String(item)).includes(fieldWidgetId)) return false;
      const expectedMode = ruleClientMode(rule);
      return !expectedMode || expectedMode === mode;
    })
    .map((rule) => {
      const control = ruleControl(rule);
      return {
        key: ruleKey(rule),
        label: String(control.label || rule.label || ruleKey(rule)).trim(),
        value: String(control.value || ruleKey(rule)).trim(),
        checked: fieldKey && Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)
          ? fieldVisibilityDraft[fieldKey] === (String(control.value || ruleKey(rule)).trim() === 'show')
          : control.checked === true,
        disabled: control.disabled === true || busy.value,
        title: String(control.title || '').trim(),
        raw: rule,
      };
    });
}

function formSettingsFieldActions(field: FormSectionFieldSchema) {
  const fieldKey = String(field.name || '').trim();
  if (!fieldKey) return [];
  const existingRow = activeContractModeFieldRows.value.find((row) => row.fieldKey === fieldKey);
  if (existingRow?.actions.length) {
    return existingRow.actions.map((action) => ({
      ...action,
      checked: Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)
        ? fieldVisibilityDraft[fieldKey] === (action.value === 'show')
        : Boolean(action.checked),
      disabled: Boolean(action.disabled) || busy.value,
    }));
  }
  const visible = Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)
    ? fieldVisibilityDraft[fieldKey]
    : true;
  return [
    {
      key: `${fieldKey}:show`,
      label: '显示',
      value: 'show',
      checked: visible,
      disabled: busy.value,
      title: '在当前页面显示这个字段',
      raw: {},
    },
    {
      key: `${fieldKey}:hide`,
      label: '隐藏',
      value: 'hide',
      checked: !visible,
      disabled: busy.value,
      title: '在当前页面隐藏这个字段',
      raw: {},
    },
  ];
}

const contractPromptFields = computed(() => (contractPromptRule.value ? rulePromptFields(contractPromptRule.value) : []));

const activeContractModeActions = computed(() => {
  const mode = activeContractMode.value;
  if (!mode) return [];
  const source = `mode.${mode}`;
  return contractV2ActionRules()
    .filter((rule) => {
      if (ruleKey(rule) === BUSINESS_CONFIG_ACTION_KEYS.currentFormFieldOrderSave) return false;
      const sourceWidgetId = String(rule.sourceWidgetId || rule.source_widget_id || '').trim();
      if (sourceWidgetId !== source) return false;
      const expectedMode = ruleClientMode(rule);
      return !expectedMode || expectedMode === mode;
    })
    .map((rule) => ({
      key: ruleKey(rule),
      label: String(rule.label || ruleKey(rule)).trim(),
      raw: rule,
    }));
});


const fieldOrderDraft = ref<string[]>([]);
const fieldOrderPreviewActive = ref(false);
const nativeFormDesignFieldKeys = ref<string[]>([]);
const nativeFormDesignFieldLabels = ref<Record<string, string>>({});
const formConfigFieldLabelCache = reactive<Record<string, string>>({});
const fieldGroupBase = ref<Record<string, string>>({});
const fieldGroupSavedBase = ref<Record<string, string>>({});
const fieldGroupDraft = reactive<Record<string, string>>({});
const formLayoutColumnsBase = ref<1 | 2 | 3>(3);
const formLayoutColumnsDraft = ref<1 | 2 | 3>(3);
const formLayoutColumnsConfigured = ref(false);
const groupVisibilityBase = ref<Record<string, boolean>>({});
const groupVisibilityDraft = reactive<Record<string, boolean>>({});
const groupColumnsBase = ref<Record<string, 1 | 2 | 3>>({});
const groupColumnsDraft = reactive<Record<string, 1 | 2 | 3>>({});
const fieldSizeBase = ref<Record<string, LowCodeFieldSize>>({});
const fieldSizeDraft = reactive<Record<string, LowCodeFieldSize>>({});
const formLayoutDirty = ref(false);
const groupLayoutDirtyKeys = reactive<Record<string, boolean>>({});
const fieldLayoutDirtyKeys = reactive<Record<string, boolean>>({});
const fieldMoveTargetDraft = reactive<Record<string, string>>({});
const draggingFieldKey = ref('');
const draggingFieldLabel = ref('');
const dropTargetFieldKey = ref('');
const dropTargetPlacement = ref<'before' | 'after'>('before');
const fieldDragAutoScrollDirection = ref(0);
let fieldDragAutoScrollFrame = 0;
const selectedFormSettingsFieldKey = ref('');
const selectedFormSettingsFieldLabel = ref('');
const selectedFormSettingsFieldGroupTitleDraft = ref('');
const selectedFormSettingsFieldGroupTitleEdit = ref('');
const formDesignerFieldSearchText = ref('');
const selectedFormSettingsOrderTargetKey = ref('');
const selectedFormSettingsOrderPlacement = ref<'before' | 'after'>('before');
const isContractFieldOrderEditable = computed(() => (
  !isBusinessConfigRuntimeModel(model.value)
  && (
    activeContractMode.value === BUSINESS_CONFIG_MODES.formFieldConfiguration
    || activeContractMode.value === BUSINESS_CONFIG_MODES.lowCode
  )
));
const showReturnToBusinessConfigAction = computed(() => (
  routeQueryText(BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig) === '1'
  || activeContractMode.value === BUSINESS_CONFIG_MODES.lowCode
));
const fieldVisibilityBase = ref<Record<string, boolean>>({});
const fieldVisibilityDirty = ref(false);
const fieldVisibilityDraft = reactive<Record<string, boolean>>({});
const fieldVisibilityDirtyKeys = reactive<Record<string, boolean>>({});
const formConfigAuditBusy = ref(false);
const formConfigAuditResult = ref<FormConfigAuditResult | null>(null);
const formConfigOperationLog = ref<FormConfigOperationLogEntry[]>([]);
const lowCodeFieldCreateDialog = reactive({
  open: false,
  afterFieldKey: '',
  groupTitle: '',
  sequence: 100,
  label: '',
  ttype: 'char',
});
const lowCodeFieldCreateLabelRef = ref<HTMLInputElement | null>(null);
const lowCodeContractLoaded = ref(false);
const lowCodeContractHydrating = ref(false);
const lowCodePrecheckWarnings = ref<string[]>([]);
const lowCodeContractList = ref<Array<{ id: number; name: string; model: string; status: string; version_no: number }>>([]);
const lowCodeSelectedContractName = ref('');
const lowCodeFormLayoutBase = ref<NativeFormLayoutNode[]>([]);
const lowCodeLayoutDraft = ref<Array<{ section: 'form' | 'list' | 'kanban'; object: string; field: string }>>([]);

const contractModeBaseFieldRows = computed<ContractFieldGovernanceRow[]>(() => {
  const mode = activeContractMode.value;
  if (!mode) return [];
  const rows = new Map<string, ContractFieldGovernanceRow>();
  contractV2ActionRules().forEach((rule) => {
    const sourceWidgetId = String(rule.sourceWidgetId || rule.source_widget_id || '').trim();
    if (!sourceWidgetId.startsWith('field.')) return;
    const expectedMode = ruleClientMode(rule);
    if (expectedMode && expectedMode !== mode) return;
    const fieldKey = sourceWidgetId.slice('field.'.length);
    if (!fieldKey) return;
    const control = ruleControl(rule);
    const target = parseMaybeJsonRecord(rule.target);
    const params = parseMaybeJsonRecord(target.params || rule.params);
    const fieldLabel = String(params.label || fieldKey).trim();
    const action: ContractFieldGovernanceAction = {
      key: ruleKey(rule),
      label: String(control.label || rule.label || ruleKey(rule)).trim(),
      value: String(control.value || ruleKey(rule)).trim(),
      checked: control.checked === true,
      disabled: control.disabled === true || busy.value,
      title: String(control.title || '').trim(),
      raw: rule,
    };
    if (!rows.has(fieldKey)) {
      rows.set(fieldKey, { fieldKey, label: fieldLabel, actions: [] });
    }
    rows.get(fieldKey)?.actions.push(action);
  });
  return Array.from(rows.values())
    .map((row) => ({
      ...row,
      actions: row.actions.sort((left, right) => {
        const order = (value: string) => (value === 'show' ? 0 : value === 'hide' ? 1 : 2);
        return order(left.value) - order(right.value) || left.label.localeCompare(right.label);
      }),
    }));
});

const activeContractModeFieldRows = computed<ContractFieldGovernanceRow[]>(() => {
  const computedRows = contractModeBaseFieldRows.value;
  const rowsWithDraftVisibility = computedRows.map((row) => ({
    ...row,
    actions: row.actions.map((action) => ({
      ...action,
      checked: Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, row.fieldKey)
        ? fieldVisibilityDraft[row.fieldKey] === (action.value === 'show')
        : action.checked,
    })),
  }));
  if (!isContractFieldOrderEditable.value || !fieldOrderDraft.value.length) return rowsWithDraftVisibility;
  const rank = new Map(fieldOrderDraft.value.map((key, index) => [key, index]));
  return rowsWithDraftVisibility.sort((left, right) => (rank.get(left.fieldKey) ?? 9999) - (rank.get(right.fieldKey) ?? 9999));
});

watch(contractModeBaseFieldRows, (rows) => {
  const keys = rows.map((row) => row.fieldKey);
  if (!isContractFieldOrderEditable.value || !keys.length) {
    fieldOrderDraft.value = [];
    fieldVisibilityBase.value = {};
    fieldGroupBase.value = {};
    fieldGroupSavedBase.value = {};
    formLayoutColumnsBase.value = 3;
    formLayoutColumnsDraft.value = 3;
    formLayoutColumnsConfigured.value = false;
    groupVisibilityBase.value = {};
    Object.keys(groupVisibilityDraft).forEach((key) => delete groupVisibilityDraft[key]);
    groupColumnsBase.value = {};
    Object.keys(groupColumnsDraft).forEach((key) => delete groupColumnsDraft[key]);
    fieldSizeBase.value = {};
    Object.keys(fieldSizeDraft).forEach((key) => delete fieldSizeDraft[key]);
    formLayoutDirty.value = false;
    Object.keys(groupLayoutDirtyKeys).forEach((key) => delete groupLayoutDirtyKeys[key]);
    Object.keys(fieldLayoutDirtyKeys).forEach((key) => delete fieldLayoutDirtyKeys[key]);
    lowCodeFormLayoutBase.value = [];
    Object.keys(fieldGroupDraft).forEach((key) => delete fieldGroupDraft[key]);
    Object.keys(fieldMoveTargetDraft).forEach((key) => delete fieldMoveTargetDraft[key]);
    return;
  }
  if (!fieldOrderDraft.value.length) {
    fieldOrderDraft.value = [...keys];
    return;
  }
  const inRows = new Set(keys);
  const kept = fieldOrderDraft.value.filter((key) => inRows.has(key));
  const missing = keys.filter((key) => !kept.includes(key));
  fieldOrderDraft.value = [...kept, ...missing];
  const nextVisibilityBase = { ...fieldVisibilityBase.value };
  rows.forEach((row) => {
    const selected = row.actions.find((action) => Boolean(action.checked));
    if (!selected) return;
    const visible = selected.value === 'show';
    if (!Object.prototype.hasOwnProperty.call(nextVisibilityBase, row.fieldKey)) {
      nextVisibilityBase[row.fieldKey] = visible;
    }
    if (!Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, row.fieldKey)) {
      fieldVisibilityDraft[row.fieldKey] = visible;
    }
  });
  fieldVisibilityBase.value = nextVisibilityBase;
}, { immediate: true });

watch(isContractFieldOrderEditable, (enabled) => {
  if (!enabled) {
    lowCodeContractLoaded.value = false;
    selectedFormSettingsFieldKey.value = '';
    selectedFormSettingsFieldLabel.value = '';
    selectedFormSettingsFieldGroupTitleDraft.value = '';
    fieldVisibilityDirty.value = false;
    formConfigAuditResult.value = null;
    return;
  }
  formSettingsActiveTab.value = 'fields';
  syncFieldOrderDraftWithDesignKeys();
  void loadLowCodeContractList();
  void hydrateLowCodeDraftFromContract();
  void refreshLowCodeFormLayoutBase();
}, { immediate: true });

watch(
  () => [v2ContractStore.value, contract.value, isContractFieldOrderEditable.value],
  () => {
    applyRuntimeInferredFormColumns();
  },
  { flush: 'post' },
);

const currentFormDesignFieldKeys = computed(() => {
  const keys = new Set<string>();
  contractModeBaseFieldRows.value.forEach((row) => {
    if (row.fieldKey) keys.add(row.fieldKey);
  });
  nativeFormDesignFieldKeys.value.forEach((fieldKey) => {
    if (fieldKey) keys.add(fieldKey);
  });
  return Array.from(keys);
});

const currentFormOrderedFieldKeys = computed(() => {
  const baseKeys = currentFormDesignFieldKeys.value;
  if (!fieldOrderDraft.value.length) return baseKeys;
  const baseSet = new Set(baseKeys);
  const ordered = fieldOrderDraft.value.filter((fieldKey) => baseSet.has(fieldKey));
  const missing = baseKeys.filter((fieldKey) => !ordered.includes(fieldKey));
  return [...ordered, ...missing];
});

const selectedFormSettingsOrderTargetOptions = computed(() => {
  const selectedFieldKey = selectedFormSettingsFieldKey.value;
  return currentFormOrderedFieldKeys.value
    .filter((fieldKey) => fieldKey && fieldKey !== selectedFieldKey)
    .map((fieldKey) => ({
      fieldKey,
      label: formDesignFieldLabel(fieldKey),
    }));
});

watch([selectedFormSettingsFieldKey, selectedFormSettingsOrderTargetOptions], () => {
  if (!selectedFormSettingsFieldKey.value) {
    selectedFormSettingsOrderTargetKey.value = '';
    return;
  }
  const options = selectedFormSettingsOrderTargetOptions.value;
  if (!options.length) {
    selectedFormSettingsOrderTargetKey.value = '';
    return;
  }
  if (!options.some((option) => option.fieldKey === selectedFormSettingsOrderTargetKey.value)) {
    const selectedIndex = currentFormOrderedFieldKeys.value.indexOf(selectedFormSettingsFieldKey.value);
    const preferred = currentFormOrderedFieldKeys.value[selectedIndex + 1]
      || currentFormOrderedFieldKeys.value[selectedIndex - 1]
      || options[0].fieldKey;
    selectedFormSettingsOrderTargetKey.value = options.some((option) => option.fieldKey === preferred)
      ? preferred
      : options[0].fieldKey;
  }
}, { immediate: true });

function syncFieldOrderDraftWithDesignKeys(rawKeys = currentFormDesignFieldKeys.value) {
  if (!isContractFieldOrderEditable.value) return;
  const keys = Array.from(new Set(rawKeys.map((key) => String(key || '').trim()).filter(Boolean)));
  if (!keys.length) return;
  if (!fieldOrderPreviewActive.value) {
    const same = keys.length === fieldOrderDraft.value.length
      && keys.every((key, index) => fieldOrderDraft.value[index] === key);
    if (!same) fieldOrderDraft.value = keys;
    return;
  }
  const keySet = new Set(keys);
  const kept = fieldOrderDraft.value.filter((key) => keySet.has(key));
  const missing = keys.filter((key) => !kept.includes(key));
  fieldOrderDraft.value = [...kept, ...missing];
}

watch(currentFormDesignFieldKeys, (keys) => {
  syncFieldOrderDraftWithDesignKeys(keys);
  if (isContractFieldOrderEditable.value && keys.length && !lowCodeContractLoaded.value) {
    void hydrateLowCodeDraftFromContract();
  }
  if (isContractFieldOrderEditable.value && keys.length) {
    void refreshLowCodeFormLayoutBase();
  }
}, { immediate: true });

const hasFieldOrderChanges = computed(() => {
  if (!fieldOrderPreviewActive.value) return false;
  const rows = currentFormDesignFieldKeys.value;
  if (!rows.length || !fieldOrderDraft.value.length) return false;
  return rows.some((key, index) => fieldOrderDraft.value[index] !== key);
});

const formVisibilityDraftFieldKeys = computed(() => Array.from(new Set([
  ...currentFormDesignFieldKeys.value,
  ...Object.keys(fieldVisibilityDraft),
  ...Object.keys(fieldVisibilityBase.value),
].map((key) => String(key || '').trim()).filter(Boolean))));

const hasFieldVisibilityChanges = computed(() => formVisibilityDraftFieldKeys.value.some((fieldKey) => {
  if (!Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)) return false;
  if (!Object.prototype.hasOwnProperty.call(fieldVisibilityBase.value, fieldKey)) return false;
  return fieldVisibilityDraft[fieldKey] !== fieldVisibilityBase.value[fieldKey];
}));

const hasFieldGroupChanges = computed(() => Object.keys(fieldGroupDraft).some((fieldKey) => {
  const draft = effectiveFieldGroupTitleForDraft(fieldKey);
  const base = normalizeFieldGroupTitle(fieldGroupSavedBase.value[fieldKey] || fieldGroupBase.value[fieldKey]);
  return Boolean(draft) && draft !== base;
}));

function effectiveGroupVisible(title: string) {
  const key = normalizeFieldGroupTitle(title);
  if (!key) return true;
  if (Object.prototype.hasOwnProperty.call(groupVisibilityDraft, key)) return groupVisibilityDraft[key] !== false;
  if (Object.prototype.hasOwnProperty.call(groupVisibilityBase.value, key)) return groupVisibilityBase.value[key] !== false;
  return true;
}

function effectiveGroupColumns(title: string): 1 | 2 | 3 {
  const key = normalizeFieldGroupTitle(title);
  if (!key) return formLayoutColumnsDraft.value;
  return groupColumnsDraft[key] || groupColumnsBase.value[key] || formLayoutColumnsDraft.value;
}

function effectiveFieldSize(fieldKey: string): LowCodeFieldSize {
  const key = String(fieldKey || '').trim();
  if (!key) return 'normal';
  return fieldSizeDraft[key] || fieldSizeBase.value[key] || 'normal';
}

const hasFormLayoutChanges = computed(() => formLayoutDirty.value);

const hasGroupLayoutChanges = computed(() => Object.keys(groupLayoutDirtyKeys).length > 0);

const hasFieldLayoutChanges = computed(() => Object.keys(fieldLayoutDirtyKeys).length > 0);

const hasCurrentFormFieldDraftChanges = computed(() => (
  hasFieldOrderChanges.value
  || hasFieldVisibilityChanges.value
  || hasFieldGroupChanges.value
  || hasFormLayoutChanges.value
  || hasGroupLayoutChanges.value
  || hasFieldLayoutChanges.value
  || fieldVisibilityDirty.value
));

const formConfigOperatorName = computed(() => {
  const user = (session.user || {}) as Record<string, unknown>;
  return String(user.name || user.login || user.email || user.id || '当前用户').trim();
});

const formConfigOperationLogStorageKey = computed(() => {
  const user = (session.user || {}) as Record<string, unknown>;
  return buildFormConfigOperationLogStorageKey({
    db: route.query.db,
    modelName: model.value || route.params.model,
    actionId: actionId.value || route.query.action_id,
    viewId: routeQueryText('view_id') || routeQueryText('viewId'),
    page: routeQueryText('page_label') || routeQueryText('pageLabel') || route.fullPath,
    userId: user.id || user.login || formConfigOperatorName.value,
  });
});

function persistFormConfigOperationLog() {
  if (typeof window === 'undefined') return;
  const key = formConfigOperationLogStorageKey.value;
  if (!key) return;
  try {
    window.sessionStorage.setItem(key, JSON.stringify(formConfigOperationLog.value.slice(0, 50)));
  } catch {
    // ignore session storage failures
  }
}

function hydrateFormConfigOperationLog() {
  if (typeof window === 'undefined') return;
  const key = formConfigOperationLogStorageKey.value;
  if (!key) return;
  try {
    const raw = window.sessionStorage.getItem(key);
    formConfigOperationLog.value = normalizeFormConfigOperationLogEntries(raw ? JSON.parse(raw) : [], formConfigOperatorName.value);
  } catch {
    formConfigOperationLog.value = [];
  }
}

function appendFormConfigOperation(
  action: string,
  summary: string,
  status: FormConfigOperationLogEntry['status'] = 'pending',
) {
  const entry = createFormConfigOperationLogEntry(action, summary, formConfigOperatorName.value, status);
  if (!entry) return;
  formConfigOperationLog.value = appendFormConfigOperationLogEntry(formConfigOperationLog.value, entry);
  persistFormConfigOperationLog();
}

function markPendingFormConfigOperations(status: Extract<FormConfigOperationLogEntry['status'], 'saved' | 'reverted'>) {
  const hasPending = formConfigOperationLog.value.some((entry) => entry.status === 'pending');
  if (!hasPending) return;
  formConfigOperationLog.value = formConfigOperationLog.value.map((entry) => (
    entry.status === 'pending' ? { ...entry, status } : entry
  ));
  persistFormConfigOperationLog();
}

function clearFormConfigOperationLog() {
  formConfigOperationLog.value = [];
  persistFormConfigOperationLog();
}

function formConfigFieldLabelReplacementEntries() {
  const labels = new Map<string, string>();
  const remember = (fieldKey: string, label: string) => {
    const key = String(fieldKey || '').trim();
    const value = String(label || '').trim();
    if (!key || !value || key === value) return;
    labels.set(key, value);
  };
  Object.entries(formConfigFieldLabelCache).forEach(([key, label]) => remember(key, label));
  Object.entries(nativeFormDesignFieldLabels.value).forEach(([key, label]) => remember(key, label));
  activeContractModeFieldRows.value.forEach((row) => remember(row.fieldKey, row.label));
  currentFormDesignFieldKeys.value.forEach((fieldKey) => {
    const key = String(fieldKey || '').trim();
    if (!key || labels.has(key)) return;
    const descriptor = contract.value?.fields?.[key] as Record<string, unknown> | undefined;
    remember(key, String(contractFieldLabel(key) || descriptor?.string || descriptor?.label || '').trim());
  });
  return Array.from(labels.entries()).sort((left, right) => right[0].length - left[0].length);
}

function formatFormConfigOperationSummary(summary: string) {
  return formatFormConfigOperationSummaryText(summary, formConfigFieldLabelReplacementEntries());
}

watch(formConfigOperationLogStorageKey, () => {
  hydrateFormConfigOperationLog();
}, { immediate: true });

function formDesignFieldLabel(fieldKey: string) {
  const key = String(fieldKey || '').trim();
  if (!key) return '';
  const selectedLabel = selectedFormSettingsFieldKey.value === key
    ? String(selectedFormSettingsFieldLabel.value || '').trim()
    : '';
  if (selectedLabel && selectedLabel !== key) return selectedLabel;
  const cachedLabel = String(formConfigFieldLabelCache[key] || '').trim();
  const structuredLabel = String(contractFieldLabel(key) || '').trim();
  const nativeLabel = String(nativeFormDesignFieldLabels.value[key] || '').trim();
  const row = activeContractModeFieldRows.value.find((item) => item.fieldKey === key);
  const rowLabel = String(row?.label || '').trim();
  const descriptor = contract.value?.fields?.[key] as Record<string, unknown> | undefined;
  const descriptorLabel = String(descriptor?.string || descriptor?.label || '').trim();
  if (cachedLabel && cachedLabel !== key) return cachedLabel;
  if (structuredLabel && structuredLabel !== key) return structuredLabel;
  if (nativeLabel && nativeLabel !== key) return nativeLabel;
  if (rowLabel && rowLabel !== key) return rowLabel;
  if (descriptorLabel && descriptorLabel !== key) return descriptorLabel;
  return rowLabel || readableFallbackFieldLabel(key);
}

function rememberFormConfigFieldLabel(fieldKey: string, label: string) {
  const key = String(fieldKey || '').trim();
  const normalizedLabel = String(label || '').trim();
  if (!key || !normalizedLabel || normalizedLabel === key) return;
  formConfigFieldLabelCache[key] = normalizedLabel;
}

const suggestedHiddenFieldRows = computed(() => currentFormDesignFieldKeys.value
  .map((fieldKey) => ({ fieldKey, label: formDesignFieldLabel(fieldKey) }))
  .filter((row) => {
    if (!isSuggestedInternalFormField(row.fieldKey, row.label)) return false;
    return fieldVisibilityDraft[row.fieldKey] !== false;
  }));

watch(hasCurrentFormFieldDraftChanges, (changed) => {
  if (changed) formConfigAuditResult.value = null;
});

function changedFieldVisibilityDraft() {
  return formVisibilityDraftFieldKeys.value.reduce<Record<string, boolean>>((acc, fieldKey) => {
    if (!Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)) return acc;
    if (
      fieldVisibilityDirtyKeys[fieldKey]
      || (
        Object.prototype.hasOwnProperty.call(fieldVisibilityBase.value, fieldKey)
        && fieldVisibilityDraft[fieldKey] !== fieldVisibilityBase.value[fieldKey]
      )
    ) {
      acc[fieldKey] = fieldVisibilityDraft[fieldKey];
    }
    return acc;
  }, {});
}

function changedFieldGroupDraft() {
  return Object.keys(fieldGroupDraft).reduce<Record<string, string>>((acc, fieldKey) => {
    const key = String(fieldKey || '').trim();
    const draft = effectiveFieldGroupTitleForDraft(key);
    const base = normalizeFieldGroupTitle(fieldGroupSavedBase.value[key] || fieldGroupBase.value[key]);
    if (key && draft && draft !== base) acc[key] = draft;
    return acc;
  }, {});
}

function effectiveFieldGroupTitleForDraft(fieldKey: string) {
  const key = String(fieldKey || '').trim();
  if (!key) return '';
  const draft = normalizeFieldGroupTitle(fieldGroupDraft[key]);
  const nativeBase = normalizeFieldGroupTitle(fieldGroupBase.value[key]);
  const savedBase = normalizeFieldGroupTitle(fieldGroupSavedBase.value[key]);
  if (draft && draft !== nativeBase) return draft;
  return savedBase || draft || nativeBase;
}

async function auditCurrentFormConfiguration() {
  if (formConfigAuditBusy.value || busy.value) return;
  const params = lowCodeApplyBaseParams();
  const modelName = String(params.model || model.value || '').trim();
  if (!modelName) return;
  formConfigAuditBusy.value = true;
  try {
    const result = await intentRequest<{
      business_config_form_fields?: unknown[];
      business_config_form_layout_fields?: unknown[];
      has_business_config_form_layout?: boolean;
      layout_matches_fields?: boolean;
      legacy_policy_fields?: unknown[];
      skipped_legacy_policy_fields?: unknown[];
      active_legacy_policy_fields?: unknown[];
      has_conflict?: boolean;
    }>({
      intent: BUSINESS_CONFIG_INTENTS.formAudit,
      params: {
        ...params,
        model: modelName,
        view_type: 'form',
      },
      context: { view: 'form' },
    });
    const normalizeNames = (value: unknown[]) => value
      .map((item) => String(item || '').trim())
      .filter(Boolean);
    formConfigAuditResult.value = {
      businessConfigFormFields: normalizeNames(Array.isArray(result.business_config_form_fields) ? result.business_config_form_fields : []),
      businessConfigFormLayoutFields: normalizeNames(Array.isArray(result.business_config_form_layout_fields) ? result.business_config_form_layout_fields : []),
      hasBusinessConfigFormLayout: Boolean(result.has_business_config_form_layout),
      layoutMatchesFields: Boolean(result.layout_matches_fields),
      legacyPolicyFields: normalizeNames(Array.isArray(result.legacy_policy_fields) ? result.legacy_policy_fields : []),
      skippedLegacyPolicyFields: normalizeNames(Array.isArray(result.skipped_legacy_policy_fields) ? result.skipped_legacy_policy_fields : []),
      activeLegacyPolicyFields: normalizeNames(Array.isArray(result.active_legacy_policy_fields) ? result.active_legacy_policy_fields : []),
      hasConflict: Boolean(result.has_conflict),
    };
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '表单配置检查失败';
    status.value = 'error';
  } finally {
    formConfigAuditBusy.value = false;
  }
}

const showCurrentFormFieldConfigScope = computed(() => isContractFieldOrderEditable.value);
const showLowCodeTechnicalDetails = computed(() => {
  if (activeContractMode.value !== BUSINESS_CONFIG_MODES.lowCode) return showHud.value;
  const hudFlag = routeQueryText('hud').toLowerCase();
  const surface = routeQueryText('surface').toLowerCase();
  return hudFlag === '1' || hudFlag === 'true' || surface === 'hud';
});

const currentFormConfigPageLabel = computed(() => normalizeConfigPageLabel(
  routeQueryText('page_label')
  || routeQueryText('pageLabel')
  || currentBusinessCategoryLabel.value
  || pageTitle.value
  || '当前表单',
));

const formFieldConfigScope = computed(() => buildFormFieldConfigScope(currentFormConfigPageLabel.value));

const formConfigAuditSummary = computed(() => {
  return formatFormConfigAuditSummary(formConfigAuditResult.value, showLowCodeTechnicalDetails.value);
});

const selectedFormSettingsFieldRow = computed(() => {
  const fieldKey = selectedFormSettingsFieldKey.value;
  if (!fieldKey) return undefined;
  const row = activeContractModeFieldRows.value.find((item) => item.fieldKey === fieldKey);
  if (!row) {
    const label = selectedFormSettingsFieldLabel.value || fieldKey;
    const visible = Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)
      ? fieldVisibilityDraft[fieldKey]
      : true;
    return {
      fieldKey,
      label,
      actions: [
        {
          key: `${fieldKey}:show`,
          label: '显示',
          value: 'show',
          checked: visible,
          disabled: busy.value,
          title: '在当前页面显示这个字段',
          raw: {},
        },
        {
          key: `${fieldKey}:hide`,
          label: '隐藏',
          value: 'hide',
          checked: !visible,
          disabled: busy.value,
          title: '在当前页面隐藏这个字段',
          raw: {},
        },
      ],
    };
  }
  return {
    ...row,
    label: selectedFormSettingsFieldLabel.value || row.label || fieldKey,
  };
});

const nativeFieldStructureGroups = computed<Array<{ key: string; title: string; fieldKeys: string[] }>>(() => {
  const lowCodeLayout = lowCodeFormLayoutBase.value;
  const useLowCodeLayout = isContractFieldOrderEditable.value && layoutHasReadableFieldGroups(lowCodeLayout);
  const legacyLayout = Array.isArray(contract.value?.views?.form?.layout)
    ? contract.value?.views?.form?.layout as unknown as NativeFormLayoutNode[]
    : [];
  const storeContainers = resolveContractV2ContainerTree(v2ContractStore.value);
  const v2 = storeContainers.length ? null : resolveUnifiedPageContractV2(contract.value);
  const containers = storeContainers.length
    ? storeContainers
    : (Array.isArray(v2?.layoutContract?.containerTree) ? v2.layoutContract.containerTree : []);
  const baseLayout = useLowCodeLayout
    ? mergeLowCodeLayoutWithRuntimeGroupShells(lowCodeLayout, runtimeNativeFormLayoutNodes())
    : (isContractFieldOrderEditable.value && legacyLayout.length
      ? legacyLayout
      : (containers.length
        ? normalizeContractV2ContainersForNativeForm(containers as unknown as ContractV2Container[])
        : legacyLayout));
  return collectNativeFieldStructureGroups(baseLayout as NativeLayoutLikeNode[]);
});

watch(nativeFieldStructureGroups, (groups) => {
  const nextBase: Record<string, string> = {};
  groups.forEach((group) => {
    const title = normalizeFieldGroupTitle(group.title || '主表区域');
    group.fieldKeys.forEach((fieldKey) => {
      if (fieldKey && !nextBase[fieldKey]) nextBase[fieldKey] = title;
    });
  });
  const preservedBase = Object.entries(fieldGroupBase.value).reduce<Record<string, string>>((acc, [fieldKey, title]) => {
    const key = String(fieldKey || '').trim();
    const normalized = normalizeFieldGroupTitle(title);
    if (key && isReadableFieldGroupTitle(normalized)) acc[key] = normalized;
    return acc;
  }, {});
  fieldGroupBase.value = { ...nextBase, ...preservedBase };
  currentFormDesignFieldKeys.value.forEach((fieldKey) => {
    if (!fieldKey) return;
    const title = fieldGroupBase.value[fieldKey];
    if (title && (!Object.prototype.hasOwnProperty.call(fieldGroupDraft, fieldKey) || !isReadableFieldGroupTitle(fieldGroupDraft[fieldKey]))) {
      fieldGroupDraft[fieldKey] = title;
    }
  });
}, { immediate: true });

const currentFormDesignFieldCount = computed(() => {
  if (activeContractModeFieldRows.value.length) return activeContractModeFieldRows.value.length;
  return nativeFieldStructureGroups.value.reduce((total, group) => total + group.fieldKeys.length, 0);
});

const currentFormGroupOptions = computed(() => {
  return buildCurrentFormGroupOptions({
    nativeGroups: nativeFieldStructureGroups.value,
    runtimeGroupTitles: collectNativeLayoutGroupTitles(runtimeNativeFormLayoutNodes()),
    fieldKeys: currentFormDesignFieldKeys.value,
    resolveDraftGroupTitle: effectiveFieldGroupTitleForDraft,
  });
});

const formDesignerGroupNavigatorItems = computed(() => {
  return buildFormDesignerGroupNavigatorItems({
    nativeGroups: nativeFieldStructureGroups.value,
    fieldKeys: currentFormDesignFieldKeys.value,
    selectedGroupTitle: selectedFormSettingsFieldGroupTitle.value,
    resolveDraftGroupTitle: effectiveFieldGroupTitleForDraft,
  });
});

const formDesignerFieldSearchQuery = computed(() => String(formDesignerFieldSearchText.value || '').trim().toLowerCase());

const formDesignerSearchableFieldRows = computed(() => {
  return buildFormDesignerSearchableFieldRows({
    orderedFieldKeys: currentFormOrderedFieldKeys.value,
    fallbackFieldKeys: currentFormDesignFieldKeys.value,
    nativeGroups: nativeFieldStructureGroups.value,
    resolveDraftGroupTitle: effectiveFieldGroupTitleForDraft,
    resolveFieldLabel: formDesignFieldLabel,
  });
});

const formDesignerFilteredFieldRows = computed(() => {
  return filterFormDesignerFieldRows(formDesignerSearchableFieldRows.value, formDesignerFieldSearchQuery.value);
});

const selectedFormSettingsFieldGroupTitle = computed(() => {
  return resolveSelectedFormSettingsFieldGroupTitle({
    fieldKey: selectedFormSettingsFieldKey.value,
    draftGroupTitle: effectiveFieldGroupTitleForDraft(selectedFormSettingsFieldKey.value),
    nativeGroups: nativeFieldStructureGroups.value,
    fallbackDraftTitle: selectedFormSettingsFieldGroupTitleDraft.value,
  });
});

const selectedFormSettingsGroupVisible = computed(() => effectiveGroupVisible(selectedFormSettingsFieldGroupTitle.value));
const selectedFormSettingsGroupColumns = computed(() => effectiveGroupColumns(selectedFormSettingsFieldGroupTitle.value));
const selectedFormSettingsFieldSize = computed(() => effectiveFieldSize(selectedFormSettingsFieldKey.value));

watch(selectedFormSettingsFieldGroupTitle, (title) => {
  selectedFormSettingsFieldGroupTitleEdit.value = title;
});

function syncLayoutDraftFromFormSpec(formSpec: Record<string, unknown>) {
  const runtimeColumns = inferLowCodeLayoutColumns(runtimeNativeFormLayoutNodes()) || inferLowCodeLayoutColumns(rawNativeFormLayoutNodes.value) || 3;
  const next = extractLowCodeLayoutDraftState(formSpec, runtimeColumns);
  formLayoutColumnsConfigured.value = next.columnsConfigured;
  formLayoutColumnsBase.value = next.columns;
  if (!formLayoutDirty.value) {
    formLayoutColumnsDraft.value = next.columns;
  }
  groupVisibilityBase.value = next.groupVisible;
  if (!Object.keys(groupLayoutDirtyKeys).length) {
    Object.keys(groupVisibilityDraft).forEach((key) => delete groupVisibilityDraft[key]);
    Object.entries(next.groupVisible).forEach(([key, value]) => {
      groupVisibilityDraft[key] = value;
    });
  }
  groupColumnsBase.value = next.groupColumns;
  if (!Object.keys(groupLayoutDirtyKeys).length) {
    Object.keys(groupColumnsDraft).forEach((key) => delete groupColumnsDraft[key]);
    Object.entries(next.groupColumns).forEach(([key, value]) => {
      groupColumnsDraft[key] = value;
    });
  }
  fieldSizeBase.value = next.fieldSize;
  if (!Object.keys(fieldLayoutDirtyKeys).length) {
    Object.keys(fieldSizeDraft).forEach((key) => delete fieldSizeDraft[key]);
    Object.entries(next.fieldSize).forEach(([key, value]) => {
      fieldSizeDraft[key] = value;
    });
  }
}

function applyRuntimeInferredFormColumns() {
  if (!isContractFieldOrderEditable.value || formLayoutColumnsConfigured.value || formLayoutDirty.value) return;
  const runtimeColumns = inferLowCodeLayoutColumns(runtimeNativeFormLayoutNodes());
  if (!runtimeColumns || runtimeColumns === formLayoutColumnsBase.value) return;
  formLayoutColumnsBase.value = runtimeColumns;
  formLayoutColumnsDraft.value = runtimeColumns;
  Object.keys(groupColumnsDraft).forEach((key) => delete groupColumnsDraft[key]);
  groupColumnsBase.value = {};
}

async function hydrateLowCodeDraftFromContract() {
  if (!isContractFieldOrderEditable.value || lowCodeContractLoaded.value || lowCodeContractHydrating.value) return;
  const modelName = String(model.value || '').trim();
  if (!modelName) return;
  let hydrated = false;
  lowCodeContractHydrating.value = true;
  try {
    const base = lowCodeApplyBaseParams();
    const scopedName = lowCodeScopedContractName(modelName, base);
    const listResult = await intentRequest<{
      items?: Array<{ name?: string }>;
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractList,
      params: { ...base, model: modelName, view_type: 'form' },
    }).catch(() => null);
    const availableNames = new Set((Array.isArray(listResult?.items) ? listResult?.items || [] : [])
      .map((row) => String(row?.name || '').trim())
      .filter(Boolean));
    const contractName = availableNames.has(scopedName) ? scopedName : '';
    if (!contractName) return;
    const res = await intentRequest<{
      contract_json?: {
        objects?: Array<{ name?: string; fields?: Array<{ name?: string; visible?: boolean; order?: number }> }>;
      }
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractGet,
      params: { ...base, model: modelName, name: contractName, view_type: 'form' },
    }).catch(() => null);
    if (!res) return;
    const viewOrchestration = res?.contract_json && typeof res.contract_json === 'object' && !Array.isArray(res.contract_json)
      ? (res.contract_json as { view_orchestration?: Record<string, unknown> }).view_orchestration || {}
      : {};
    const orchestrationViews = viewOrchestration && typeof viewOrchestration === 'object' && !Array.isArray(viewOrchestration)
      ? ((viewOrchestration as Record<string, unknown>).views || {}) as Record<string, unknown>
      : {};
    const formSpec = orchestrationViews.form && typeof orchestrationViews.form === 'object' && !Array.isArray(orchestrationViews.form)
      ? orchestrationViews.form as Record<string, unknown>
      : {};
    const formFields = Array.isArray(formSpec.fields) ? formSpec.fields as Array<Record<string, unknown>> : [];
    lowCodeFormLayoutBase.value = Array.isArray(formSpec.layout)
      ? formSpec.layout as unknown as NativeFormLayoutNode[]
      : [];
    syncLayoutDraftFromFormSpec(formSpec);
    if (formFields.length) {
      const orderNames = formFields
        .map((row) => ({ name: String(row?.name || row?.field || '').trim(), sequence: Number(row?.sequence || row?.order || 0) }))
        .filter((row) => row.name)
        .sort((a, b) => a.sequence - b.sequence)
        .map((row) => row.name);
      if (orderNames.length) fieldOrderDraft.value = orderNames;
      formFields.forEach((row) => {
        const key = String(row?.name || row?.field || '').trim();
        if (!key) return;
        const visible = row?.visible !== false;
        const rawGroupTitle = row?.group_title || row?.groupTitle || row?.section_title || row?.sectionTitle;
        const groupTitle = isReadableFieldGroupTitle(rawGroupTitle) ? normalizeFieldGroupTitle(rawGroupTitle) : '';
        fieldVisibilityBase.value = { ...fieldVisibilityBase.value, [key]: visible };
        fieldVisibilityDraft[key] = visible;
        if (groupTitle) {
          fieldGroupSavedBase.value = { ...fieldGroupSavedBase.value, [key]: groupTitle };
          fieldGroupBase.value = { ...fieldGroupBase.value, [key]: groupTitle };
          fieldGroupDraft[key] = groupTitle;
        }
      });
    }
    lowCodeLayoutDraft.value = collectLowCodeLayoutFromViewOrchestration(orchestrationViews, modelName);
    hydrated = true;
  } catch {
    // ignore low-code contract hydrate failure in form runtime
  } finally {
    if (hydrated) lowCodeContractLoaded.value = true;
    lowCodeContractHydrating.value = false;
  }
}

async function refreshLowCodeFormLayoutBase() {
  if (!isContractFieldOrderEditable.value || lowCodeContractHydrating.value) return;
  const modelName = String(model.value || '').trim();
  if (!modelName) return;
  try {
    const base = lowCodeApplyBaseParams();
    const scopedName = lowCodeScopedContractName(modelName, base);
    const res = await intentRequest<{
      contract_json?: { view_orchestration?: Record<string, unknown> }
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractGet,
      params: { ...base, model: modelName, name: scopedName, view_type: 'form' },
    }).catch(() => null);
    const viewOrchestration = res?.contract_json && typeof res.contract_json === 'object' && !Array.isArray(res.contract_json)
      ? (res.contract_json as { view_orchestration?: Record<string, unknown> }).view_orchestration || {}
      : {};
    const orchestrationViews = viewOrchestration && typeof viewOrchestration === 'object' && !Array.isArray(viewOrchestration)
      ? ((viewOrchestration as Record<string, unknown>).views || {}) as Record<string, unknown>
      : {};
    const formSpec = orchestrationViews.form && typeof orchestrationViews.form === 'object' && !Array.isArray(orchestrationViews.form)
      ? orchestrationViews.form as Record<string, unknown>
      : {};
    lowCodeFormLayoutBase.value = Array.isArray(formSpec.layout)
      ? formSpec.layout as unknown as NativeFormLayoutNode[]
      : [];
    syncLayoutDraftFromFormSpec(formSpec);
    const formFields = Array.isArray(formSpec.fields) ? formSpec.fields as Array<Record<string, unknown>> : [];
    formFields.forEach((row) => {
      const key = String(row?.name || row?.field || '').trim();
      if (!key) return;
      const rawGroupTitle = row?.group_title || row?.groupTitle || row?.section_title || row?.sectionTitle;
      const groupTitle = isReadableFieldGroupTitle(rawGroupTitle) ? normalizeFieldGroupTitle(rawGroupTitle) : '';
      if (!groupTitle) return;
      const previousDraft = normalizeFieldGroupTitle(fieldGroupDraft[key]);
      const previousBase = normalizeFieldGroupTitle(fieldGroupBase.value[key]);
      const shouldSyncDraft = !previousDraft
        || previousDraft === previousBase
        || previousDraft.startsWith('默认分组');
      fieldGroupSavedBase.value = { ...fieldGroupSavedBase.value, [key]: groupTitle };
      fieldGroupBase.value = { ...fieldGroupBase.value, [key]: groupTitle };
      if (shouldSyncDraft) {
        fieldGroupDraft[key] = groupTitle;
      }
    });
  } catch {
    // Form config still works from runtime layout if the saved contract cannot be read.
  }
}

async function loadLowCodeContractList() {
  if (!isContractFieldOrderEditable.value) return;
  const modelName = String(model.value || '').trim();
  if (!modelName) return;
  try {
    const base = lowCodeApplyBaseParams();
    const result = await intentRequest<{
      items?: Array<{ id?: number; name?: string; model?: string; status?: string; version_no?: number }>;
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractList,
      params: { ...base, model: modelName, view_type: 'form' },
    });
    const items = Array.isArray(result?.items) ? result.items || [] : [];
    lowCodeContractList.value = items.map((row) => ({
      id: Number(row?.id || 0),
      name: String(row?.name || '').trim(),
      model: String(row?.model || '').trim(),
      status: String(row?.status || 'draft').trim() || 'draft',
      version_no: Number(row?.version_no || 1),
    })).filter((row) => row.name);
    if (lowCodeSelectedContractName.value && !lowCodeContractList.value.some((row) => row.name === lowCodeSelectedContractName.value)) {
      lowCodeSelectedContractName.value = '';
    }
    if (!lowCodeSelectedContractName.value && lowCodeContractList.value.length) {
      lowCodeSelectedContractName.value = lowCodeContractList.value[0].name;
    }
  } catch {
    lowCodeContractList.value = [];
  }
}

async function switchLowCodeContractByName() {
  const name = String(lowCodeSelectedContractName.value || '').trim();
  const modelName = String(model.value || '').trim();
  if (!name || !modelName) return;
  try {
    const base = lowCodeApplyBaseParams();
    const res = await intentRequest<{
      contract_json?: {
        view_orchestration?: Record<string, unknown>;
      }
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractGet,
      params: { ...base, model: modelName, name, view_type: 'form' },
    });
    lowCodeContractLoaded.value = false;
    const json = res?.contract_json;
    if (!json || typeof json !== 'object' || Array.isArray(json)) return;
    const viewOrchestration = (json as { view_orchestration?: Record<string, unknown> }).view_orchestration || {};
    const orchestrationViews = viewOrchestration && typeof viewOrchestration === 'object' && !Array.isArray(viewOrchestration)
      ? ((viewOrchestration as Record<string, unknown>).views || {}) as Record<string, unknown>
      : {};
    const formSpec = orchestrationViews.form && typeof orchestrationViews.form === 'object' && !Array.isArray(orchestrationViews.form)
      ? orchestrationViews.form as Record<string, unknown>
      : {};
    const formFields = Array.isArray(formSpec.fields) ? formSpec.fields as Array<Record<string, unknown>> : [];
    lowCodeFormLayoutBase.value = Array.isArray(formSpec.layout)
      ? formSpec.layout as unknown as NativeFormLayoutNode[]
      : [];
    syncLayoutDraftFromFormSpec(formSpec);
    if (formFields.length) {
      const orderNames = formFields
        .map((row) => ({ name: String(row?.name || row?.field || '').trim(), sequence: Number(row?.sequence || row?.order || 0) }))
        .filter((row) => row.name)
        .sort((a, b) => a.sequence - b.sequence)
        .map((row) => row.name);
      if (orderNames.length) fieldOrderDraft.value = orderNames;
      formFields.forEach((row) => {
        const key = String(row?.name || row?.field || '').trim();
        if (!key) return;
        const visible = row?.visible !== false;
        const rawGroupTitle = row?.group_title || row?.groupTitle || row?.section_title || row?.sectionTitle;
        const groupTitle = isReadableFieldGroupTitle(rawGroupTitle) ? normalizeFieldGroupTitle(rawGroupTitle) : '';
        fieldVisibilityBase.value = { ...fieldVisibilityBase.value, [key]: visible };
        fieldVisibilityDraft[key] = visible;
        if (groupTitle) {
          fieldGroupSavedBase.value = { ...fieldGroupSavedBase.value, [key]: groupTitle };
          fieldGroupBase.value = { ...fieldGroupBase.value, [key]: groupTitle };
          fieldGroupDraft[key] = groupTitle;
        }
      });
    }
    lowCodeLayoutDraft.value = collectLowCodeLayoutFromViewOrchestration(orchestrationViews, modelName);
  } catch {
    // ignore
  }
}

async function publishSelectedLowCodeContract() {
  const name = String(lowCodeSelectedContractName.value || '').trim();
  const modelName = String(model.value || '').trim();
  if (!name || !modelName || busy.value) return;
  busyKind.value = 'action';
  try {
    const base = lowCodeApplyBaseParams();
    await intentRequest({
      intent: BUSINESS_CONFIG_INTENTS.contractPublish,
      params: { ...base, name, model: modelName, view_type: 'form' },
    });
    contractModeFeedback.value = '配置版本已发布，刷新页面后按新配置生效';
    await loadLowCodeContractList();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '配置版本发布失败';
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

async function rollbackSelectedLowCodeContract() {
  const name = String(lowCodeSelectedContractName.value || '').trim();
  const modelName = String(model.value || '').trim();
  if (!name || !modelName || busy.value) return;
  busyKind.value = 'action';
  try {
    const base = lowCodeApplyBaseParams();
    await intentRequest({
      intent: BUSINESS_CONFIG_INTENTS.contractRollback,
      params: { ...base, name, model: modelName, view_type: 'form' },
    });
    contractModeFeedback.value = '配置版本已回滚到上一版并发布生效';
    await loadLowCodeContractList();
    await switchLowCodeContractByName();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '配置版本回滚失败';
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

function collectLowCodeLayoutFromViewOrchestration(views: Record<string, unknown>, modelName: string) {
  const out: Array<{ section: 'form' | 'list' | 'kanban'; object: string; field: string }> = [];
  const collect = (section: 'form' | 'list' | 'kanban', viewKey: string, rowKey: string) => {
    const spec = views[viewKey] && typeof views[viewKey] === 'object' && !Array.isArray(views[viewKey])
      ? views[viewKey] as Record<string, unknown>
      : {};
    const rows = Array.isArray(spec[rowKey]) ? spec[rowKey] as unknown[] : [];
    rows.forEach((row) => {
      const item = row && typeof row === 'object' ? row as Record<string, unknown> : {};
      const field = String(item.name || item.field || '').trim();
      if (field) out.push({ section, object: modelName, field });
    });
  };
  collect('form', 'form', 'fields');
  collect('list', 'tree', 'columns');
  collect('list', 'list', 'columns');
  collect('kanban', 'kanban', 'fields');
  return out;
}

function buildLowCodeViewOrchestration() {
  const availableFields = contract.value?.fields || {};
  const fieldLabel = (name: string) => effectiveLowCodeFieldLabel(name, availableFields[name]);
  const fieldGroupTitle = (name: string) => (
    effectiveFieldGroupTitleForDraft(name)
  );
  const sectionFields = (section: 'form' | 'list' | 'kanban') => lowCodeLayoutDraft.value
    .filter((row) => row.section === section)
    .map((row) => String(row.field || '').trim())
    .filter((name) => name && availableFields[name]);
  const formDraftNames = fieldOrderDraft.value.filter((name) => availableFields[name]);
  const formNames = isContractFieldOrderEditable.value && formDraftNames.length
    ? formDraftNames
    : (sectionFields('form').length ? sectionFields('form') : formDraftNames);
  const listNames = sectionFields('list');
  const kanbanNames = sectionFields('kanban');
  const views: Record<string, unknown> = {};
  if (formNames.length) {
    const groupBuckets = new Map<string, string[]>();
    formNames.forEach((name) => {
      const title = fieldGroupTitle(name);
      const key = title || '业务配置字段';
      if (!groupBuckets.has(key)) groupBuckets.set(key, []);
      groupBuckets.get(key)?.push(name);
    });
    const layoutGroups = Array.from(groupBuckets.entries())
      .filter(([title]) => effectiveGroupVisible(title))
      .map(([title, names]) => ({
      type: 'group',
      string: title,
      visible: effectiveGroupVisible(title),
      columns: effectiveGroupColumns(title),
      children: names.map((name) => ({
        type: 'field',
        name,
        ...(lowCodeFieldSizeClass(effectiveFieldSize(name)) ? {
          class: lowCodeFieldSizeClass(effectiveFieldSize(name)),
          field_size: effectiveFieldSize(name),
        } : {}),
      })),
    }));
    views.form = {
      columns: formLayoutColumnsDraft.value,
      fields: formNames.map((name, index) => {
        const groupTitle = fieldGroupTitle(name);
        const fieldSize = effectiveFieldSize(name);
        const fieldClass = lowCodeFieldSizeClass(fieldSize);
        return {
          name,
          label: fieldLabel(name),
          visible: fieldVisibilityDraft[name] !== false && effectiveGroupVisible(groupTitle || '业务配置字段'),
          sequence: (index + 1) * 10,
          ...(groupTitle ? { group_title: groupTitle } : {}),
          ...(fieldClass ? { class: fieldClass, field_size: fieldSize } : {}),
        };
      }),
      sections: Array.from(groupBuckets.entries()).map(([title, names], index) => ({
        name: `business_config_section_${index + 1}`,
        title,
        visible: effectiveGroupVisible(title),
        columns: effectiveGroupColumns(title),
        sequence: (index + 1) * 10,
        fields: [...names],
      })),
      layout: layoutGroups,
    };
  }
  if (listNames.length) {
    views.tree = {
      columns: listNames.map((name, index) => ({
        name,
        label: fieldLabel(name),
        visible: true,
        sequence: (index + 1) * 10,
      })),
    };
  }
  if (kanbanNames.length) {
    views.kanban = {
      fields: kanbanNames.map((name, index) => ({
        name,
        label: fieldLabel(name),
        visible: true,
        sequence: (index + 1) * 10,
      })),
      slots: { primary: kanbanNames.slice(0, 3) },
    };
  }
  return Object.keys(views).length ? { views } : undefined;
}

function lowCodeLayoutFieldLabel(name: string) {
  const targetName = String(name || '').trim();
  if (!targetName) return '';
  const walk = (nodes: NativeFormLayoutNode[]): string => {
    for (const node of nodes) {
      if (!node || typeof node !== 'object') continue;
      const nodeType = String(node.type || (node as { containerType?: string }).containerType || '').trim().toLowerCase();
      const nodeName = String(node.name || '').trim();
      if (nodeType === 'field' && nodeName === targetName) {
        const nodeRecord = node as Record<string, unknown>;
        const fieldInfo = nativeNodeFieldInfo(nodeRecord);
        const label = String(
          nodeRecord.string
          || nodeRecord.label
          || fieldInfo.string
          || fieldInfo.label
          || '',
        ).trim();
        if (label) return label;
      }
      for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
        const children = node[key];
        if (!Array.isArray(children)) continue;
        const found = walk(children as NativeFormLayoutNode[]);
        if (found) return found;
      }
    }
    return '';
  };
  return walk(rawNativeFormLayoutNodes.value) || walk(lowCodeFormLayoutBase.value);
}

function effectiveLowCodeFieldLabel(name: string, descriptor?: FieldDescriptor) {
  const fieldName = String(name || '').trim();
  return String(
    contractFieldLabel(fieldName)
    || lowCodeLayoutFieldLabel(fieldName)
    || descriptor?.string
    || readableFallbackFieldLabel(fieldName),
  ).trim() || readableFallbackFieldLabel(fieldName);
}

function normalizeLowCodeApplyParams(raw: Record<string, unknown>): Record<string, unknown> {
  const params = { ...raw };
  for (const key of ['action_id', 'actionId', 'view_id', 'viewId']) {
    if (!(key in params)) continue;
    const numeric = Number(params[key] || 0);
    params[key] = Number.isFinite(numeric) && numeric >= 0 ? Math.trunc(numeric) : 0;
  }
  return params;
}

function lowCodeScopedContractName(modelName: string, params: Record<string, unknown>) {
  const actionId = Number(params.action_id || params.actionId || 0);
  const viewId = Number(params.view_id || params.viewId || 0);
  return `view_orchestration:${modelName}:form:action:${Number.isFinite(actionId) ? Math.trunc(actionId) : 0}:view:${Number.isFinite(viewId) ? Math.trunc(viewId) : 0}`;
}

const isQuickSubmitDisabled = computed(() => {
  if (busy.value) return true;
  if (!canSave.value) return true;
  if (isProjectQuickIntakeMode.value) return !quickRequiredReady.value;
  return Boolean(recordId.value) && !hasChanges.value;
});
const primaryFormActionDisabled = computed(() => {
  if (busy.value) return true;
  if (!canSave.value) return true;
  if (primaryCreateFooterAction.value) return false;
  if (primarySubmitAction.value) return false;
  return isQuickSubmitDisabled.value;
});
const draftSaveDisabled = computed(() => {
  if (busy.value) return true;
  if (!canSave.value) return true;
  return Boolean(recordId.value) && !hasChanges.value;
});
const isStandardCreateDisabled = computed(() => {
  if (busy.value) return true;
  if (!canSave.value) return true;
  if (isProjectStandardIntakeMode.value) return !standardCreateReady.value;
  return false;
});

const isIntakeCreateDisabled = computed(() => {
  if (!isProjectIntakeCreateMode.value) return false;
  if (isProjectQuickIntakeMode.value) return isQuickSubmitDisabled.value;
  return isStandardCreateDisabled.value;
});

function persistIntakeAutosave() {
  const key = intakeAutosaveKey.value;
  if (!key || recordId.value) return;
  try {
    const payload = {
      saved_at: Date.now(),
      values: {
        name: formData.name ?? '',
        manager_id: formData.manager_id ?? false,
        owner_id: formData.owner_id ?? false,
        project_type_id: formData.project_type_id ?? false,
        project_category_id: formData.project_category_id ?? false,
        location: formData.location ?? '',
        start_date: formData.start_date ?? '',
        end_date: formData.end_date ?? '',
      },
    };
    window.localStorage.setItem(key, JSON.stringify(payload));
  } catch {
    // ignore storage exceptions
  }
}

function restoreIntakeAutosave() {
  const key = intakeAutosaveKey.value;
  if (!key || recordId.value) return;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return;
    const parsed = JSON.parse(raw) as { values?: Record<string, unknown> };
    const values = parsed?.values;
    if (!values || typeof values !== 'object') return;
    const fields = [
      'name',
      'manager_id',
      'owner_id',
      'project_type_id',
      'project_category_id',
      'location',
      'start_date',
      'end_date',
    ];
    fields.forEach((field) => {
      if (!(field in values)) return;
      const nextValue = values[field];
      if (nextValue === null || nextValue === undefined || nextValue === '') return;
      formData[field] = nextValue as never;
    });
  } catch {
    // ignore malformed storage payload
  }
}

function clearIntakeAutosave() {
  const key = intakeAutosaveKey.value;
  if (!key) return;
  try {
    window.localStorage.removeItem(key);
  } catch {
    // ignore storage exceptions
  }
}

const contractMetaLine = computed(() => {
  if (!contract.value) return '';
  const mode = String(contractMeta.value?.contract_mode || '-');
  const surface = String((contract.value as Record<string, unknown>)?.contract_surface || contractMeta.value?.contract_surface || '-');
  const viewType = String(contract.value.head?.view_type || contract.value.view_type || '-');
  const filters = Array.isArray(contract.value.search?.filters) ? contract.value.search.filters.length : 0;
  const transitions = Array.isArray(contract.value.workflow?.transitions) ? contract.value.workflow.transitions.length : 0;
  const profileLabels: Record<string, string> = {
    create: '新建',
    edit: '编辑',
    readonly: '只读',
  };
  const permissionLabels = [
    rights.value.read ? '可查看' : '',
    rights.value.write ? '可编辑' : '',
    rights.value.create ? '可新建' : '',
    rights.value.unlink ? '可删除' : '',
  ].filter(Boolean);
  const valueLabel = (value: string, labels: Record<string, string>) => {
    const normalized = String(value || '').trim().toLowerCase();
    if (!normalized || normalized === '-') return '未配置';
    return labels[normalized] || value;
  };
  const modeLabel = valueLabel(mode, {
    native: '标准表单',
    governed: '受控表单',
    action: '操作页面',
    legacy: '历史承载',
  });
  const surfaceLabel = valueLabel(surface, {
    native: '标准界面',
    governed: '受控界面',
    business_config: '配置界面',
    lowcode_config: '低代码配置',
  });
  const viewTypeLabel = valueLabel(viewType, {
    form: '表单',
    tree: '列表',
    list: '列表',
    kanban: '看板',
    search: '搜索',
    calendar: '日历',
    pivot: '透视',
    graph: '图表',
  });
  return `配置模式：${modeLabel} · 承载界面：${surfaceLabel} · 视图类型：${viewTypeLabel} · 页面状态：${profileLabels[renderProfile.value] || renderProfile.value} · 筛选项：${filters} · 流转项：${transitions} · 操作权限：${permissionLabels.join('、') || '无可用权限'}`;
});

const showDebugActions = computed(() => renderProfile.value !== 'create');
const showDebugActionsVisible = computed(() => showHud.value && showDebugActions.value);
const runtimeRoleCode = computed(() => String(session.roleSurface?.role_code || '').trim().toLowerCase());
const runtimeCapabilities = computed(() => {
  const out = new Set<string>();
  (session.capabilities || []).forEach((key) => {
    const normalized = String(key || '').trim();
    if (normalized) out.add(normalized);
  });
  const catalog = session.capabilityCatalog || {};
  Object.values(catalog).forEach((meta) => {
    const key = String(meta?.key || '').trim();
    if (!key) return;
    const state = String(meta?.state || '').trim().toUpperCase();
    const capState = String(meta?.capability_state || '').trim().toLowerCase();
    if (state === 'LOCKED' || capState === 'deny') return;
    out.add(key);
  });
  return out;
});
const runtimeUserGroups = computed(() => {
  const user = session.user as { groups_xmlids?: unknown } | null;
  return Array.isArray(user?.groups_xmlids)
    ? user.groups_xmlids.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
});
const policyContext = computed(() => ({
  profile: renderProfile.value,
  formData: formData as Record<string, unknown>,
  capabilities: runtimeCapabilities.value,
  userGroups: runtimeUserGroups.value,
  roleCode: runtimeRoleCode.value,
}));

const warnings = computed(() => {
  const rows = contract.value?.warnings;
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => {
      if (typeof row === 'string') return row;
      if (row && typeof row === 'object') return String((row as Record<string, unknown>).message || (row as Record<string, unknown>).code || '');
      return '';
    })
    .map((x) => x.trim())
    .filter((item) => Boolean(item) && !item.startsWith('access_policy:'));
});

const contractAccessPolicy = computed<ContractAccessPolicy>(() => {
  const raw = (contract.value as Record<string, unknown> | null)?.access_policy;
  return normalizeContractAccessPolicy(raw);
});

const workflowTransitions = computed(() => {
  const rows = contract.value?.workflow?.transitions;
  if (!Array.isArray(rows)) return [];
  // Create profile only keeps primary create action in header; hide workflow transitions to avoid duplicated semantics.
  if (renderProfile.value === 'create') return [];
  const headerActionKeys = new Set(
    contractActions.value
      .filter((item) => item.level === 'header' || item.level === 'toolbar')
      .map((item) => item.key),
  );
  const transitions = rows.map((row, idx) => {
    const triggerLabel = String(row.trigger?.label || '').trim();
    const triggerName = String(row.trigger?.name || '').trim();
    const triggerKind = String(row.trigger?.kind || '').trim().toLowerCase();
    const action = contractActions.value.find((item) => {
      if (triggerKind && item.kind && item.kind !== triggerKind) return false;
      if (triggerName && (item.methodName === triggerName || item.key.includes(triggerName))) return true;
      if (triggerLabel && item.label === triggerLabel) return true;
      return false;
    }) || null;
    return {
      key: `wf_${idx}`,
      label: triggerLabel || triggerName || `transition_${idx + 1}`,
      notes: String(row.notes || ''),
      action,
    };
  });
  if (showHud.value) return transitions;
  return transitions.filter((item) => {
    const label = String(item.label || '').trim();
    if (!item.action) return false;
    if (item.action?.key && headerActionKeys.has(item.action.key)) return false;
    if (/^\d+$/.test(label)) return false;
    return true;
  });
});

const searchFilters = computed(() => {
  const rows = contract.value?.search?.filters;
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => ({
      key: String(row.key || '').trim(),
      label: String(row.label || row.key || '').trim(),
      domainRaw: String(row.domain_raw || '').trim(),
      contextRaw: String(row.context_raw || '').trim(),
    }))
    .filter((row) => row.key && row.label);
});

const showSearchFilters = computed(() => {
  if (useNativeFormTree.value) return false;
  if (!contract.value) return true;
  if (renderProfile.value !== 'create') return true;
  return !contract.value.hide_filters_on_create;
});

function relationIds(name: string): number[] {
  return normalizeRelationIds(formData[name]);
}

function selectedRelationOptions(name: string): RelationOption[] {
  const options = relationOptionsForField(name);
  const byId = new Map(options.map((option) => [option.id, option]));
  return relationIds(name).map((id) => byId.get(id) || { id, label: `#${id}` });
}

function many2oneValue(name: string) {
  const ids = relationIds(name);
  return ids.length ? String(ids[0]) : '';
}

function relationOptionsForField(name: string) {
  const rows = relationOptions.value[name];
  if (Array.isArray(rows) && rows.length) return rows;
  const ids = relationIds(name);
  if (!ids.length) return [];
  return ids.map((id) => ({ id, label: `#${id}` }));
}

function upsertRelationOption(fieldName: string, option: RelationOption | null) {
  if (!option) return;
  const current = Array.isArray(relationOptions.value[fieldName]) ? relationOptions.value[fieldName] : [];
  if (current.some((item) => item.id === option.id)) return;
  relationOptions.value = {
    ...relationOptions.value,
    [fieldName]: [option, ...current],
  };
}

function mergeRelationOptions(fieldName: string, options: RelationOption[]) {
  const current = Array.isArray(relationOptions.value[fieldName]) ? relationOptions.value[fieldName] : [];
  const incomingIds = new Set(options.map((item) => item.id));
  const merged = [
    ...options,
    ...current.filter((item) => !incomingIds.has(item.id)),
  ];
  relationOptions.value = {
    ...relationOptions.value,
    [fieldName]: merged,
  };
}

async function hydrateSelectedRelationOptions() {
  const fields = contract.value?.fields || {};
  await Promise.all(Object.entries(fields).map(async ([name, descriptor]) => {
    const type = fieldType(descriptor);
    if (!['many2one', 'many2many'].includes(type)) return;
    const relation = relationModel(name);
    if (!relation || deniedRelationModels.has(relation)) return;
    const ids = relationIds(name);
    if (!ids.length) return;
    const existingIds = new Set((relationOptions.value[name] || []).map((option) => option.id));
    const missingIds = ids.filter((id) => !existingIds.has(id));
    if (!missingIds.length) return;
    try {
      const response = await readContractFormRecord({
        model: relation,
        ids: missingIds,
        fields: relationReadFields(descriptor),
      });
      const records = Array.isArray(response.records) ? response.records : [];
      const options = records
        .map((row) => relationOptionFromRow(row as Record<string, unknown>, descriptor))
        .filter((item): item is RelationOption => Boolean(item));
      if (options.length) mergeRelationOptions(name, options);
    } catch (err) {
      if (err instanceof ApiError) {
        const denied = err.status === 403 || String(err.reasonCode || '').toUpperCase() === 'PERMISSION_DENIED';
        if (denied) deniedRelationModels.add(relation);
      }
    }
  }));
}

function relationKeyword(name: string) {
  return String(relationKeywords[name] || '');
}

function one2manyFieldRows(name: string) {
  return Array.isArray(one2manyRows[name]) ? one2manyRows[name] : [];
}

function one2manyRelationModel(name: string) {
  const descriptor = contract.value?.fields?.[name] as Record<string, unknown> | undefined;
  return String(descriptor?.relation || '').trim();
}

function one2manyRelationFieldDescriptor(fieldName: string, column: string) {
  const model = one2manyRelationModel(fieldName);
  if (!model) return null;
  const map = relationFieldDescriptors.value[model] || {};
  const descriptor = map[column];
  return descriptor || null;
}

function nativeNodeFieldDescriptor(nodeRaw: NativeFormLayoutNode, fallback?: FieldDescriptor): FieldDescriptor | undefined {
  return nativeNodeFieldDescriptorFromNode(nodeRaw as NativeLayoutLikeNode, fallback, contractFieldLabel);
}

function findNativeFieldNode(name: string): NativeFormLayoutNode | null {
  return findNativeFieldNodeInTree(nativeFormLayoutNodes.value as NativeLayoutLikeNode[], name) as NativeFormLayoutNode | null;
}

function effectiveFieldDescriptor(name: string): FieldDescriptor | undefined {
  const normalized = String(name || '').trim();
  if (!normalized) return undefined;
  const fallback = contract.value?.fields?.[normalized];
  const nativeNode = findNativeFieldNode(normalized);
  return nativeNode ? nativeNodeFieldDescriptor(nativeNode, fallback) : fallback;
}

function mergeNativeLayoutFieldDescriptorsIntoContract() {
  if (!contract.value?.fields) return;
  const fields = { ...(contract.value.fields || {}) };
  let changed = false;
  const walk = (nodes: NativeFormLayoutNode[]) => {
    nodes.forEach((node) => {
      const type = String(node?.type || (node as { containerType?: string })?.containerType || '').trim().toLowerCase();
      const name = String(node?.name || '').trim();
      if (type === 'field' && name) {
        const descriptor = nativeNodeFieldDescriptor(node, fields[name]);
        if (descriptor) {
          fields[name] = descriptor;
          changed = true;
        }
      }
      for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeFormLayoutNode[]);
      }
    });
  };
  walk(rawNativeFormLayoutNodes.value);
  if (changed) {
    contract.value = {
      ...contract.value,
      fields,
    };
  }
}

function nativeFieldSubview(name: string): Record<string, unknown> | null {
  return nativeFieldSubviewFromTree(nativeFormLayoutNodes.value as NativeLayoutLikeNode[], name);
}

function one2manyColumns(name: string): One2ManyColumn[] {
  const subviews = (contract.value?.views?.form as Record<string, unknown> | undefined)?.subviews;
  const legacySubview = subviews && typeof subviews === 'object'
    ? (subviews as Record<string, unknown>)[name]
    : undefined;
  const nativeSubview = nativeFieldSubview(name);
  const legacyColumns = subviewColumnCount(legacySubview);
  const nativeColumns = subviewColumnCount(nativeSubview);
  const fieldSubview = nativeColumns > legacyColumns ? nativeSubview : (legacySubview || nativeSubview);
  const tree = fieldSubview && typeof fieldSubview === 'object'
    ? (fieldSubview as Record<string, unknown>).tree
    : undefined;
  const columnsRaw = tree && typeof tree === 'object'
    ? (tree as Record<string, unknown>).columns
    : undefined;
  const out: One2ManyColumn[] = [];
  const columnLabel = (value: unknown, fallback: string) => {
    const label = String(value || '').trim();
    if (label === 'display_name' || label === 'name') return '名称';
    if (label) return label;
    return fallback === 'display_name' || fallback === 'name' ? '名称' : fallback;
  };
  if (Array.isArray(columnsRaw)) {
    columnsRaw.forEach((item) => {
      if (typeof item === 'string') {
        const normalized = item.trim();
        if (!normalized) return;
        const descriptor = one2manyRelationFieldDescriptor(name, normalized);
        const ttype = fieldType(descriptor) || 'char';
        out.push({
          name: normalized,
          label: columnLabel(descriptor?.string, normalized),
          ttype,
          required: Boolean(descriptor?.required),
          readonly: Boolean(descriptor?.readonly),
          selection: Array.isArray(descriptor?.selection) ? descriptor?.selection : undefined,
        });
        return;
      }
      if (!item || typeof item !== 'object') return;
      const row = item as Record<string, unknown>;
      const colName = String(row.name || '').trim();
      if (!colName) return;
      const descriptor = one2manyRelationFieldDescriptor(name, colName);
      const ttype = String(row.ttype || fieldType(descriptor) || 'char').trim() || 'char';
      out.push({
        name: colName,
        label: columnLabel(row.label || row.string || descriptor?.string, colName),
        ttype,
        required: Boolean(row.required || descriptor?.required),
        readonly: Boolean(row.readonly || descriptor?.readonly),
        selection: Array.isArray(row.selection)
          ? row.selection as Array<[string, string]>
          : (Array.isArray(descriptor?.selection) ? descriptor?.selection : undefined),
      });
    });
  }
  if (!out.length) {
    return [];
  }
  return out;
}

function one2manyPolicies(name: string) {
  const subviews = (contract.value?.views?.form as Record<string, unknown> | undefined)?.subviews;
  const legacySubview = subviews && typeof subviews === 'object'
    ? (subviews as Record<string, unknown>)[name]
    : undefined;
  const nativeSubview = nativeFieldSubview(name);
  const fieldSubview = nativeSubview || legacySubview;
  return one2manySubviewPolicies(fieldSubview);
}

function one2manyCanCreate(name: string) {
  return one2manyCanCreateFromPolicies(one2manyPolicies(name));
}

function one2manyCreateLabel(name: string, fieldLabel = '') {
  const label = String(fieldLabel || contractFieldLabel(name) || contract.value?.fields?.[name]?.string || '').trim();
  return one2manyCreateLabelFromPolicies(one2manyPolicies(name), label);
}

function one2manyPrimaryColumn(name: string) {
  return one2manyPrimaryColumnFromColumns(one2manyColumns(name));
}

function one2manyRowLabel(fieldName: string, row: One2ManyInlineRow) {
  return one2manyRowLabelFromPrimary(one2manyPrimaryColumn(fieldName), row);
}

function one2manySummary(name: string) {
  return one2manyDraftSummary(one2manyFieldRows(name));
}

function visibleOne2manyRows(name: string) {
  return one2manyFieldRows(name).filter((row) => !row.removed);
}

function removedOne2manyRows(name: string) {
  return one2manyFieldRows(name).filter((row) => row.removed);
}

function ensureOne2manyRows(name: string) {
  if (!Array.isArray(one2manyRows[name])) {
    one2manyRows[name] = [];
  }
  return one2manyRows[name];
}

function makeOne2manyKey() {
  return `o2m_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
}

function addOne2manyRow(name: string) {
  const rows = ensureOne2manyRows(name);
  const primary = one2manyPrimaryColumn(name);
  const columns = one2manyColumns(name);
  const values = columns.reduce<Record<string, unknown>>((acc, column) => {
    acc[column.name] = column.ttype === 'boolean' ? false : '';
    return acc;
  }, {});
  rows.push({
    key: makeOne2manyKey(),
    id: null,
    isNew: true,
    removed: false,
    dirty: true,
    dirtyFields: columns.map((column) => column.name),
    values: { ...values, [primary]: values[primary] ?? '' },
  });
  markFieldChanged(name);
}

function setOne2manyRowField(fieldName: string, rowKey: string, column: One2ManyColumn, value: unknown) {
  if (column.readonly) return;
  const rows = ensureOne2manyRows(fieldName);
  const row = rows.find((item) => item.key === rowKey);
  if (!row) return;
  const normalized = normalizeOne2manyColumnValue(column, value);
  row.values = {
    ...(row.values || {}),
    [column.name]: normalized,
  };
  row.dirty = true;
  if (!row.dirtyFields.includes(column.name)) {
    row.dirtyFields = [...row.dirtyFields, column.name];
  }
  markFieldChanged(fieldName);
}

function removeOne2manyRow(fieldName: string, rowKey: string) {
  const rows = ensureOne2manyRows(fieldName);
  const index = rows.findIndex((item) => item.key === rowKey);
  if (index < 0) return;
  const row = rows[index];
  if (row.isNew) {
    rows.splice(index, 1);
  } else {
    row.removed = true;
    row.dirty = true;
  }
  markFieldChanged(fieldName);
}

function restoreOne2manyRow(fieldName: string, rowKey: string) {
  const rows = ensureOne2manyRows(fieldName);
  const row = rows.find((item) => item.key === rowKey);
  if (!row) return;
  row.removed = false;
  row.dirty = true;
  markFieldChanged(fieldName);
}

function initOne2manyRows(name: string, source: unknown) {
  const ids = normalizeRelationIds(source);
  const options = relationOptionsForField(name);
  const optionMap = new Map(options.map((item) => [item.id, item.label]));
  const primary = one2manyPrimaryColumn(name);
  one2manyRows[name] = ids.map((id) => ({
    key: `o2m_id_${id}`,
    id,
    isNew: false,
    removed: false,
    dirty: false,
    dirtyFields: [],
    values: {
      [primary]: optionMap.get(id) || `#${id}`,
      name: optionMap.get(id) || `#${id}`,
    },
  }));
}

async function hydrateOne2manyRows(name: string) {
  const relation = one2manyRelationModel(name);
  if (!relation) return;
  const rows = ensureOne2manyRows(name).filter((row) => row.id && !row.isNew);
  if (!rows.length) return;
  const columns = one2manyColumns(name);
  if (!columns.length) return;
  const fields = Array.from(new Set(['id', 'display_name', 'name', ...columns.map((column) => column.name)]));
  try {
    const response = await readContractFormRecord({
      model: relation,
      ids: rows.map((row) => Number(row.id)).filter((id) => Number.isFinite(id) && id > 0),
      fields,
    });
    const records = Array.isArray(response.records) ? response.records : [];
    const byId = new Map<number, Record<string, unknown>>();
    records.forEach((record) => {
      const id = Number((record as Record<string, unknown>).id);
      if (Number.isFinite(id) && id > 0) byId.set(Math.trunc(id), record as Record<string, unknown>);
    });
    rows.forEach((row) => {
      if (!row.id || row.dirty) return;
      const record = byId.get(Number(row.id));
      if (!record) return;
      row.values = columns.reduce<Record<string, unknown>>((acc, column) => {
        acc[column.name] = record[column.name] ?? '';
        return acc;
      }, {
        id: record.id,
        display_name: record.display_name,
        name: record.name ?? record.display_name ?? row.values?.name ?? `#${row.id}`,
      });
    });
  } catch {
    // Keep the id/display-name fallback when the child model is not readable.
  }
}

async function hydrateVisibleOne2manyRows() {
  const fields = contract.value?.fields || {};
  const names = Object.entries(fields)
    .filter(([, descriptor]) => fieldType(descriptor) === 'one2many')
    .map(([name]) => name)
    .filter((name) => isWritableFieldVisible(name) || one2manyFieldRows(name).length > 0);
  await Promise.all(names.map((name) => hydrateOne2manyRows(name)));
}

function buildOne2manyCommandValue(name: string, mode: 'onchange' | 'write') {
  return buildOne2manyCommandValueFromRows(originalValues.value[name], one2manyFieldRows(name), mode);
}

function collectOne2manyDraftValidation() {
  const issues: string[] = [];
  const rowErrors: Record<string, string[]> = {};
  Object.entries(one2manyRows).forEach(([fieldName, rows]) => {
    if (!Array.isArray(rows) || !rows.length) return;
    const hasTouchedRows = rows.some((row) => row.isNew || row.dirty || row.removed);
    if (recordId.value && !hasTouchedRows) return;
    const primary = one2manyPrimaryColumn(fieldName);
    const columns = one2manyColumns(fieldName);
    const requiredColumns = columns.filter((column) => column.required);
    const labels = new Set<string>();
    rows.forEach((row, index) => {
      if (row.removed) return;
      const rowKey = `${fieldName}:${row.key}`;
      const perRow: string[] = [];
      requiredColumns.forEach((column) => {
        const value = row.values?.[column.name];
        if (isOne2manyEmptyValue(column, value)) {
          perRow.push(`${column.label}不能为空`);
          issues.push(`${fieldName} 第${index + 1}行${column.label}不能为空`);
        }
      });
      const label = String(row.values?.[primary] ?? row.values?.name ?? '').trim();
      if (label) {
        const key = label.toLowerCase();
        if (labels.has(key)) {
          perRow.push(`主值重复：${label}`);
          issues.push(`${fieldName} 存在重复行值：${label}`);
        } else {
          labels.add(key);
        }
      }
      if (perRow.length) {
        rowErrors[rowKey] = perRow;
      }
    });
  });
  return { issues, rowErrors };
}

function one2manyRowErrors(fieldName: string, rowKey: string) {
  return one2manyValidation.value.rowErrors[`${fieldName}:${rowKey}`] || [];
}

function one2manyRowHints(fieldName: string, row: One2ManyInlineRow) {
  const messages: string[] = [];
  onchangeLinePatches.value.forEach((patch) => {
    if (String(patch.field || '') !== fieldName) return;
    const rowKey = String(patch.row_key || '').trim();
    const rowId = Number(patch.row_id || 0);
    const matched = (rowKey && rowKey === row.key) || (rowId > 0 && Number(row.id || 0) === rowId);
    if (!matched) return;
    const warns = Array.isArray(patch.warnings) ? patch.warnings : [];
    warns.forEach((warn) => {
      const message = String(warn?.message || warn?.title || '').trim();
      if (message) messages.push(message);
      const reasonCode = String(warn?.reason_code || '').trim();
      if (reasonCode) messages.push(`处理原因：${formRuntimeReasonLabel(reasonCode)}`);
    });
    const rowState = String(patch.row_state || '').trim().toLowerCase();
    if (rowState) {
      messages.push(`处理结果：${formRuntimeRowStateLabel(rowState)}`);
    }
    if (Array.isArray(patch.command_hint) && patch.command_hint.length) {
      messages.push(`处理建议：${formRuntimeCommandHintLabel(patch.command_hint)}`);
    }
  });
  return Array.from(new Set(messages));
}

function applyOnchangeLinePatches(linePatches: OnchangeLinePatch[]) {
  if (!Array.isArray(linePatches) || !linePatches.length) return;
  linePatches.forEach((line) => {
    const fieldName = String(line.field || '').trim();
    if (!fieldName) return;
    const rowKey = String(line.row_key || '').trim();
    const rowId = Number(line.row_id || 0);
    const rows = ensureOne2manyRows(fieldName);
    const row = rows.find((item) => (rowKey && item.key === rowKey) || (rowId > 0 && Number(item.id || 0) === rowId));
    if (!row) return;
    const patch = line.patch;
    if (patch && typeof patch === 'object') {
      row.values = {
        ...(row.values || {}),
        ...(patch as Record<string, unknown>),
      };
    }
  });
}

function setRelationKeyword(name: string, keyword: string) {
  relationKeywords[name] = keyword;
  const descriptor = effectiveFieldDescriptor(name);
  const widget = String((descriptor as Record<string, unknown> | undefined)?.widget || '').trim().toLowerCase();
  if (fieldType(descriptor) === 'many2many' && widget === 'many2many_tags') {
    markFieldChanged(name);
  }
  if (relationQueryTimers[name]) {
    clearTimeout(relationQueryTimers[name]);
  }
  relationQueryTimers[name] = setTimeout(() => {
    const currentKeyword = relationKeywords[name] || '';
    void queryRelationOptions(name, currentKeyword);
  }, 260);
}

function filteredRelationOptions(name: string) {
  const rows = relationOptionsForField(name);
  const kw = relationKeyword(name).trim().toLowerCase();
  if (!kw) return rows;
  return rows.filter((row) => row.label.toLowerCase().includes(kw) || String(row.id).includes(kw));
}

function relationModel(name: string) {
  return relationModelFromDescriptor(effectiveFieldDescriptor(name));
}

function formUiLabels(): Record<string, string> {
  return formUiLabelsFromFormView(contract.value?.views?.form);
}

function formUiLabel(key: string) {
  return formUiLabelFromLabels(formUiLabels(), key);
}

function dynamicDomainFromDescriptor(descriptor?: FieldDescriptor) {
  const raw = (descriptor as Record<string, unknown> | undefined)?.domain;
  if (typeof raw !== 'string' || !raw.trim()) return [];
  const out: unknown[] = [];
  const text = raw.trim();
  const tuplePattern = /\(['"]([\w.]+)['"]\s*,\s*['"]([=!<>]{1,2}|in|not in|ilike|like)['"]\s*,\s*([A-Za-z_]\w*)\)/g;
  let match: RegExpExecArray | null;
  let hasDynamicDependency = false;
  let hasUnresolvedDependency = false;
  while ((match = tuplePattern.exec(text))) {
    const [, fieldName, operator, valueField] = match;
    if (!fieldName || !operator || !valueField) continue;
    hasDynamicDependency = true;
    const value = resolveDynamicDomainDependencyValue(valueField);
    if (value === undefined || value === null || value === '' || value === false) {
      hasUnresolvedDependency = true;
      continue;
    }
    const normalizedValue = normalizeFieldValue(valueField, value);
    if (normalizedValue === undefined || normalizedValue === null || normalizedValue === '' || normalizedValue === false) {
      hasUnresolvedDependency = true;
      continue;
    }
    out.push([fieldName, operator, normalizedValue]);
  }
  if (hasDynamicDependency && hasUnresolvedDependency) {
    const descriptorRecord = descriptor as Record<string, unknown> | undefined;
    const currentFieldName = String(descriptorRecord?.name || descriptorRecord?.field || '').trim();
    if (currentFieldName && fieldType(descriptor) === 'many2one') {
      const currentValue = normalizeFieldValue(currentFieldName, formData[currentFieldName]);
      const currentId = Number(currentValue || 0);
      if (Number.isFinite(currentId) && currentId > 0) {
        return [['id', '=', Math.trunc(currentId)]];
      }
    }
    return [['id', '=', -1]];
  }
  return out;
}

function resolveDynamicDomainDependencyValue(valueField: string) {
  const direct = formData[valueField]
    ?? route.query[`default_${valueField}`]
    ?? route.query[valueField];
  if (direct !== undefined && direct !== null && direct !== '') return direct;
  const keyword = relationKeyword(valueField).trim().toLowerCase();
  if (!keyword) return direct;
  const option = (relationOptions.value[valueField] || []).find((item) => {
    const label = item.label.trim().toLowerCase();
    return label === keyword || label.includes(keyword) || keyword.includes(label);
  });
  return option?.id || direct;
}

function clearDynamicRelationDependents(changedName: string) {
  const fields = contract.value?.fields || {};
  const changed = String(changedName || '').trim();
  if (!changed) return;
  Object.entries(fields).forEach(([name, descriptor]) => {
    descriptor = effectiveFieldDescriptor(name) || descriptor;
    if (name === changed) return;
    if (!['many2one', 'many2many'].includes(fieldType(descriptor))) return;
    if (!dynamicDomainDependencyFields(descriptor).includes(changed)) return;
    const currentIds = relationIds(name);
    const selectedOption = currentIds.length
      ? (relationOptions.value[name] || []).find((option) => option.id === currentIds[0])
      : null;
    const staleKeyword = relationKeyword(name).trim() || String(selectedOption?.label || '').trim();
    if (staleKeyword) invalidatedRelationKeywords[name] = staleKeyword;
    clearedDynamicRelationFields[name] = true;
    if (fieldType(descriptor) === 'many2many') {
      formData[name] = [];
    } else {
      formData[name] = false;
    }
    if (relationQueryTimers[name]) {
      clearTimeout(relationQueryTimers[name]);
      delete relationQueryTimers[name];
    }
    relationKeywords[name] = '';
    relationOptions.value = {
      ...relationOptions.value,
      [name]: [],
    };
    void queryRelationOptions(name, '');
  });
}

function relationDomain(descriptor?: FieldDescriptor) {
  const entry = relationEntry(descriptor);
  const out: unknown[] = [];
  const entryDomain = Array.isArray(entry?.domain) ? entry.domain : [];
  const dynamicDomain = dynamicDomainFromDescriptor(descriptor);
  const dynamicResolved = Array.isArray(dynamicDomain)
    && dynamicDomain.length > 0
    && !isBlockAllDomain(dynamicDomain);
  const entryBlocksAll = isBlockAllDomain(entryDomain);
  const dynamicBlocksAll = isBlockAllDomain(dynamicDomain);
  if (entryDomain.length && !(entryBlocksAll && (dynamicResolved || dynamicBlocksAll))) out.push(...entryDomain);
  out.push(...dynamicDomain);
  const descriptorRecord = descriptor as Record<string, unknown> | undefined;
  const fieldName = String(descriptorRecord?.name || descriptorRecord?.field || '').trim();
  const relation = String(descriptorRecord?.relation || entry?.model || '').trim();
  const routeDefaultType = String(route.query.default_type || '').trim();
  if (!out.length && fieldName === 'original_contract_id' && relation === 'construction.contract' && ['out', 'in'].includes(routeDefaultType)) {
    out.push(['type', '=', routeDefaultType]);
  }
  const type = String(entry?.defaultVals?.type || '').trim();
  if (type) out.push(['type', '=', type]);
  return out.length ? out : undefined;
}

function runtimeRelationDomain(name: string) {
  const out: unknown[] = [];
  const base = (fieldModifierMap.value?.[name] || {}) as Record<string, unknown>;
  if (Array.isArray(base.domain)) out.push(...base.domain);
  const patch = (onchangeModifiersPatch.value?.[name] || {}) as Record<string, unknown>;
  if (Array.isArray(patch.domain)) out.push(...patch.domain);
  return out;
}

function mergedRelationDomain(name: string, descriptor?: FieldDescriptor) {
  const base = relationDomain(descriptor);
  const runtime = runtimeRelationDomain(name);
  const out: unknown[] = [];
  const runtimeHasDomain = Array.isArray(runtime) && runtime.length > 0;
  const baseOnlyBlocksAll = isBlockAllDomain(base);
  if (Array.isArray(base) && !(runtimeHasDomain && baseOnlyBlocksAll)) out.push(...base);
  if (Array.isArray(runtime)) out.push(...runtime);
  return out.length ? out : undefined;
}

async function queryRelationOptions(name: string, keyword: string): Promise<RelationOption[]> {
  const descriptor = effectiveFieldDescriptor(name);
  const relation = relationModel(name);
  if (!relation) return [];
  const entry = relationEntry(descriptor);
  if (entry && entry.canRead === false) {
    deniedRelationModels.add(relation);
    return [];
  }
  if (deniedRelationModels.has(relation)) return [];
  let search = String(keyword || '').trim();
  if (search && invalidatedRelationKeywords[name] === search && !formData[name]) {
    search = '';
    relationKeywords[name] = '';
  }
  const domain = mergedRelationDomain(name, descriptor);
  try {
    const listed = await listContractFormRecords({
      model: relation,
      fields: relationReadFields(descriptor),
      limit: search ? 40 : 80,
      order: relationOrder(descriptor),
      domain,
      search_term: search || undefined,
      silentErrors: true,
    });
    const records = Array.isArray(listed?.records) ? listed.records : [];
    const mapped = records
      .map((row) => relationOptionFromRow(row as Record<string, unknown>, descriptor))
      .filter((item): item is RelationOption => Boolean(item));
    if (search && !mapped.length && (dynamicDomainDependencyFields(descriptor).length || runtimeRelationDomain(name).length)) {
      return queryRelationOptions(name, '');
    }
    if (mapped.length || !search) {
      relationOptions.value = {
        ...relationOptions.value,
        [name]: mapped,
      };
    }
    return mapped;
  } catch (err) {
    if (err instanceof ApiError) {
      const denied = err.status === 403 || String(err.reasonCode || '').toUpperCase() === 'PERMISSION_DENIED';
      if (denied) deniedRelationModels.add(relation);
    }
    // keep existing options if remote query fails
    return [];
  }
}

async function fetchRelationOptions(name: string, keyword: string, limit = 80): Promise<RelationOption[]> {
  const descriptor = effectiveFieldDescriptor(name);
  const relation = relationModel(name);
  if (!relation) return [];
  const entry = relationEntry(descriptor);
  if (entry && entry.canRead === false) return [];
  const domain = mergedRelationDomain(name, descriptor);
  const listed = await listContractFormRecords({
    model: relation,
    fields: relationReadFields(descriptor),
    limit,
    order: relationOrder(descriptor),
    domain,
    search_term: String(keyword || '').trim() || undefined,
    silentErrors: true,
  });
  const records = Array.isArray(listed?.records) ? listed.records : [];
  return records
    .map((row) => relationOptionFromRow(row as Record<string, unknown>, descriptor))
    .filter((item): item is RelationOption => Boolean(item));
}

async function loadRelationSearchColumns(fieldName: string): Promise<RelationSearchColumn[]> {
  const descriptor = effectiveFieldDescriptor(fieldName);
  const contractColumns = relationSearchColumnsFromContract(relationSearchDialogContract(descriptor));
  if (contractColumns.length) return contractColumns;
  const relation = relationModel(fieldName);
  if (!relation) return fallbackRelationSearchColumns(descriptor);
  try {
    const response = await loadModelContractRaw(relation, {
      viewType: 'tree',
      renderProfile: 'readonly',
    });
    const data = response?.data && typeof response.data === 'object'
      ? response.data as Record<string, unknown>
      : response as unknown as Record<string, unknown>;
    return normalizeRelationSearchColumns(data, descriptor);
  } catch {
    return fallbackRelationSearchColumns(descriptor);
  }
}

async function fetchRelationSearchRows(name: string, keyword: string, limit = 120): Promise<RelationSearchRow[]> {
  const descriptor = effectiveFieldDescriptor(name);
  const relation = relationModel(name);
  if (!relation) return [];
  const entry = relationEntry(descriptor);
  if (entry && entry.canRead === false) return [];
  const domain = mergedRelationDomain(name, descriptor);
  const dialog = relationSearchDialogContract(descriptor);
  const columns = relationSearchDialog.columns.length ? relationSearchDialog.columns : relationSearchColumnsFromContract(dialog);
  const limitValue = Number(dialog.limit || limit || 120);
  const order = String(dialog.order || 'id desc').trim() || 'id desc';
  const listed = await listContractFormRecords({
    model: relation,
    fields: relationSearchReadFields(columns.length ? columns : fallbackRelationSearchColumns(descriptor), dialog),
    limit: Number.isFinite(limitValue) && limitValue > 0 ? Math.min(Math.trunc(limitValue), 200) : 120,
    order,
    domain,
    search_term: String(keyword || '').trim() || undefined,
    silentErrors: true,
  });
  const records = Array.isArray(listed?.records) ? listed.records : [];
  return records
    .map((row) => {
      const values = row as Record<string, unknown>;
      const id = Number(values.id);
      if (!Number.isFinite(id) || id <= 0) return null;
      const firstColumn = columns[0]?.name || '';
      const label = cleanRelationDisplayLabel(values.display_name || values.name || values[firstColumn], id);
      return { id: Math.trunc(id), label, values };
    })
    .filter((item): item is RelationSearchRow => Boolean(item));
}

function closeRelationSearchDialog() {
  relationSearchDialog.open = false;
  relationSearchDialog.fieldName = '';
  relationSearchDialog.error = '';
  relationSearchDialog.selectedId = null;
}

function onRelationDialogDocumentKeydown(event: KeyboardEvent) {
  if (!relationSearchDialog.open || event.key !== 'Escape') return;
  event.preventDefault();
  closeRelationSearchDialog();
}

async function openRelationSearchDialog(fieldName: string, descriptor?: FieldDescriptor) {
  const relation = relationModel(fieldName);
  if (!relation) return;
  const labels = relationUiLabels(descriptor);
  relationSearchDialog.open = true;
  relationSearchDialog.fieldName = fieldName;
  relationSearchDialog.labels = labels;
  const descriptorLabel = descriptor && typeof descriptor === 'object'
    ? String((descriptor as Record<string, unknown>).string || (descriptor as Record<string, unknown>).label || fieldName).trim()
    : fieldName;
  relationSearchDialog.title = labels.dialog_title || `${descriptorLabel}：搜索更多`;
  relationSearchDialog.keyword = relationKeyword(fieldName);
  relationSearchDialog.error = '';
  relationSearchDialog.options = [];
  relationSearchDialog.rows = [];
  const resolvedDescriptor = effectiveFieldDescriptor(fieldName);
  relationSearchDialog.columns = relationSearchColumnsFromContract(relationSearchDialogContract(resolvedDescriptor));
  relationSearchDialog.selectedId = null;
  relationSearchDialog.createMode = relationCreateMode(resolvedDescriptor);
  relationSearchDialog.columns = await loadRelationSearchColumns(fieldName);
  await runRelationSearch();
  await nextTick();
  relationSearchInputRef.value?.focus();
}

function setRelationSearchKeyword(keyword: string) {
  relationSearchDialog.keyword = keyword;
}

async function runRelationSearch() {
  const fieldName = relationSearchDialog.fieldName;
  if (!fieldName) return;
  relationSearchDialog.loading = true;
  relationSearchDialog.error = '';
  try {
    const rows = await fetchRelationSearchRows(fieldName, relationSearchDialog.keyword, 120);
    relationSearchDialog.rows = rows;
    relationSearchDialog.options = rows.map((row) => ({ id: row.id, label: row.label }));
    relationSearchDialog.selectedId = null;
    relationOptions.value = {
      ...relationOptions.value,
      [fieldName]: relationSearchDialog.options,
    };
  } catch (err) {
    relationSearchDialog.error = sanitizeUiErrorMessage(
      err instanceof Error ? err.message : err,
      relationSearchDialog.labels.search_failed || '',
    );
  } finally {
    relationSearchDialog.loading = false;
  }
}

function relationSearchCell(row: RelationSearchRow, columnName: string) {
  const value = row.values[columnName];
  if (value === null || value === undefined || value === false) return '';
  if (Array.isArray(value)) {
    if (value.length >= 2) return String(value[1] ?? '');
    return value.map((item) => String(item ?? '')).filter(Boolean).join(', ');
  }
  if (typeof value === 'object') {
    const rec = value as Record<string, unknown>;
    return String(rec.display_name || rec.name || rec.id || '');
  }
  if (typeof value === 'boolean') return value ? '是' : '否';
  return String(value);
}

function selectRelationSearchRow(row: RelationSearchRow) {
  relationSearchDialog.selectedId = row.id;
}

function confirmRelationSearchSelection(rowArg?: RelationSearchRow) {
  const row = rowArg || relationSearchDialog.rows.find((item) => item.id === relationSearchDialog.selectedId);
  if (!row) return;
  selectRelationSearchOption({ id: row.id, label: row.label });
}

function selectRelationSearchOption(option: RelationOption) {
  const fieldName = relationSearchDialog.fieldName;
  if (!fieldName) return;
  setMany2oneOption(fieldName, option);
  closeRelationSearchDialog();
}

function setMany2oneOption(fieldName: string, option: RelationOption) {
  formData[fieldName] = option.id;
  relationKeywords[fieldName] = option.label;
  mergeRelationOptions(fieldName, [option]);
  clearDynamicRelationDependents(fieldName);
  markFieldChanged(fieldName);
  void switchFormByRelationOption(fieldName, option);
}

function normalizedRouteQuery(): Record<string, string | string[]> {
  return Object.fromEntries(
    Object.entries(route.query).map(([key, value]) => [
      key,
      Array.isArray(value)
        ? value.filter((item): item is string => typeof item === 'string')
        : String(value || ''),
    ]),
  );
}

async function switchFormByRelationOption(fieldName: string, option: RelationOption) {
  if (recordId.value) return;
  const descriptor = contract.value?.fields?.[fieldName];
  const entry = relationEntry(descriptor);
  if (!entry?.switchContext?.enabled || !option.switchContext?.code) return;
  const nextCode = option.switchContext.code;
  const currentCode = String(route.query.current_business_category_code || route.query.default_business_category_code || '').trim();
  if (currentCode === nextCode) return;
  const query = normalizedRouteQuery();
  for (const key of entry.switchContext.defaultClearFields || []) {
    delete query[`default_${key}`];
  }
  query.current_business_category_code = nextCode;
  query.default_business_category_code = nextCode;
  query.current_business_category_label = option.switchContext.label || option.label;
  query.default_business_category_label = option.switchContext.label || option.label;
  query.default_business_category_id = String(option.id);
  query.ctx_source = 'business_category_relation_switch';
  Object.entries(option.switchContext.defaultValues || {}).forEach(([key, value]) => {
    const normalizedKey = String(key || '').trim();
    if (!normalizedKey || value === undefined || value === null) return;
    if (Array.isArray(value) || typeof value === 'object') return;
    query[`default_${normalizedKey}`] = String(value);
  });
  await router.replace({ query });
  await reload();
}

async function createRelationFromSearchDialog() {
  const fieldName = relationSearchDialog.fieldName;
  if (!fieldName) return;
  const descriptor = contract.value?.fields?.[fieldName];
  const label = relationSearchDialog.keyword.trim();
  const mode = relationCreateMode(descriptor);
  const exact = label
    ? relationSearchDialog.options.find((item) => item.label.trim().toLowerCase() === label.toLowerCase())
    : null;
  if (exact && mode !== 'page') {
    selectRelationSearchOption(exact);
    return;
  }
  if (mode === 'quick') {
    if (!label) {
      relationSearchDialog.error = relationSearchDialog.labels.missing_name || '';
      return;
    }
    validationErrors.value = [];
    await quickCreateRelation(fieldName, descriptor, label, { stayInDialog: true });
    if (!validationErrors.value.length) {
      closeRelationSearchDialog();
    } else {
      relationSearchDialog.error = validationErrors.value.join('；');
      validationErrors.value = [];
    }
    return;
  }
  closeRelationSearchDialog();
  await openRelationCreateForm(fieldName, descriptor);
}

async function ensureRelationFieldDescriptors(name: string) {
  const relation = one2manyRelationModel(name);
  if (!relation) return;
  if (relationFieldDescriptors.value[relation]) return;
  try {
    const response = await loadModelContractRaw(relation, {
      viewType: 'form',
      renderProfile: 'edit',
    });
    const fields = response?.data?.fields;
    if (fields && typeof fields === 'object') {
      relationFieldDescriptors.value = {
        ...relationFieldDescriptors.value,
        [relation]: fields as Record<string, FieldDescriptor>,
      };
    }
  } catch {
    // best effort; fallback to char fields
  }
}

async function openRelationCreateForm(fieldName: string, descriptor?: FieldDescriptor) {
  const relation = String((descriptor as Record<string, unknown> | undefined)?.relation || '').trim();
  if (!relation) return;
  const mode = relationCreateMode(descriptor);
  if (mode === 'none') {
    validationErrors.value = [relationUiLabel(descriptor, 'missing_create_entry')];
    return;
  }
  if (mode === 'quick') {
    const currentKeyword = relationKeyword(fieldName).trim();
    if (!currentKeyword) {
      validationErrors.value = [relationUiLabel(descriptor, 'missing_name', relationUiLabel(descriptor, 'quick_create_prompt', '请先输入要新增的名称'))];
      return;
    }
    await quickCreateRelation(fieldName, descriptor, currentKeyword);
    return;
  }
  const entry = relationEntry(descriptor);
  const relationActionId = entry?.actionId || null;
  const menuId = entry?.menuId || 0;
  if (!relationActionId) {
    validationErrors.value = [relationUiLabel(descriptor, 'missing_page_entry')];
    return;
  }
  const defaultQuery = Object.entries(entry?.defaultVals || {}).reduce<Record<string, unknown>>((acc, [key, value]) => {
    if (!key) return acc;
    acc[`default_${key}`] = value;
    return acc;
  }, {});
  Object.entries(entry?.defaultFromFields || {}).forEach(([targetField, sourceFieldRaw]) => {
    const sourceField = String(sourceFieldRaw || '').trim();
    if (!targetField || !sourceField) return;
    const value = normalizeFieldValue(sourceField, formData[sourceField]);
    if (value === undefined || value === null || value === '') return;
    defaultQuery[`default_${targetField}`] = value;
  });
  const nextQuery = pickContractNavQuery(route.query as Record<string, unknown>, {
    action_id: relationActionId,
    menu_id: menuId || undefined,
    view_mode: 'form',
    ...defaultQuery,
  });
  const returnUrl = `${window.location.pathname}${window.location.search}`;
  try {
    await router.push({
      name: 'model-form',
      params: { model: relation, id: 'new' },
      query: {
        ...nextQuery,
        return_url: encodeURIComponent(returnUrl),
        return_field: fieldName,
        return_model: model.value,
        return_action_id: actionId.value || undefined,
        return_menu_id: Number(route.query.menu_id || 0) || undefined,
      },
    });
  } catch (err) {
    if (relation === 'sc.dictionary' && mode === 'page' && entry?.canCreate && Object.keys(entry?.defaultVals || {}).length) {
      const label = String(await actionInputDialog.open({
        title: relationUiLabel(descriptor, 'page_unavailable_prompt'),
        label: relationUiLabel(descriptor, 'create_label_placeholder'),
        placeholder: relationUiLabel(descriptor, 'create_label_placeholder'),
        confirmLabel: relationUiLabel(descriptor, 'quick_create_confirm'),
        cancelLabel: relationUiLabel(descriptor, 'cancel'),
        required: true,
      }) || '').trim();
      if (label) await quickCreateRelation(fieldName, descriptor, label);
      return;
    }
    validationErrors.value = [sanitizeUiErrorMessage(err instanceof Error ? err.message : err, relationUiLabel(descriptor, 'create_page_failed'))];
  }
}

function currentRelationRecordId(fieldName: string) {
  const id = Number(relationIds(fieldName)[0] || 0);
  return Number.isFinite(id) && id > 0 ? Math.trunc(id) : 0;
}

function canOpenRelationRecordForm(fieldName: string, descriptor?: FieldDescriptor) {
  const relation = relationModel(fieldName);
  const entry = relationEntry(descriptor);
  return Boolean(relation && currentRelationRecordId(fieldName) > 0 && entry?.canRead !== false && entry?.canOpen !== false);
}

async function openRelationRecordForm(fieldName: string, descriptor?: FieldDescriptor) {
  const relation = relationModel(fieldName);
  const recordId = currentRelationRecordId(fieldName);
  const entry = relationEntry(descriptor);
  if (!relation || recordId <= 0) return;
  if (entry?.canRead === false) {
    validationErrors.value = [relationUiLabel(descriptor, 'missing_read_entry')];
    return;
  }
  const relationActionId = entry?.actionId || null;
  const menuId = entry?.menuId || 0;
  const nextQuery = pickContractNavQuery(route.query as Record<string, unknown>, {
    action_id: relationActionId || undefined,
    menu_id: menuId || undefined,
    view_mode: 'form',
  });
  const returnUrl = `${window.location.pathname}${window.location.search}`;
  try {
    await router.push({
      name: 'model-form',
      params: { model: relation, id: String(recordId) },
      query: {
        ...nextQuery,
        return_url: encodeURIComponent(returnUrl),
        return_field: fieldName,
        return_model: model.value,
        return_action_id: actionId.value || undefined,
        return_menu_id: Number(route.query.menu_id || 0) || undefined,
      },
    });
  } catch (err) {
    validationErrors.value = [sanitizeUiErrorMessage(err instanceof Error ? err.message : err, relationUiLabel(descriptor, 'open_record_failed'))];
  }
}

async function quickCreateRelation(
  fieldName: string,
  descriptor: FieldDescriptor | undefined,
  label: string,
  options: { stayInDialog?: boolean } = {},
) {
  const relation = String((descriptor as Record<string, unknown> | undefined)?.relation || '').trim();
  if (!relation) return;
  const entry = relationEntry(descriptor);
  try {
    const existing = await fetchRelationOptions(fieldName, label, 20);
    const exact = existing.find((item) => item.label.trim().toLowerCase() === label.trim().toLowerCase());
    if (exact) {
      setMany2oneOption(fieldName, exact);
      return;
    }
    const inline = relationInlineCreate(descriptor);
    const nameField = inline.nameField || 'name';
    const vals: Record<string, unknown> = { ...(entry?.defaultVals || {}), [nameField]: label };
    if (relation === 'sc.dictionary' && typeof vals.type === 'string' && String(vals.type || '').trim()) {
      vals.code = label.toUpperCase().replace(/\\s+/g, '_').slice(0, 60);
    }
    const created = await createContractFormRecord({ model: relation, vals });
    const id = Number(created?.id || 0);
    if (Number.isFinite(id) && id > 0) {
      const option = { id: Math.trunc(id), label };
      setMany2oneOption(fieldName, option);
      if (!options.stayInDialog) await queryRelationOptions(fieldName, label);
    }
  } catch (err) {
    const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, relationUiLabel(descriptor, 'quick_create_failed'));
    validationErrors.value = [message];
  }
}

async function loadRelationOptions() {
  const fields = contract.value?.fields || {};
  const visibleRelationFields = new Set(
    layoutNodes.value
      .filter((node) => node.kind === 'field' && isWritableFieldVisible(node.name))
      .map((node) => node.name),
  );
  const entries = Object.entries(fields).filter(([name]) => {
    if (!visibleRelationFields.size) return relationIds(name).length > 0;
    if (visibleRelationFields.has(name)) return true;
    return relationIds(name).length > 0;
  });
  const one2manyNames = entries
    .filter(([, descriptor]) => fieldType(descriptor) === 'one2many')
    .map(([name]) => name);
  await Promise.all(one2manyNames.map((name) => ensureRelationFieldDescriptors(name)));
  const next: Record<string, RelationOption[]> = {};
  await Promise.all(entries.map(async ([name, descriptor]) => {
    if (!descriptor || typeof descriptor !== 'object') return;
    const type = fieldType(descriptor);
    if (!['many2one', 'many2many', 'one2many'].includes(type)) return;
    const relation = String((descriptor as Record<string, unknown>).relation || '').trim();
    if (!relation) return;
    const entry = relationEntry(descriptor as FieldDescriptor);
    if (entry && entry.canRead === false) {
      deniedRelationModels.add(relation);
      next[name] = [];
      return;
    }
    if (deniedRelationModels.has(relation)) {
      next[name] = [];
      return;
    }
    const domain = mergedRelationDomain(name, descriptor as FieldDescriptor);
    try {
      const listed = await listContractFormRecords({
        model: relation,
        fields: relationReadFields(descriptor as FieldDescriptor),
        limit: 80,
        order: relationOrder(descriptor as FieldDescriptor),
        domain,
        silentErrors: true,
      });
      const records = Array.isArray(listed?.records) ? listed.records : [];
      next[name] = records
        .map((row) => relationOptionFromRow(row as Record<string, unknown>, descriptor as FieldDescriptor))
        .filter((item): item is RelationOption => Boolean(item));
    } catch (err) {
      if (err instanceof ApiError) {
        const denied = err.status === 403 || String(err.reasonCode || '').toUpperCase() === 'PERMISSION_DENIED';
        if (denied) deniedRelationModels.add(relation);
      }
      next[name] = [];
    }
  }));
  Object.entries(next).forEach(([fieldName, options]) => {
    mergeRelationOptions(fieldName, options);
  });
}

function toActionId(raw: unknown) {
  return toPositiveInt(raw);
}

function detectMethodName(key: string, payloadMethod: string) {
  return detectObjectMethodFromActionKey(key, payloadMethod);
}

function currentWorkflowContract(): Record<string, unknown> {
  const root = dictOrEmpty(contract.value);
  const storeSnapshot = dictOrEmpty(v2ContractStore.value?.snapshot);
  const storeDirect = dictOrEmpty(storeSnapshot.workflowContract);
  if (Object.keys(storeDirect).length) return storeDirect;
  const storeRuntime = dictOrEmpty(storeSnapshot.runtimeContract);
  const storeNested = dictOrEmpty(storeRuntime.workflowContract);
  if (Object.keys(storeNested).length) return storeNested;
  const direct = root.workflowContract;
  if (direct && typeof direct === 'object' && !Array.isArray(direct)) {
    return direct as Record<string, unknown>;
  }
  const runtime = root.runtimeContract;
  if (runtime && typeof runtime === 'object' && !Array.isArray(runtime)) {
    const nested = (runtime as Record<string, unknown>).workflowContract;
    if (nested && typeof nested === 'object' && !Array.isArray(nested)) {
      return nested as Record<string, unknown>;
    }
  }
  const rawV2 = dictOrEmpty(root.__unified_page_contract_v2);
  const rawDirect = dictOrEmpty(rawV2.workflowContract);
  if (Object.keys(rawDirect).length) return rawDirect;
  const rawRuntime = dictOrEmpty(rawV2.runtimeContract);
  const rawNested = dictOrEmpty(rawRuntime.workflowContract);
  if (Object.keys(rawNested).length) return rawNested;
  return {};
}

function workflowContractActionRows(): Array<Record<string, unknown>> {
  if (!recordId.value) return [];
  return normalizeWorkflowActionRows(currentWorkflowContract(), model.value);
}

function blockingWorkflowEvidenceMessage() {
  const row = workflowEvidenceGateRows.value.find((item) => item.blocking);
  return row?.message || '';
}

function applyWorkflowContractToAction(action: ContractAction): ContractAction {
  const workflow = currentWorkflowContract();
  if (!recordId.value || !action.methodName || !isWorkflowTransitionMethod(workflow, action.methodName)) return action;
  const workflowRow = workflowActionRowForMethod(workflow, action.methodName);
  const blockingMessage = blockingWorkflowEvidenceMessage();
  if (!workflowRow) {
    return {
      ...action,
      enabled: false,
      hint: blockingMessage || '当前流程状态不允许执行该操作',
    };
  }
  if (workflowRow.enabled === false) {
    return {
      ...action,
      enabled: false,
      hint: String(workflowRow.blocked_message || workflowRow.message || blockingMessage || workflowRow.reason_code || workflowRow.reasonCode || '').trim(),
    };
  }
  return action;
}

function hasWorkflowContractActions() {
  const workflow = currentWorkflowContract();
  return Array.isArray(workflow.availableActions);
}

function shouldShowWorkflowNativeAction(methodName: string) {
  const method = String(methodName || '').trim();
  const workflow = currentWorkflowContract();
  if (!recordId.value || !method || !hasWorkflowContractActions() || !isWorkflowTransitionMethod(workflow, method)) return true;
  return Boolean(workflowActionRowForMethod(workflow, method));
}

const workflowEvidenceGateRows = computed(() => {
  return normalizeWorkflowEvidenceGateRows(currentWorkflowContract());
});

const contractActions = computed<ContractAction[]>(() => {
  const mapSceneReadyAction = (row: Record<string, unknown>): ContractAction | null => {
    const protocol = normalizeSceneActionProtocol(row);
    const key = String(row.key || '').trim();
    if (!key) return null;
    const target = parseMaybeJsonRecord(row.target);
    const intent = String(row.intent || '').trim().toLowerCase();
    const tier = String(row.tier || '').trim().toLowerCase();
    const placement = String(row.placement || 'header').trim().toLowerCase();
    const actionId = toActionId(target.action_id) ?? toActionId(target.ref);
    const hasOpenTarget = Boolean(actionId || String(target.url || '').trim() || String(target.route || '').trim());
    const kind = hasOpenTarget || intent === 'ui.contract' ? 'open' : 'object';
    const semantic = tier === 'primary'
      ? 'primary_action'
      : tier === 'secondary'
        ? 'secondary_action'
        : '';
    return {
      key,
      label: String(row.label || key),
      kind,
      level: placement,
      selection: 'none',
      actionId,
      methodName: detectMethodName(key, String(target.method || '').trim()),
      targetModel: String(target.model || model.value || '').trim(),
      context: parseMaybeJsonRecord(target.context_raw),
      domainRaw: String(target.domain_raw || '').trim(),
      target: String(target.target || '').trim(),
      url: String(target.url || target.route || '').trim(),
      enabled: true,
      hint: '',
      intent,
      semantic,
      sourceWidgetId: String(row.sourceWidgetId || row.source_widget_id || '').trim(),
      clientMode: String(target.mode || target.client_mode || row.clientMode || row.client_mode || '').trim(),
      visibleProfiles: ['create', 'edit', 'readonly'],
      requiredParams: normalizeRequiredParams(row.required_params),
      requiresReason: row.requires_reason === true,
      actionSafety: normalizeActionSafety(row.action_safety),
      mutation: protocol?.mutation,
      refreshPolicy: protocol?.refresh_policy,
    };
  };

  const sceneReadyActions = useSceneFormAugmentations.value && Array.isArray(sceneReadyFormSurface.value.actions)
    ? sceneReadyFormSurface.value.actions as Array<Record<string, unknown>>
    : [];
  const storeButtonStatus = collectContractV2ButtonStatusById(v2ContractStore.value);
  const v2ButtonStatus = Object.keys(storeButtonStatus).length
    ? storeButtonStatus
    : collectUnifiedPageContractV2ButtonStatus(contract.value);
  const merged: Array<Record<string, unknown>> = [];
  const workflowRows = workflowContractActionRows();
  const workflowMethods = new Set<string>();
  workflowRows.forEach((row) => {
    const method = String(parseMaybeJsonRecord(row.payload).method || '').trim();
    if (method) workflowMethods.add(method);
    workflowActionMethodAliases(String(row.key || '').trim()).forEach((alias) => workflowMethods.add(alias));
  });
  if (workflowRows.length) {
    merged.push(...workflowRows);
  }
  const nativeFormContract = contract.value?.views?.form as Record<string, unknown> | undefined;
  if (Array.isArray(nativeFormContract?.header_buttons)) {
    merged.push(...(nativeFormContract.header_buttons as Array<Record<string, unknown>>));
  }
  if (Array.isArray(nativeFormContract?.button_box)) {
    merged.push(...(nativeFormContract.button_box as Array<Record<string, unknown>>));
  }
  if (Array.isArray(nativeFormContract?.business_actions)) {
    merged.push(...(nativeFormContract.business_actions as Array<Record<string, unknown>>));
  }
  if (Array.isArray(contract.value?.buttons)) merged.push(...(contract.value?.buttons as Array<Record<string, unknown>>));
  if (Array.isArray(contract.value?.toolbar?.header)) merged.push(...(contract.value?.toolbar?.header as Array<Record<string, unknown>>));
  if (Array.isArray(contract.value?.toolbar?.sidebar)) merged.push(...(contract.value?.toolbar?.sidebar as Array<Record<string, unknown>>));
  if (Array.isArray(contract.value?.toolbar?.footer)) merged.push(...(contract.value?.toolbar?.footer as Array<Record<string, unknown>>));
  const v2ActionRules = resolveUnifiedPageContractV2(contract.value)?.actionContract;
  const v2ActionRuleList = parseMaybeJsonRecord(v2ActionRules).actionRuleList;
  if (Array.isArray(v2ActionRuleList)) {
    v2ActionRuleList.forEach((raw) => {
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return;
      const row = raw as Record<string, unknown>;
      const sourceWidgetId = String(row.sourceWidgetId || row.source_widget_id || '').trim();
      const targetScope = String(row.targetScope || row.target_scope || '').trim().toLowerCase();
      const triggerType = String(row.triggerType || row.trigger_type || '').trim();
      if (triggerType && triggerType !== 'click') return;
      const key = String(row.actionKey || row.key || row.actionId || '').trim();
      if (!key) return;
      const target = parseMaybeJsonRecord(row.target);
      const button = parseMaybeJsonRecord(row.button);
      const clientMode = String(target.mode || target.client_mode || '').trim();
      const intent = String(row.intent || '').trim();
      const buttonType = String(button.type || button.buttonType || '').trim();
      const buttonName = String(button.name || button.method || '').trim();
      const isRootObjectAction = sourceWidgetId === 'page.root' && Boolean(buttonName);
      if (sourceWidgetId !== 'page.header' && targetScope !== 'footer' && !isRootObjectAction) return;
      const actionKind = buttonType === 'server' || buttonType === 'server_action'
        ? 'server'
        : buttonName
          ? 'object'
          : (clientMode ? 'client' : 'open');
      merged.push({
        key,
        label: String(row.label || key).trim() || key,
        kind: actionKind,
        intent,
        level: targetScope === 'footer' ? 'footer' : 'header',
        selection: 'none',
        sourceWidgetId,
        target,
        target_model: String(target.model || '').trim(),
        payload: {
          method: buttonName,
          type: buttonType,
          action_id: target.action_id,
          ref: target.ref,
          url: target.url || target.route,
          target: target.target,
          mode: clientMode,
          client_mode: clientMode,
          domain_raw: target.domain_raw,
          context_raw: target.context_raw,
        },
        visible_profiles: ['create', 'edit', 'readonly'],
      });
    });
  }
  if (sceneReadyActions.length) {
    merged.push(...sceneReadyActions);
  }

  const dedup = new Set<string>();
  const out: ContractAction[] = [];
  for (const row of merged) {
    if (sceneReadyActions.length && !String(row.key || '').trim()) {
      const mapped = mapSceneReadyAction(row);
      if (!mapped || dedup.has(mapped.key)) continue;
      const status = resolveV2ButtonStatus(mapped.key, v2ButtonStatus);
      if (status?.visible === false) continue;
      if (status?.disabled === true) {
        mapped.enabled = false;
        mapped.hint = status.reasonCode || mapped.hint || 'disabled_by_status_contract';
      }
      dedup.add(mapped.key);
      out.push(mapped);
      continue;
    }
    if (sceneReadyActions.includes(row)) {
      const mapped = mapSceneReadyAction(row);
      if (!mapped || dedup.has(mapped.key)) continue;
      const status = resolveV2ButtonStatus(mapped.key, v2ButtonStatus);
      if (status?.visible === false) continue;
      if (status?.disabled === true) {
        mapped.enabled = false;
        mapped.hint = status.reasonCode || mapped.hint || 'disabled_by_status_contract';
      }
      dedup.add(mapped.key);
      out.push(mapped);
      continue;
    }
    const rowName = String(row.name || '').trim();
    const rowLabel = normalizeActionLabel(row.label);
    const keyBase = String(row.key || rowName || rowLabel || '').trim();
    const key = dedup.has(keyBase) && rowLabel ? `${keyBase}:${rowLabel}` : keyBase;
    if (!key || dedup.has(key)) continue;
    dedup.add(key);
    const payload = parseMaybeJsonRecord(row.payload);
    const kind = normalizeActionKind(row.kind);
    const protocol = normalizeSceneActionProtocol(row);
    const targetRaw = parseMaybeJsonRecord(row.target);
    const rowIntent = String(row.intent || '').trim();
    const effectiveKind = protocol?.mutation ? 'mutation' : kind;
    const level = String(row.level || 'body').trim().toLowerCase();
    const actionId = toActionId(payload.action_id) ?? toActionId(payload.ref) ?? toActionId(row.actionId) ?? toActionId(row.action_id);
    const methodName = detectMethodName(key, String(payload.method || '').trim());
    const isWorkflowContractAction = row.workflow_contract_action === true;
    if (!isWorkflowContractAction && methodName && workflowMethods.has(methodName)) continue;
    if (isTierValidationActionHidden(methodName)) continue;
    const targetModel = String(row.target_model || row.model || model.value || '').trim();
    const context = parseMaybeJsonRecord(payload.context_raw);
    const domainRaw = String(payload.domain_raw || '').trim();
    const target = String(payload.target || '').trim();
    const selectionRaw = String(row.selection || 'none').trim().toLowerCase();
    const selection = selectionRaw === 'single' || selectionRaw === 'multi' ? selectionRaw : 'none';
    const visibleProfiles = (
      Array.isArray(row.visible_profiles) ? row.visible_profiles : ['create', 'edit']
    )
      .map((item) => String(item || '').trim().toLowerCase())
      .filter((item): item is 'create' | 'edit' | 'readonly' => item === 'create' || item === 'edit' || item === 'readonly');
    const requiredParams = normalizeRequiredParams(row.required_params);
    const policy = evaluateActionPolicy(contract.value, key, policyContext.value);
    if (!policy.visible) continue;
    if (!evaluateNativeActionVisibility(row)) continue;
    const status = resolveV2ButtonStatus(key, v2ButtonStatus);
    if (status?.visible === false) continue;
    const contractAllowed = typeof row.allowed === 'boolean' ? Boolean(row.allowed) : true;
    const needRecord = effectiveKind === 'object' || effectiveKind === 'server' || effectiveKind === 'mutation' || level === 'row' || level === 'smart';
    const blockedMessage = String(row.blocked_message || row.reason || row.reason_code || '').trim();
    const warningMessage = String(row.warning_message || '').trim();
    const enabled = contractAllowed && policy.enabled && (!needRecord || Boolean(recordId.value)) && status?.disabled !== true;
    out.push({
      key,
      label: normalizeActionLabel(row.label, key),
      kind: effectiveKind,
      level,
      selection,
      actionId,
      methodName,
      targetModel,
      context,
      domainRaw,
      target,
      url: String(payload.url || row.url || '').trim(),
      enabled,
      hint: status?.disabled === true
        ? status.reasonCode || 'disabled_by_status_contract'
        : (needRecord && !recordId.value ? 'requires record id' : (contractAllowed ? (warningMessage || policy.reason) : blockedMessage)),
      intent: rowIntent,
      semantic: policy.semantic,
      sourceWidgetId: String(row.sourceWidgetId || row.source_widget_id || '').trim(),
      clientMode: String(targetRaw.mode || targetRaw.client_mode || row.clientMode || row.client_mode || '').trim(),
      visibleProfiles,
      requiredParams,
      requiresReason: row.requires_reason === true || requiredParams.includes('reason'),
      actionSafety: normalizeActionSafety(row.action_safety),
      mutation: protocol?.mutation,
      refreshPolicy: protocol?.refresh_policy,
    });
  }
  if (
    model.value === 'payment.request'
    && recordId.value
    && String(formData.type || 'pay').trim() === 'pay'
    && !out.some((item) => item.methodName === 'action_create_payment_execution')
  ) {
    out.push({
      key: 'action_create_payment_execution',
      label: '生成付款登记',
      kind: 'object',
      level: 'header',
      selection: 'none',
      actionId: null,
      methodName: 'action_create_payment_execution',
      targetModel: 'payment.request',
      context: {},
      domainRaw: '',
      target: '',
      url: '',
      enabled: true,
      hint: '',
      intent: '',
      semantic: 'secondary_action',
      sourceWidgetId: '',
      clientMode: '',
      visibleProfiles: ['edit', 'readonly'],
      requiredParams: [],
      requiresReason: false,
    });
  }
  return out.sort((a, b) => {
    const levelDelta = a.level.localeCompare(b.level);
    if (levelDelta !== 0) return levelDelta;
    return a.label.localeCompare(b.label, 'zh-CN');
  }).filter((item) => {
    const profiles = Array.isArray(item.visibleProfiles) ? item.visibleProfiles : [];
    if (profiles.length && !profiles.includes(renderProfile.value)) return false;
    if (item.selection !== 'none') return false;
    return item.level !== 'toolbar';
  });
});

const headerActions = computed(() => contractActions.value.filter((item) => item.level === 'header' || item.level === 'toolbar'));
const bodyActions = computed(() => contractActions.value.filter((item) => item.level !== 'header' && item.level !== 'toolbar'));

const contractFieldLabels = computed<Record<string, string>>(() => {
  const labels: Record<string, string> = {};
  const snapshot = dictOrEmpty(v2ContractStore.value?.snapshot);
  const source = Object.keys(snapshot).length ? snapshot : contract.value;
  const businessProfile = resolveUnifiedPageContractV2BusinessOperationProfile(source);
  Object.entries(dictOrEmpty(businessProfile.field_labels)).forEach(([name, value]) => {
    const label = String(value || '').trim();
    if (name && label) labels[name] = label;
  });
  mergeFieldLabelsFromSource(resolveUnifiedPageContractV2FormStructureContract(source), labels);
  mergeFieldLabelsFromSource(snapshot.formStructureContract, labels);
  mergeFieldLabelsFromSource((contract.value as Record<string, unknown> | null | undefined)?.formStructureContract, labels);
  return labels;
});

function contractFieldLabel(name: string) {
  return contractFieldLabels.value[String(name || '').trim()] || '';
}

const runtimeCollaborationContract = computed(() => {
  return resolveRuntimeCollaborationContract(
    v2ContractStore.value?.snapshot?.runtimeContract,
    (contract.value as Record<string, unknown> | null | undefined)?.runtimeContract,
  );
});

const nativeChatterContract = computed(() => {
  return resolveNativeChatterContract(contract.value?.views?.form, runtimeCollaborationContract.value);
});

const nativeAttachmentContract = computed(() => {
  return resolveNativeAttachmentContract(contract.value?.views?.form, runtimeCollaborationContract.value);
});

const nativeChatterActions = computed<NativeChatterAction[]>(() => {
  return nativeChatterActionsFromContract(nativeChatterContract.value, {
    recordId: recordId.value,
    model: model.value,
  });
});

const nativeChatterTitle = computed(() => {
  const chatter = nativeChatterContract.value;
  return String(chatter?.label || '').trim();
});

const nativeCollaborationTitle = computed(() => nativeChatterTitle.value || '协作日志');
const nativeCollaborationUnavailableMessage = computed(() => {
  if (recordId.value && model.value) return '';
  if (renderProfile.value === 'create') {
    return nativeAttachments.value
      ? '保存草稿或提交生成单据后，可记录沟通、记录备注和安排计划；附件会随保存草稿或提交一起上传。'
      : '保存草稿或提交生成单据后，可记录沟通、记录备注和安排计划。';
  }
  return '当前记录尚未加载完成，暂不能写入协作日志。';
});

const activeChatterSubmitLabel = computed(() => {
  if (activeChatterMode.value === 'activity') return activeChatterLabel.value || '安排计划';
  if (activeChatterMode.value === 'note') return '记录备注';
  return '记录沟通';
});

const activeChatterPostingLabel = computed(() => (activeChatterMode.value === 'activity' ? '安排中...' : '发布中...'));

const activeChatterPlaceholder = computed(() => {
  if (activeChatterMode.value === 'note') return '输入备注内容';
  return '输入沟通内容';
});

const activeChatterIsActivity = computed(() => activeChatterMode.value === 'activity');

const activeActivityAction = computed(() => (
  nativeChatterActions.value.find((item) => item.mode === 'activity' && item.label === activeChatterLabel.value)
  || nativeChatterActions.value.find((item) => item.mode === 'activity')
  || null
));

function activityFieldLabel(name: string, fallback: string) {
  return nativeActivityFieldLabel(activeActivityAction.value, name, fallback);
}

const activitySummaryLabel = computed(() => activityFieldLabel('summary', '摘要'));
const activityDeadlineLabel = computed(() => activityFieldLabel('date_deadline', '截止日期'));
const activityNoteLabel = computed(() => activityFieldLabel('note', '备注'));
const activitySummaryPlaceholder = computed(() => `填写需要跟进的计划事项，例如：补充资料、确认付款、复核合同`);
const activityNotePlaceholder = computed(() => '补充计划背景、办理要求或注意事项');
const selectedMentionUsers = computed(() => {
  const selected = new Set(selectedMentionUserIds.value);
  return collaborationUserOptions.value.filter((item) => selected.has(Number(item.id || 0)));
});
const collaborationUserChoices = computed(() => {
  const selected = new Set(selectedMentionUserIds.value);
  return collaborationUserOptions.value.filter((item) => !selected.has(Number(item.id || 0)));
});
const activityAssigneeOptions = computed(() => collaborationUserOptions.value);
const activityAssigneeLabel = computed(() => activityFieldLabel('user_id', '指派给'));

const isNativeChatterSubmitDisabled = computed(() => {
  if (chatterPosting.value) return true;
  if (activeChatterMode.value === 'activity') return !activitySummary.value.trim();
  return !chatterDraft.value.trim();
});

const nativeAttachments = computed(() => {
  return nativeAttachmentContractOrNull(nativeAttachmentContract.value);
});

const nativeAttachmentLabels = computed<Record<string, string>>(() => {
  return nativeAttachmentLabelsFromContract(nativeAttachments.value);
});

function resolveNativeAttachmentLabel(key: string, fallback: string) {
  return nativeAttachmentLabel(nativeAttachmentLabels.value, key, fallback);
}

const nativeAttachmentUploadLabel = computed(() => resolveNativeAttachmentLabel('upload', '上传附件'));
const nativeAttachmentUploadingLabel = computed(() => resolveNativeAttachmentLabel('uploading', '上传中...'));
const nativeAttachmentViewLabel = computed(() => resolveNativeAttachmentLabel('view', '查看'));
const nativeAttachmentMaxBytes = computed(() => nativeAttachmentMaxBytesFromContract(nativeAttachments.value));

const hasNativeChatterNode = computed(() => nativeLayoutContainsType(nativeFormLayoutNodes.value, 'chatter'));

function nativeLayoutContainsType(nodes: NativeFormLayoutNode[], type: string): boolean {
  return layoutContainsType(nodes as Array<Record<string, unknown>>, type);
}

function contractActionFromNativeRow(row: Record<string, unknown>): ContractAction | null {
  const nativeAction = row.action && typeof row.action === 'object' && !Array.isArray(row.action)
    ? row.action as Record<string, unknown>
    : {};
  const payload = parseMaybeJsonRecord(nativeAction.payload || row.payload);
  const rowName = String(nativeAction.name || row.name || payload.method || payload.ref || '').trim();
  const rowLabel = String(nativeAction.label || row.label || '').trim();
  const key = String(nativeAction.key || row.key || rowName || rowLabel || '').trim();
  if (!key) return null;
  const kind = normalizeActionKind(
    nativeAction.kind || row.kind || row.buttonType || payload.type || row.type || (rowName ? 'object' : ''),
  );
  const level = String(nativeAction.level || row.level || 'body').trim().toLowerCase();
  const actionId = toActionId(payload.action_id) ?? toActionId(payload.ref) ?? toActionId(row.action_id) ?? toActionId(row.ref);
  const methodName = detectMethodName(
    key,
    String(payload.method || row.method || (kind === 'object' || kind === 'server' ? rowName : '') || '').trim(),
  );
  if (!shouldShowWorkflowNativeAction(methodName)) return null;
  const needRecord = kind === 'object' || kind === 'server' || level === 'row' || level === 'smart';
  return applyWorkflowContractToAction({
    key,
    label: rowLabel || key,
    kind,
    level,
    selection: 'none',
    actionId,
    methodName,
    targetModel: String(row.target_model || row.model || payload.model || model.value || '').trim(),
    context: parseMaybeJsonRecord(payload.context_raw || row.context),
    domainRaw: String(payload.domain_raw || row.domain_raw || '').trim(),
    target: String(payload.target || row.target || '').trim(),
    url: String(payload.url || row.url || '').trim(),
    enabled: !needRecord || Boolean(recordId.value),
    hint: needRecord && !recordId.value ? 'requires record id' : '',
    intent: String(nativeAction.intent || row.intent || '').trim(),
    semantic: '',
    sourceWidgetId: String(row.sourceWidgetId || row.source_widget_id || '').trim(),
    clientMode: '',
    visibleProfiles: ['create', 'edit', 'readonly'],
    requiredParams: normalizeRequiredParams(nativeAction.required_params || row.required_params),
    requiresReason: nativeAction.requires_reason === true || row.requires_reason === true,
    actionSafety: normalizeActionSafety(nativeAction.action_safety || row.action_safety),
  });
}

function resolveNativeActionState(row: Record<string, unknown>) {
  const action = contractActionFromNativeRow(row);
  if (!action) return {};
  return {
    disabled: busy.value || !action.enabled,
    title: action.hint || '',
  };
}

function isUnifiedSubmitMethod(methodName: string) {
  const method = String(methodName || '').trim();
  return method === 'action_submit'
    || method === 'action_submit_progress'
    || method === 'action_confirm'
    || method === 'button_confirm';
}

function isUnifiedSubmitAction(action: ContractAction | null | undefined) {
  return Boolean(action && isUnifiedSubmitMethod(action.methodName));
}

function nativeHeaderSubmitActionForCreate(): ContractAction | null {
  const nativeFormContract = contract.value?.views?.form as Record<string, unknown> | undefined;
  const rows = Array.isArray(nativeFormContract?.header_buttons)
    ? nativeFormContract.header_buttons as Array<Record<string, unknown>>
    : [];
  for (const row of rows) {
    const action = contractActionFromNativeRow(row);
    if (!isUnifiedSubmitAction(action)) continue;
    return {
      ...action,
      enabled: true,
      hint: '',
    };
  }
  return null;
}

const primarySubmitAction = computed<ContractAction | null>(() => {
  if (isProjectIntakeCreateMode.value) return null;
  if (!model.value) return null;
  if (!recordId.value) return nativeHeaderSubmitActionForCreate();
  const visibleAction = headerActions.value.find((action) => isUnifiedSubmitAction(action) && action.enabled);
  return visibleAction || null;
});

function rawCreateRootActionCandidates(): ContractAction[] {
  const v2 = resolveUnifiedPageContractV2(contract.value);
  const rows = parseMaybeJsonRecord(v2?.actionContract).actionRuleList;
  if (!Array.isArray(rows)) return [];
  return rows
    .map((raw) => (raw && typeof raw === 'object' && !Array.isArray(raw) ? raw as Record<string, unknown> : null))
    .filter((row): row is Record<string, unknown> => Boolean(row))
    .map((row) => {
      const sourceWidgetId = String(row.sourceWidgetId || row.source_widget_id || '').trim();
      const targetScope = String(row.targetScope || row.target_scope || '').trim().toLowerCase();
      const button = parseMaybeJsonRecord(row.button);
      const buttonName = String(button.name || '').trim();
      const buttonType = String(button.type || 'object').trim();
      const normalizedIntent = String(row.intent || 'execute_button').trim().toLowerCase();
      const normalizedButtonType = buttonType.toLowerCase();
      if (
        !buttonName
        || sourceWidgetId !== 'page.root'
        || (targetScope && targetScope !== 'header' && targetScope !== 'footer')
        || (normalizedIntent && normalizedIntent !== 'execute' && normalizedIntent !== 'execute_button')
        || (normalizedButtonType && normalizedButtonType !== 'object' && normalizedButtonType !== 'server' && normalizedButtonType !== 'server_action')
      ) {
        return null;
      }
      return {
        key: String(row.actionKey || row.key || row.actionId || buttonName).trim() || buttonName,
        label: String(row.label || buttonName).trim() || buttonName,
        kind: buttonType === 'server' || buttonType === 'server_action' ? 'server' : 'object',
        level: targetScope === 'footer' ? 'footer' : 'header',
        selection: 'none' as const,
        actionId: null,
        methodName: buttonName,
        targetModel: String(model.value || '').trim(),
        context: {},
        domainRaw: '',
        target: '',
        url: '',
        enabled: true,
        hint: '',
        intent: String(row.intent || 'execute_button').trim(),
        semantic: 'primary_action',
        sourceWidgetId,
        clientMode: '',
        visibleProfiles: ['create', 'edit', 'readonly'] as Array<'create' | 'edit' | 'readonly'>,
        requiredParams: [],
        requiresReason: false,
      };
    })
    .filter(Boolean) as ContractAction[];
}

const primaryCreateFooterAction = computed<ContractAction | null>(() => {
  if (isProjectIntakeCreateMode.value) return null;
  if (!model.value || recordId.value) return null;
  if (primarySubmitAction.value) return null;
  const mappedCandidates = contractActions.value.filter((action) => {
    const level = String(action.level || '').trim().toLowerCase();
    const kind = String(action.kind || '').trim().toLowerCase();
    const source = String(action.sourceWidgetId || '').trim();
    const isWizardRootAction = source === 'page.root' && level === 'header';
    return (level === 'footer' || isWizardRootAction)
      && (kind === 'object' || kind === 'server')
      && Boolean(action.methodName)
      && action.selection === 'none';
  });
  const candidates = mappedCandidates.length ? mappedCandidates : rawCreateRootActionCandidates();
  if (candidates.length !== 1) return null;
  return {
    ...candidates[0],
    enabled: true,
    hint: '',
  };
});

function actionResponseNavQuery(result: object | null | undefined, extra?: Record<string, unknown>) {
  return actionResponseNavQueryFromResult(route.query as Record<string, unknown>, result, extra);
}

function actionResponseRouteTarget(target: unknown, result: object | null | undefined, extra?: Record<string, unknown>) {
  return actionResponseRouteTargetFromResult(route.query as Record<string, unknown>, target, result, extra);
}

async function runNativeLayoutAction(row: Record<string, unknown>) {
  const action = contractActionFromNativeRow(row);
  if (!action) return;
  if ((action.kind === 'object' || action.kind === 'server') && action.methodName && recordId.value) {
    if (!action.enabled || !await confirmActionSafety(action)) return;
    if (!await ensureSavedBeforeRecordAction()) return;
    busyKind.value = 'action';
    try {
      const response = await executeButton({
        model: action.targetModel || model.value,
        res_id: recordId.value,
        button: { name: action.methodName, type: action.kind === 'server' ? 'server' : 'object' },
        context: action.context,
        meta: {
          menu_id: Number(route.query.menu_id || 0) || undefined,
          action_id: actionId.value || undefined,
        },
      });
      const result = response?.result;
      if (result?.entry_target) {
        await router.push(actionResponseRouteTarget(buildEntryTargetRouteTarget(result.entry_target, {
          query: actionResponseNavQuery(result),
          actionId: result.action_id,
        }), result) as never);
        return;
      }
      const nextActionId = toPositiveInt(result?.action_id);
      if (nextActionId) {
        await router.push({
          name: 'action',
          params: { actionId: String(nextActionId) },
          query: actionResponseNavQuery(result, { action_id: nextActionId }),
        });
        return;
      }
      await reload();
      return;
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : '操作执行失败';
      status.value = 'error';
      return;
    } finally {
      busyKind.value = null;
    }
  }
  await runAction(action);
}

type SemanticFieldGroup = {
  name: string;
  label: string;
  collapsible: boolean;
  fields: string[];
};

const semanticFieldGroups = computed<Record<string, SemanticFieldGroup>>(() => {
  const snapshot = dictOrEmpty(v2ContractStore.value?.snapshot);
  const source = Object.keys(snapshot).length ? snapshot : contract.value;
  const raw = resolveUnifiedPageContractV2FieldGroups(source);
  const out: Record<string, SemanticFieldGroup> = {};
  for (const item of raw || []) {
    if (!item || typeof item !== 'object') continue;
    const row = item as Record<string, unknown>;
    const key = String(row.name || '').trim().toLowerCase();
    if (!key) continue;
    const fields = Array.isArray(row.fields) ? row.fields.map((f) => String(f || '').trim()).filter(Boolean) : [];
    out[key] = {
      name: key,
      label: String(row.label || (key === 'core' ? '核心信息' : '高级信息')).trim(),
      collapsible: Boolean(row.collapsible),
      fields,
    };
  }
  if (!Object.keys(out).length) {
    const profile = ((contract.value?.views?.form as Record<string, unknown> | undefined)?.form_profile
      || (contract.value as Record<string, unknown> | undefined)?.form_profile) as Record<string, unknown> | undefined;
    const core = Array.isArray(profile?.core_fields)
      ? profile?.core_fields.map((f) => String(f || '').trim()).filter(Boolean)
      : [];
    const advanced = Array.isArray(profile?.advanced_fields)
      ? profile?.advanced_fields.map((f) => String(f || '').trim()).filter(Boolean)
      : [];
    if (core.length || advanced.length) {
      out.core = {
        name: 'core',
        label: '核心信息',
        collapsible: false,
        fields: core,
      };
      out.advanced = {
        name: 'advanced',
        label: '高级信息',
        collapsible: true,
        fields: advanced,
      };
    }
  }
  return out;
});

const contractFieldSemantics = computed<Record<string, { semantic_type?: string; surface_role?: string; technical?: boolean }>>(() => {
  const out: Record<string, { semantic_type?: string; surface_role?: string; technical?: boolean }> = {};
  const raw = (contract.value as Record<string, unknown> | null)?.field_semantics;
  if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
    Object.entries(raw as Record<string, unknown>).forEach(([name, value]) => {
      if (!value || typeof value !== 'object' || Array.isArray(value)) return;
      const row = value as Record<string, unknown>;
      out[name] = {
        semantic_type: String(row.semantic_type || '').trim().toLowerCase(),
        surface_role: String(row.surface_role || '').trim().toLowerCase(),
        technical: Boolean(row.technical),
      };
    });
  }
  return out;
});

function fieldSemanticMeta(name: string) {
  const fromMap = contractFieldSemantics.value[name];
  if (fromMap) return fromMap;
  const descriptor = contract.value?.fields?.[name] as Record<string, unknown> | undefined;
  return {
    semantic_type: String(descriptor?.semantic_type || '').trim().toLowerCase(),
    surface_role: String(descriptor?.surface_role || '').trim().toLowerCase(),
    technical: Boolean(descriptor?.technical),
  };
}

const coreFieldNames = computed<string[]>(() => {
  const fromSemantic = Object.keys(contract.value?.fields || {}).filter((name) => fieldSemanticMeta(name).surface_role === 'core');
  if (fromSemantic.length) return fromSemantic;
  return semanticFieldGroups.value.core?.fields || [];
});
const advancedFieldNames = computed<string[]>(() => {
  const fromSemantic = Object.keys(contract.value?.fields || {}).filter((name) => fieldSemanticMeta(name).surface_role === 'advanced');
  if (fromSemantic.length) return fromSemantic;
  return semanticFieldGroups.value.advanced?.fields || [];
});
const hasAdvancedFields = computed(() => advancedFieldNames.value.length > 0);
const policyRequiredFields = computed(() => {
  const out = new Set<string>();
  const map = (contract.value?.action_policies || {}) as Record<string, { semantic?: string; enabled_when?: { required_fields?: string[] } }>;
  Object.values(map).forEach((policy) => {
    const semantic = String(policy?.semantic || '').trim().toLowerCase();
    if (semantic !== 'primary_action') return;
    const requiredFields = Array.isArray(policy?.enabled_when?.required_fields)
      ? policy.enabled_when?.required_fields
      : [];
    requiredFields.forEach((field) => {
      const normalized = String(field || '').trim();
      if (normalized) out.add(normalized);
    });
  });
  return out;
});
const sceneReadySceneKey = computed(() => String(
  route.query.scene_key
  || route.params.sceneKey
  || findActionMeta(session.menuTree, actionId.value)?.scene_key
  || findActionMeta(session.menuTree, actionId.value)?.sceneKey
  || session.currentAction?.scene_key
  || session.currentAction?.sceneKey
  || '',
).trim());
const sceneReadyHydrateRequested = ref(false);
const useSceneFormAugmentations = computed(() => {
  if (isProjectIntakeCreateMode.value) return true;
  return Boolean(sceneReadySceneKey.value);
});
const sceneReadyEntry = computed<Record<string, unknown> | null>(() => {
  if (!useSceneFormAugmentations.value) return null;
  const key = sceneReadySceneKey.value;
  return key ? findSceneReadyEntry(session.sceneReadyContractV1, key) : null;
});
const strictContractMode = computed(() => isCoreSceneStrictMode(sceneReadySceneKey.value, sceneReadyEntry.value));
const strictContractGuard = computed<Record<string, unknown>>(() => {
  const entry = (sceneReadyEntry.value && typeof sceneReadyEntry.value === 'object')
    ? (sceneReadyEntry.value as Record<string, unknown>)
    : {};
  const direct = entry.contract_guard;
  if (direct && typeof direct === 'object' && !Array.isArray(direct)) return direct as Record<string, unknown>;
  const meta = (entry.meta && typeof entry.meta === 'object' && !Array.isArray(entry.meta))
    ? (entry.meta as Record<string, unknown>)
    : {};
  const nested = meta.contract_guard;
  if (nested && typeof nested === 'object' && !Array.isArray(nested)) return nested as Record<string, unknown>;
  return {};
});
const strictContractMissingSummary = computed(() => {
  if (!strictContractMode.value) return '';
  const raw = strictContractGuard.value.missing;
  if (!Array.isArray(raw) || !raw.length) return '';
  const missing = raw.map((item) => String(item || '').trim()).filter(Boolean);
  if (!missing.length) return '';
  return `严格模式检测到页面配置不完整：${missing.join(', ')}`;
});
const strictContractDefaultsSummary = computed(() => {
  if (!strictContractMode.value) return '';
  const raw = strictContractGuard.value.defaults_applied;
  if (!Array.isArray(raw) || !raw.length) return '';
  const defaults = raw.map((item) => String(item || '').trim()).filter(Boolean);
  if (!defaults.length) return '';
  return `系统已自动补齐：${defaults.join(', ')}`;
});
const sceneValidationRequiredFields = computed<string[]>(() => {
  if (!useSceneFormAugmentations.value) return [];
  return resolveFormSceneReady(sceneReadyEntry.value).requiredFields;
});
const sceneReadyFormSurface = computed(() => {
  if (!useSceneFormAugmentations.value) return resolveFormSceneReady(null);
  return resolveFormSceneReady(sceneReadyEntry.value);
});
watch(
  () => [sceneReadySceneKey.value, sceneReadyFormSurface.value.sceneBlocks.length],
  async ([sceneKey, blockCount]) => {
    if (!sceneKey || Number(blockCount || 0) > 0 || sceneReadyHydrateRequested.value) return;
    sceneReadyHydrateRequested.value = true;
    try {
      const result = await intentRequest<Record<string, unknown>>({
        intent: 'system.init',
        params: {
          scene: 'web',
          with_preload: false,
          scene_ready_mode: 'full',
          with: ['workspace_home'],
          ...(config.startupRootXmlid ? { root_xmlid: config.startupRootXmlid } : {}),
          scene_key: sceneKey,
        },
        meta: { startup_chain_bypass: true },
      });
      const contract = result.scene_ready_contract_v1;
      if (contract && typeof contract === 'object' && Array.isArray((contract as Record<string, unknown>).scenes)) {
        session.sceneReadyContractV1 = contract as never;
      }
    } catch (err) {
      void err;
    }
  },
  { immediate: true },
);
const validationRequiredFields = computed(() => {
  const out = new Set<string>();
  const rules = Array.isArray(contract.value?.validation_rules) ? contract.value.validation_rules : [];
  rules.forEach((rule) => {
    if (!rule || typeof rule !== 'object') return;
    const item = rule as Record<string, unknown>;
    if (String(item.code || '').trim().toUpperCase() !== 'REQUIRED') return;
    const field = String(item.field || '').trim();
    if (!field) return;
    const profiles = Array.isArray(item.when_profiles)
      ? item.when_profiles.map((p) => String(p || '').trim().toLowerCase())
      : [];
    if (profiles.length && !profiles.includes(renderProfile.value)) return;
    out.add(field);
  });
  sceneValidationRequiredFields.value.forEach((field) => {
    out.add(field);
  });
  return out;
});
const sceneValidationErrorPrefix = `${ErrorCodes.SCENE_VALIDATION_REQUIRED}:`;
const sceneValidationPanel = computed(() => {
  if (!useSceneFormAugmentations.value) return null;
  const rows = validationErrors.value
    .map((item) => String(item || '').trim())
    .filter((item) => item.startsWith(sceneValidationErrorPrefix));
  if (!rows.length) return null;
  const normalized = rows
    .map((item) => item.slice(sceneValidationErrorPrefix.length).trim())
    .filter(Boolean);
  const sceneKey = String(route.query.scene_key || route.params.sceneKey || '').trim();
  const modelName = String(model.value || '').trim();
  const suggestedAction = resolveSceneValidationSuggestedAction({
    modelName,
    recordId: recordId.value,
    actionId: actionId.value,
    sceneKey,
    roleCode: runtimeRoleCode.value,
  });
  return {
    code: ErrorCodes.SCENE_VALIDATION_REQUIRED,
    message: normalized.join('；') || '场景约束校验未通过，请补齐必填字段。',
    hint: '请补齐必填字段后重试。',
    suggestedAction,
  };
});
const nonSceneValidationErrors = computed(() => (
  validationErrors.value.filter((item) => !String(item || '').trim().startsWith(sceneValidationErrorPrefix))
));
const contractVisibleFields = computed<string[]>(() => {
  const snapshot = dictOrEmpty(v2ContractStore.value?.snapshot);
  const source = Object.keys(snapshot).length ? snapshot : contract.value;
  return resolveUnifiedPageContractV2VisibleFields(source);
});

const CREATE_WORKFLOW_STATE_FIELD_NAMES = new Set([
  'state',
  'status',
  'lifecycle_state',
  'workflow_state',
  'approval_state',
  'tier_validation_state',
  'validation_state',
  'document_status',
  'document_state',
  'document_state_label',
  'legacy_document_state',
  'legacy_document_state_label',
  'legacy_visible_document_state',
]);

const fieldModifierMap = computed<Record<string, Record<string, unknown>>>(() => {
  const formView = (contract.value?.views?.form || {}) as { field_modifiers?: Record<string, Record<string, unknown>> };
  const out: Record<string, Record<string, unknown>> = { ...(formView.field_modifiers || {}) };
  const fromStore = collectContractV2FieldStatusByCode(v2ContractStore.value);
  const v2FieldStatus = Object.keys(fromStore).length ? fromStore : collectUnifiedPageContractV2FieldStatus(contract.value);
  Object.entries(v2FieldStatus).forEach(([name, status]) => {
    out[name] = {
      ...(out[name] || {}),
      ...(status.visible === false ? { invisible: true } : {}),
      ...(status.readonly === true || status.disabled === true ? { readonly: true } : {}),
      ...(status.required === true ? { required: true } : {}),
    };
  });
  return out;
});
const runtimeFieldStates = computed(() => {
  const storeFieldNames = Array.from(v2ContractStore.value?.widgetsByFieldCode.keys() || []);
  const v2FieldNames = storeFieldNames.length
    ? storeFieldNames
    : collectUnifiedPageContractV2FieldWidgets(contract.value).map((widget) => widget.fieldCode).filter(Boolean);
  const names = Array.from(new Set([...Object.keys(contract.value?.fields || {}), ...v2FieldNames]));
  return buildRuntimeFieldStates({
    fieldNames: names,
    fieldModifiers: fieldModifierMap.value,
    modifierPatch: onchangeModifiersPatch.value,
    values: formData as Record<string, unknown>,
  });
});

function runtimeState(name: string) {
  return runtimeFieldStates.value[name] || { invisible: false, readonly: false, required: false };
}

function isCreateWorkflowStateField(name: string, label = '') {
  const normalized = String(name || '').trim();
  const normalizedLabel = String(label || '').replace(/\s+/g, '').trim();
  return !recordId.value && (
    CREATE_WORKFLOW_STATE_FIELD_NAMES.has(normalized)
    || normalizedLabel === '状态'
    || normalizedLabel.endsWith('状态')
  );
}

function isFieldVisible(name: string) {
  if (isProjectQuickIntakeMode.value) {
    return ['name', 'manager_id', 'owner_id'].includes(String(name || '').trim());
  }
  const descriptor = contract.value?.fields?.[String(name || '').trim()];
  if (isCreateWorkflowStateField(name, String(contractFieldLabel(name) || descriptor?.string || ''))) return false;
  const statusField = nativeStatusbar.value.field;
  if (statusField && String(name || '').trim() === statusField) return false;
  const semantic = fieldSemanticMeta(name);
  if ((semantic.technical || semantic.semantic_type === 'technical') && !showHud.value) return false;
  if (semantic.surface_role === 'hidden' && !showHud.value) return false;
  const state = runtimeState(name);
  if (state.invisible) return false;
  const visible = contractVisibleFields.value;
  if (visible.length && !visible.includes(name)) return false;
  if (semantic.surface_role === 'core') return true;
  if (semantic.surface_role === 'advanced') return advancedExpanded.value;
  const core = coreFieldNames.value;
  const advanced = advancedFieldNames.value;
  const hasCore = core.length > 0;
  const hasAdvanced = advanced.length > 0;
  if (!hasCore && !hasAdvanced) return true;
  if (hasCore && core.includes(name)) return true;
  if (hasAdvanced && advanced.includes(name)) return advancedExpanded.value;
  // Some contracts only tag advanced fields; keep non-tagged fields visible in that case.
  if (!hasCore) return true;
  return renderProfile.value !== 'create';
}

function isWritableFieldVisible(name: string) {
  if (useNativeFormTree.value) return nativeVisibleFieldNames.value.has(String(name || '').trim());
  return isFieldVisible(name);
}

const useNativeFormTree = computed(() => {
  return nativeFormLayoutNodes.value.length > 0;
});

function filterVisibleNativeLayoutNodes(nodes: NativeFormLayoutNode[]): NativeFormLayoutNode[] {
  return nodes
    .filter((node) => isNativeLayoutNodeVisible(node))
    .map((node) => {
      const next = { ...(node as Record<string, unknown>) } as Record<string, unknown>;
      const nodeType = String(next.type || '').trim().toLowerCase();
      if (isContractFieldOrderEditable.value && nodeType === 'group') {
        const title = normalizeFieldGroupTitle(next.string || next.label || next.title);
        if (title && !effectiveGroupVisible(title)) {
          next.visible = false;
        }
      }
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const value = next[key];
        if (Array.isArray(value)) {
          next[key] = filterVisibleNativeLayoutNodes(value as NativeFormLayoutNode[]);
        }
      });
      return next as NativeFormLayoutNode;
    });
}

function applyNativeFieldOrderPreview(nodes: NativeFormLayoutNode[]): NativeFormLayoutNode[] {
  if (!fieldOrderDraft.value.length) return nodes;
  const rank = new Map(fieldOrderDraft.value.map((fieldName, index) => [fieldName, index]));
  const movedGroups = changedFieldGroupDraft();
  const movedNames = new Set(Object.keys(movedGroups));
  const movedNodes = new Map<string, NativeFormLayoutNode>();
  const collectMoved = (rows: NativeFormLayoutNode[]) => {
    rows.forEach((node) => {
      const name = String(node?.name || '').trim();
      if (isNativeFieldLayoutNode(node) && movedNames.has(name)) {
        movedNodes.set(name, node);
      }
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const value = node?.[key];
        if (Array.isArray(value)) collectMoved(value as NativeFormLayoutNode[]);
      });
    });
  };
  collectMoved(nodes);

  const sortDirectFields = (rows: NativeFormLayoutNode[]) => {
    const fields = rows.filter(isNativeFieldLayoutNode).sort((left, right) => {
      const leftRank = rank.get(String(left.name || '').trim()) ?? Number.MAX_SAFE_INTEGER;
      const rightRank = rank.get(String(right.name || '').trim()) ?? Number.MAX_SAFE_INTEGER;
      return leftRank - rightRank;
    });
    let index = 0;
    const sorted = rows.map((row) => (isNativeFieldLayoutNode(row) ? fields[index++] : row));
    return index < fields.length ? [...sorted, ...fields.slice(index)] : sorted;
  };
  const cloneWithoutMoved = (rows: NativeFormLayoutNode[]): NativeFormLayoutNode[] => rows.flatMap((node) => {
    const name = String(node?.name || '').trim();
    if (isNativeFieldLayoutNode(node) && movedNames.has(name)) return [];
    const next = { ...(node as Record<string, unknown>) } as Record<string, unknown>;
    (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
      const value = next[key];
      if (Array.isArray(value)) {
        next[key] = cloneWithoutMoved(value as NativeFormLayoutNode[]);
      }
    });
    return [next as NativeFormLayoutNode];
  });

  const withChildren = movedNodes.size
    ? cloneWithoutMoved(nodes)
    : nodes.map((node) => {
      const next = { ...(node as Record<string, unknown>) } as Record<string, unknown>;
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const value = next[key];
        if (Array.isArray(value)) {
          next[key] = applyNativeFieldOrderPreview(value as NativeFormLayoutNode[]);
        }
      });
      return next as NativeFormLayoutNode;
    });

  if (movedNodes.size) {
    const injected = new Set<string>();
    const injectIntoTarget = (rows: NativeFormLayoutNode[]): NativeFormLayoutNode[] => rows.map((node) => {
      const next = { ...(node as Record<string, unknown>) } as Record<string, unknown>;
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const value = next[key];
        if (Array.isArray(value)) {
          next[key] = injectIntoTarget(value as NativeFormLayoutNode[]);
        }
      });
      const directFieldGroupTitle = () => {
        const children = Array.isArray(next.children) ? next.children as NativeFormLayoutNode[] : [];
        for (const child of children) {
          const fieldName = String(child?.name || '').trim();
          if (isNativeFieldLayoutNode(child) && fieldName) {
            const title = normalizeFieldGroupTitle(fieldGroupBase.value[fieldName] || fieldGroupDraft[fieldName]);
            if (title) return title;
          }
        }
        return '';
      };
      const nodeTitle = isReadableFieldGroupTitle(next.string || next.label)
        ? normalizeFieldGroupTitle(next.string || next.label)
        : '';
      const title = directFieldGroupTitle() || nodeTitle;
      const directFieldNames = Array.isArray(next.children)
        ? (next.children as NativeFormLayoutNode[])
          .filter(isNativeFieldLayoutNode)
          .map((child) => String(child.name || '').trim())
          .filter(Boolean)
        : [];
      const isFieldGroupContainer = nativeLayoutNodeType(next as NativeFormLayoutNode) === 'group' && directFieldNames.length > 0;
      const toAppend = Array.from(movedNodes.entries())
        .filter(([name]) => (
          !injected.has(name)
          && isFieldGroupContainer
          && (
            fieldGroupTitleMatches(movedGroups[name], title)
            || directFieldNames.includes(String(fieldMoveTargetDraft[name] || '').trim())
          )
        ))
        .map(([name, nodeValue]) => {
          injected.add(name);
          return nodeValue;
        });
      if (toAppend.length) {
        const children = Array.isArray(next.children) ? next.children as NativeFormLayoutNode[] : [];
        next.children = sortDirectFields([...children, ...toAppend]);
      }
      return next as NativeFormLayoutNode;
    });
    const injectedTree = injectIntoTarget(withChildren);
    const fallback = Array.from(movedNodes.entries())
      .filter(([name]) => !injected.has(name))
      .map(([name, nodeValue]) => {
        injected.add(name);
        return nodeValue;
      });
    if (fallback.length) {
      let consumed = false;
      const injectFallback = (rows: NativeFormLayoutNode[]): NativeFormLayoutNode[] => rows.map((node) => {
        if (consumed) return node;
        const next = { ...(node as Record<string, unknown>) } as Record<string, unknown>;
        const children = Array.isArray(next.children) ? next.children as NativeFormLayoutNode[] : [];
        const directFieldNames = children
          .filter(isNativeFieldLayoutNode)
          .map((child) => String(child.name || '').trim())
          .filter(Boolean);
        if (directFieldNames.length) {
          next.children = sortDirectFields([...children, ...fallback]);
          consumed = true;
          return next as NativeFormLayoutNode;
        }
        (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
          const value = next[key];
          if (Array.isArray(value)) {
            next[key] = injectFallback(value as NativeFormLayoutNode[]);
          }
        });
        return next as NativeFormLayoutNode;
      });
      const withFallback = injectFallback(injectedTree);
      return consumed ? withFallback : [...injectedTree, ...sortDirectFields(fallback)];
    }
    return injectedTree;
  }

  const fieldNodes = withChildren.filter(isNativeFieldLayoutNode);
  if (fieldNodes.length <= 1) return withChildren;
  const sortedFields = [...fieldNodes].sort((left, right) => {
    const leftRank = rank.get(String(left.name || '').trim()) ?? Number.MAX_SAFE_INTEGER;
    const rightRank = rank.get(String(right.name || '').trim()) ?? Number.MAX_SAFE_INTEGER;
    return leftRank - rightRank;
  });
  let fieldIndex = 0;
  return withChildren.map((node) => (isNativeFieldLayoutNode(node) ? sortedFields[fieldIndex++] : node));
}

function runtimeNativeFormLayoutNodes(): NativeFormLayoutNode[] {
  const storeContainers = resolveContractV2ContainerTree(v2ContractStore.value);
  const v2 = storeContainers.length ? null : resolveUnifiedPageContractV2(contract.value);
  const containers = storeContainers.length
    ? storeContainers
    : (Array.isArray(v2?.layoutContract?.containerTree) ? v2.layoutContract.containerTree : []);
  if (containers.length > 0) {
    return normalizeContractV2ContainersForNativeForm(containers as unknown as ContractV2Container[]);
  }
  return Array.isArray(contract.value?.views?.form?.layout)
    ? contract.value?.views?.form?.layout as unknown as NativeFormLayoutNode[]
    : [];
}

const rawNativeFormLayoutNodes = computed<NativeFormLayoutNode[]>(() => {
  if (isContractFieldOrderEditable.value && layoutHasReadableFieldGroups(lowCodeFormLayoutBase.value)) {
    return mergeLowCodeLayoutWithRuntimeGroupShells(lowCodeFormLayoutBase.value, runtimeNativeFormLayoutNodes());
  }
  const legacyLayout = Array.isArray(contract.value?.views?.form?.layout)
    ? contract.value?.views?.form?.layout as unknown as NativeFormLayoutNode[]
    : [];
  if (isContractFieldOrderEditable.value && legacyLayout.length) {
    return legacyLayout;
  }
  const storeContainers = resolveContractV2ContainerTree(v2ContractStore.value);
  const v2 = storeContainers.length ? null : resolveUnifiedPageContractV2(contract.value);
  const containers = storeContainers.length
    ? storeContainers
    : (Array.isArray(v2?.layoutContract?.containerTree) ? v2.layoutContract.containerTree : []);
  if (containers.length > 0) {
    return normalizeContractV2ContainersForNativeForm(containers as unknown as ContractV2Container[]);
  }
  return legacyLayout;
});

function contractV2WidgetToNativeFieldNode(widget: ContractV2Widget): NativeFormLayoutNode | null {
  const fieldName = String(widget?.fieldCode || '').trim();
  if (!fieldName) return null;
  const componentConfig = widget.componentConfig && typeof widget.componentConfig === 'object'
    ? widget.componentConfig as Record<string, unknown>
    : {};
  const fieldInfo: Record<string, unknown> = {
    name: fieldName,
    label: widget.label || fieldName,
    string: widget.label || fieldName,
    type: widget.fieldType || componentConfig.fieldType || componentConfig.ttype || 'char',
    ...(widget.relation || componentConfig.relation ? { relation: widget.relation || componentConfig.relation } : {}),
    ...(typeof componentConfig.required === 'boolean' ? { required: componentConfig.required } : {}),
    ...(typeof componentConfig.readonly === 'boolean' ? { readonly: componentConfig.readonly } : {}),
    ...(Array.isArray(componentConfig.selection) ? { selection: componentConfig.selection } : {}),
  };
  return {
    type: 'field',
    name: fieldName,
    string: widget.label || fieldName,
    label: widget.label || fieldName,
    widget: widget.widgetType,
    fieldInfo,
    field_info: fieldInfo,
  };
}

function normalizeContractV2ContainersForNativeForm(containers: ContractV2Container[]): NativeFormLayoutNode[] {
  const walk = (node: ContractV2Container): NativeFormLayoutNode => {
    const next = { ...(node as unknown as Record<string, unknown>) } as NativeFormLayoutNode;
    (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
      const value = next[key];
      if (Array.isArray(value)) {
        next[key] = (value as ContractV2Container[]).map(walk);
      }
    });
    const widgetFields = Array.isArray(node.widgetList)
      ? node.widgetList
        .map((widget) => contractV2WidgetToNativeFieldNode(widget))
        .filter((item): item is NativeFormLayoutNode => Boolean(item))
      : [];
    if (widgetFields.length) {
      const children = Array.isArray(next.children) ? next.children : [];
      const existingFieldNames = new Set(
        children
          .filter((child) => String(child?.type || '').trim().toLowerCase() === 'field')
          .map((child) => String(child?.name || '').trim())
          .filter(Boolean),
      );
      next.children = [
        ...children,
        ...widgetFields.filter((child) => !existingFieldNames.has(String(child.name || '').trim())),
      ];
    }
    return next;
  };
  return containers.map(walk);
}

const baseNativeFormLayoutNodes = computed<NativeFormLayoutNode[]>(() => {
  nativeLayoutVisibilityRevision.value;
  return filterVisibleNativeLayoutNodes(rawNativeFormLayoutNodes.value);
});

const nativeFormLayoutNodes = computed<NativeFormLayoutNode[]>(() => {
  const nodes = baseNativeFormLayoutNodes.value;
  if (isContractFieldOrderEditable.value && fieldOrderPreviewActive.value && fieldOrderDraft.value.length) {
    return applyNativeFieldOrderPreview(nodes);
  }
  return nodes;
});

const nativeFormRootColumns = computed<1 | 2 | 3>(() => {
  if (isContractFieldOrderEditable.value) return formLayoutColumnsDraft.value;
  const walk = (nodes: NativeFormLayoutNode[]): 1 | 2 | 3 | null => {
    for (const node of nodes) {
      const attrs = node && typeof node.attributes === 'object' && node.attributes
        ? node.attributes as Record<string, unknown>
        : {};
      const direct = normalizeNativeLayoutColumns(
        attrs.col
        ?? attrs.columns
        ?? (node as { cols?: unknown; columns?: unknown }).cols
        ?? (node as { cols?: unknown; columns?: unknown }).columns,
      );
      if (direct) return direct;
      for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
        const children = node?.[key];
        if (Array.isArray(children)) {
          const nested = walk(children as NativeFormLayoutNode[]);
          if (nested) return nested;
        }
      }
    }
    return null;
  };
  return walk(nativeFormLayoutNodes.value) || 3;
});

watch(baseNativeFormLayoutNodes, (nodes) => {
  const keys: string[] = [];
  const seen = new Set<string>();
  const labels: Record<string, string> = {};
  const walk = (items: NativeFormLayoutNode[]) => {
    items.forEach((node) => {
      const type = nativeLayoutNodeType(node);
      const name = String(node?.name || '').trim();
      if (type === 'field' && name && !seen.has(name)) {
        seen.add(name);
        keys.push(name);
        labels[name] = String(node?.string || node?.label || name).trim() || name;
      }
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeFormLayoutNode[]);
      });
    });
  };
  walk(nodes);
  nativeFormDesignFieldKeys.value = keys;
  nativeFormDesignFieldLabels.value = labels;
}, { immediate: true });

const nativeNotebookPageCount = computed(() => countNativeNodesByType(nativeFormLayoutNodes.value as NativeLayoutLikeNode[], 'page'));
const nativeGroupCount = computed(() => countNativeNodesByType(nativeFormLayoutNodes.value as NativeLayoutLikeNode[], 'group'));
const nativeVisibleSectionTitles = computed(() => collectNativeVisibleSectionTitles(nativeFormLayoutNodes.value as NativeLayoutLikeNode[]));
const showNativeDefaultSectionTitle = computed(() => (
  useNativeFormTree.value
  && nativeVisibleFieldNames.value.size > 0
  && nativeVisibleSectionTitles.value.length === 0
));

function resolveNativeButtonLabel(node: NativeFormLayoutNode) {
  return resolveNativeButtonLabelFromNode(node as NativeLayoutLikeNode, (field) => formData[field]);
}

const nativeVisibleFieldNames = computed(() => {
  const names = new Set<string>();
  const walk = (nodes: NativeFormLayoutNode[]) => {
    nodes.forEach((node) => {
      const name = String(node?.name || '').trim();
      if (name && isNativeFieldVisible(name, node)) names.add(name);
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeFormLayoutNode[]);
      });
    });
  };
  walk(nativeFormLayoutNodes.value);
  return names;
});

function formDataFieldNames() {
  const fieldMap = contract.value?.fields || {};
  const contractRecord = contract.value && typeof contract.value === 'object'
    ? contract.value as Record<string, unknown>
    : {};
  const toolbar = contractRecord.toolbar && typeof contractRecord.toolbar === 'object' && !Array.isArray(contractRecord.toolbar)
    ? contractRecord.toolbar as Record<string, unknown>
    : {};
  const views = contractRecord.views && typeof contractRecord.views === 'object' && !Array.isArray(contractRecord.views)
    ? contractRecord.views as Record<string, unknown>
    : {};
  const formView = views.form && typeof views.form === 'object' && !Array.isArray(views.form)
    ? views.form as Record<string, unknown>
    : {};
  const names = new Set<string>();
  collectNativeLayoutFieldNames(rawNativeFormLayoutNodes.value as NativeLayoutLikeNode[], names, (name) => Boolean(contract.value?.fields?.[name]));
  collectNativeLayoutBadgeCountFieldNames(rawNativeFormLayoutNodes.value as NativeLayoutLikeNode[], names);
  collectContractActionBadgeCountFieldNames(contractRecord.buttons, names);
  collectContractActionBadgeCountFieldNames(toolbar.header, names);
  collectContractActionBadgeCountFieldNames(toolbar.sidebar, names);
  collectContractActionBadgeCountFieldNames(toolbar.footer, names);
  collectContractActionBadgeCountFieldNames(formView.header_buttons, names);
  collectContractActionBadgeCountFieldNames(formView.button_box, names);
  collectContractActionBadgeCountFieldNames(formView.business_actions, names);
  layoutNodes.value.forEach((node) => {
    if (node.kind === 'field' && fieldMap[node.name]) names.add(node.name);
  });
  contractVisibleFields.value.forEach((name) => {
    if (fieldMap[name]) names.add(name);
  });
  const statusField = nativeStatusbar.value.field;
  if (statusField && fieldMap[statusField]) names.add(statusField);
  const storeMainData = resolveContractV2MainData(v2ContractStore.value);
  const contractMainData = Object.keys(storeMainData).length ? storeMainData : resolveUnifiedPageContractV2MainData(contract.value);
  ['can_review', 'validation_status'].forEach((name) => {
    if (fieldMap[name] || Object.prototype.hasOwnProperty.call(contractMainData, name)) names.add(name);
  });
  if (fieldMap.active) names.add('active');
  if (!names.size) {
    Object.keys(fieldMap).slice(0, 40).forEach((name) => names.add(name));
  }
  return Array.from(names);
}

const nativeFavoriteFieldNames = computed(() => {
  const names = new Set<string>();
  collectNativeFavoriteFieldNames(rawNativeFormLayoutNodes.value, names);
  return names;
});

function workflowPhaseStatusbar(): NativeStatusbarVm {
  return normalizeWorkflowPhaseStatusbar(currentWorkflowContract());
}

const nativeStatusbar = computed<NativeStatusbarVm>(() => {
  if (!recordId.value) {
    return { visible: false, field: '', current: '', states: [], reachedValues: [], readonly: true };
  }
  const formView = contract.value?.views?.form as Record<string, unknown> | undefined;
  const raw = formView?.statusbar && typeof formView.statusbar === 'object'
    ? formView.statusbar as Record<string, unknown>
    : {};
  const field = String(raw.field || '').trim();
  const descriptor = field ? contract.value?.fields?.[field] : undefined;
  const rawStates = Array.isArray(raw.states) ? raw.states as Array<Record<string, unknown>> : [];
  const selectionStates = Array.isArray(descriptor?.selection)
    ? descriptor.selection.map((item) => {
      const pair = item as unknown[];
      return { value: String(pair[0] ?? ''), label: String(pair[1] ?? pair[0] ?? '') };
    })
    : [];
  const states: StatusbarState[] = (rawStates.length
    ? rawStates.map((item) => ({ value: item.value as string | number, label: String(item.label || item.value || '') }))
    : selectionStates)
    .filter((item) => String(item.value ?? '').trim() && String(item.label || '').trim());
  const storeMainData = resolveContractV2MainData(v2ContractStore.value);
  const contractMainData = Object.keys(storeMainData).length ? storeMainData : resolveUnifiedPageContractV2MainData(contract.value);
  const rawFormStatus = formData[field];
  const formStatusValue = rawFormStatus === false || rawFormStatus == null ? '' : String(rawFormStatus).trim();
  const current = String(
    formStatusValue
      || (Object.prototype.hasOwnProperty.call(contractMainData, field) ? contractMainData[field] : '')
      || '',
  ).trim();
  const currentIndex = states.findIndex((item) => String(item.value) === current);
  const state = field ? runtimeState(field) : { readonly: true };
  if (!field || !states.length) {
    return workflowPhaseStatusbar();
  }
  return {
    visible: Boolean(field && states.length),
    field,
    current,
    states,
    reachedValues: currentIndex >= 0 ? states.slice(0, currentIndex).map((item) => String(item.value)) : [],
    readonly: Boolean(state.readonly || renderProfile.value === 'readonly' || (recordId.value ? !rights.value.write : !rights.value.create)),
  };
});

function setStatusbarValue(value: string) {
  const field = nativeStatusbar.value.field;
  if (!field || nativeStatusbar.value.readonly) return;
  const raw = String(value || '').trim();
  let resolved = raw;
  const descriptor = contract.value?.fields?.[field];
  const selection = Array.isArray(descriptor?.selection) ? descriptor.selection : [];
  if (selection.length) {
    const byCode = selection.find((item) => String((item as unknown[])[0] ?? '') === raw);
    const byLabel = selection.find((item) => String((item as unknown[])[1] ?? '') === raw);
    const matched = byCode || byLabel;
    if (matched) {
      resolved = String((matched as unknown[])[0] ?? raw);
    }
  }
  formData[field] = resolved || false;
  markFieldChanged(field);
}

function evaluateNativeModifierValue(value: unknown) {
  return evaluateNativeModifierValueWithResolver(value, (field) => formData[field]);
}

function evaluateNativeActionVisibility(row: Record<string, unknown>) {
  const nativeAction = row.action && typeof row.action === 'object' && !Array.isArray(row.action)
    ? row.action as Record<string, unknown>
    : {};
  const visibleRaw = nativeAction.visible || row.visible;
  const visible = visibleRaw && typeof visibleRaw === 'object' && !Array.isArray(visibleRaw)
    ? visibleRaw as Record<string, unknown>
    : {};
  const states = Array.isArray(visible.states)
    ? visible.states.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  if (states.length) {
    const currentState = String(formData.state || '').trim();
    if (currentState && !states.includes(currentState)) return false;
  }
  const attrs = visible.attrs && typeof visible.attrs === 'object' && !Array.isArray(visible.attrs)
    ? visible.attrs as Record<string, unknown>
    : {};
  const modifiers = row.modifiers && typeof row.modifiers === 'object' && !Array.isArray(row.modifiers)
    ? row.modifiers as Record<string, unknown>
    : {};
  const invisible = attrs.invisible ?? modifiers.invisible ?? row.invisible;
  if (evaluateNativeModifierValue(invisible)) return false;
  const nativeType = String(row.type || row.buttonType || '').trim().toLowerCase();
  const hasNativeActionShape = nativeType === 'button'
    || nativeType === 'object'
    || nativeType === 'server'
    || Boolean(row.action || row.payload || row.name || row.method);
  if (hasNativeActionShape) {
    const action = contractActionFromNativeRow(row);
    if (!action) return false;
  }
  return true;
}

function isNativeLayoutNodeVisible(nodeRaw: NativeFormLayoutNode) {
  if (evaluateNativeModifierValue(nativeModifierValue(nodeRaw, 'invisible'))) return false;
  const node = nodeRaw as Record<string, unknown>;
  const nodeType = String(node.type || '').trim().toLowerCase();
  if (node.visible === false && !(isContractFieldOrderEditable.value && nodeType === 'group')) return false;
  if (nodeType === 'group') {
    const title = normalizeFieldGroupTitle(node.string || node.label || node.title);
    if (title && !effectiveGroupVisible(title) && !isContractFieldOrderEditable.value) return false;
  }
  const fieldName = String(nodeRaw.name || '').trim();
  if (
    nodeType === 'field'
    && fieldName
    && Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldName)
    && fieldVisibilityDraft[fieldName] === false
    && !isContractFieldOrderEditable.value
  ) {
    return false;
  }
  if (nodeType === 'button') {
    return Boolean(contractActionFromNativeRow(node));
  }
  return true;
}

function isNativeFavoriteField(name: string) {
  return nativeFavoriteFieldNames.value.has(String(name || '').trim());
}

function nativeFieldLabel(nodeRaw: NativeFormLayoutNode, descriptor?: FieldDescriptor) {
  const node = nodeRaw as Record<string, unknown>;
  const fieldInfo = nativeNodeFieldInfo(node);
  return String(
    contractFieldLabel(String(nodeRaw.name || ''))
    || descriptor?.string
    || node.string
    || node.label
    || fieldInfo.string
    || fieldInfo.label
    || nodeRaw.name
    || '',
  );
}

function isNativeFieldVisible(name: string, nodeRaw?: NativeFormLayoutNode) {
  const normalized = String(name || '').trim();
  if (!normalized) return false;
  if (nodeRaw && !isNativeLayoutNodeVisible(nodeRaw)) return false;
  const statusField = nativeStatusbar.value.field;
  if (statusField && normalized === statusField) return false;
  if (normalized === 'message_needaction') return false;
  const semantic = fieldSemanticMeta(normalized);
  if ((semantic.technical || semantic.semantic_type === 'technical') && !showHud.value) return false;
  if (semantic.surface_role === 'hidden' && !showHud.value) return false;
  const state = runtimeState(normalized);
  if (state.invisible) return false;
  const descriptor = nodeRaw
    ? nativeNodeFieldDescriptor(nodeRaw, contract.value?.fields?.[normalized])
    : contract.value?.fields?.[normalized];
  if (!descriptor) return false;
  if (isCreateWorkflowStateField(normalized, nativeFieldLabel(nodeRaw || {} as NativeFormLayoutNode, descriptor))) return false;
  const resolved = evaluateFieldPolicy(
    contract.value,
    normalized,
    {
      required: Boolean(descriptor?.required),
      readonly: Boolean(descriptor?.readonly),
    },
    policyContext.value,
  );
  if (resolved.visible) return true;
  // Native layout is already a backend-scoped form contract. Do not re-apply
  // the legacy core/advanced create-mode filter here, otherwise fields in
  // later notebook pages disappear even though the action-bound view exposes
  // them explicitly. Explicit invisible/status rules are handled above.
  if (nodeRaw) return true;
  return renderProfile.value === 'create' && semantic.surface_role === 'advanced';
}

function currentNativeFieldOrder() {
  const out: string[] = [];
  const seen = new Set<string>();
  const walk = (nodes: NativeFormLayoutNode[]) => {
    nodes.forEach((node) => {
      const type = String(node?.type || (node as { containerType?: string })?.containerType || '').trim().toLowerCase();
      const name = String(node?.name || '').trim();
      if (type === 'field' && name && !seen.has(name) && isNativeFieldVisible(name, node)) {
        seen.add(name);
        out.push(name);
      }
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeFormLayoutNode[]);
      });
    });
  };
  walk(nativeFormLayoutNodes.value);
  return out;
}

function ensureFieldOrderDraftStartsFromCurrentLayout() {
  if (!useNativeFormTree.value || fieldOrderPreviewActive.value) return;
  const current = currentNativeFieldOrder();
  if (!current.length) return;
  const known = new Set(current);
  const extra = fieldOrderDraft.value.filter((name) => name && !known.has(name));
  fieldOrderDraft.value = [...current, ...extra];
}

function nativeLayoutNodeToFieldNode(nodeRaw: NativeFormLayoutNode, index: number): LayoutNode | null {
  const name = String(nodeRaw?.name || '').trim();
  if (!name || !isNativeFieldVisible(name, nodeRaw)) return null;
  const descriptor = nativeNodeFieldDescriptor(nodeRaw, contract.value?.fields?.[name]);
  if (!descriptor) return null;
  const resolved = evaluateFieldPolicy(
    contract.value,
    name,
    {
      required: Boolean(descriptor?.required),
      readonly: Boolean(descriptor?.readonly),
    },
    policyContext.value,
  );
  const state = runtimeState(name);
  const nativeReadonly = isStaticTruthyModifier(nativeModifierValue(nodeRaw, 'readonly'));
  const nativeRequired = isStaticTruthyModifier(nativeModifierValue(nodeRaw, 'required'));
  const label = nativeFieldLabel(nodeRaw, descriptor);
  const nodeClass = String((nodeRaw as Record<string, unknown>).class || (nodeRaw as Record<string, unknown>).className || '').trim();
  const fieldSize = isContractFieldOrderEditable.value
    ? effectiveFieldSize(name)
    : normalizeLowCodeFieldSize(
      (nodeRaw as Record<string, unknown>).field_size
      || (nodeRaw as Record<string, unknown>).fieldSize
      || (nodeClass.includes('field--large') ? 'large'
        : (nodeClass.includes('field--full') ? 'full'
          : (nodeClass.includes('field--wide') ? 'wide' : 'normal'))),
    );
  rememberFormConfigFieldLabel(name, label);
  return {
    key: `native_field_${name}_${index}`,
    kind: 'field',
    name,
    label,
    readonly: Boolean(nativeReadonly || resolved.readonly || state.readonly || (recordId.value ? !rights.value.write : !rights.value.create)),
    required: Boolean(nativeRequired || resolved.required || state.required || descriptor?.required),
    widget: nativeNodeWidget(nodeRaw),
    widgetSemantics: nativeNodeWidgetSemantics(nodeRaw),
    spanClass: lowCodeFieldSizeClass(fieldSize) || nodeClass,
    descriptor,
  };
}

function nativeFieldSchemasForNodes(nodes: NativeFormLayoutNode[]): FormSectionFieldSchema[] {
  const mappedNodes = nodes
    .map((node, index) => ({ raw: node, field: nativeLayoutNodeToFieldNode(node, index) }))
    .filter((item): item is { raw: NativeFormLayoutNode; field: LayoutNode } => Boolean(item.field));
  const favoriteNode = mappedNodes.find((item) => item.field.widget === 'boolean_favorite' || item.field.name === 'is_favorite');
  const fieldNodes = mappedNodes
    .filter((item) => item !== favoriteNode)
    .map((item) => item.field);
  if (isContractFieldOrderEditable.value && fieldOrderPreviewActive.value && fieldOrderDraft.value.length) {
    const rank = new Map(fieldOrderDraft.value.map((fieldName, order) => [fieldName, order]));
    fieldNodes.sort((left, right) => {
      const leftRank = rank.get(left.name) ?? Number.MAX_SAFE_INTEGER;
      const rightRank = rank.get(right.name) ?? Number.MAX_SAFE_INTEGER;
      return leftRank - rightRank;
    });
  }
  const schemas = applyV2ReadonlyFieldValues(buildSectionFieldSchemas(fieldNodes));
  if (!favoriteNode || !schemas.length) return schemas;
  const target = schemas.find((field) => field.name === 'name')
    || schemas.find((field) => ['char', 'text'].includes(String(field.type || '').trim().toLowerCase()))
    || schemas[0];
  if (target) {
    target.favoriteToggle = {
      name: favoriteNode.field.name,
      label: favoriteNode.field.label || favoriteNode.field.name,
      active: Boolean(formData[favoriteNode.field.name]),
      readonly: Boolean(favoriteNode.field.readonly || busy.value),
      descriptor: favoriteNode.field.descriptor,
    };
  }
  return schemas;
}

function v2FieldValue(name: string) {
  const normalized = String(name || '').trim();
  if (!normalized || !v2ContractStore.value?.widgetsByFieldCode.has(normalized)) {
    return { found: false, value: undefined };
  }
  const source = v2ShadowValueSource.value.values;
  if (!Object.prototype.hasOwnProperty.call(source, normalized)) {
    return { found: false, value: undefined };
  }
  return { found: true, value: source[normalized] };
}

function schemaInputValueFromRaw(fieldName: string, fieldType: string, raw: unknown) {
  const type = String(fieldType || '').trim().toLowerCase();
  if (type === 'many2one') {
    const id = normalizeRelationIds(raw)[0];
    return id ? String(id) : '';
  }
  if (raw === null || raw === undefined || raw === false) return '';
  if (type === 'date') return toDateInputValue(raw);
  if (type === 'datetime') return toDatetimeInputValue(raw);
  if (typeof raw === 'number' || typeof raw === 'boolean') return raw;
  return String(raw);
}

function applyV2ReadonlyFieldValues(schemas: FormSectionFieldSchema[]): FormSectionFieldSchema[] {
  return schemas.map((field) => {
    if (!field.readonly) return field;
    const resolved = v2FieldValue(field.name);
    if (!resolved.found) return field;
    return {
      ...field,
      value: resolved.value,
      inputValue: schemaInputValueFromRaw(field.name, String(field.type || ''), resolved.value),
    };
  });
}

function shouldShowRequiredMark(node: LayoutNode) {
  if (node.kind !== 'field' || node.readonly) return false;
  if (!node.required) return false;
  if (showHud.value) return true;
  if (renderProfile.value !== 'create') return true;
  const policyRequired = policyRequiredFields.value;
  const validationRequired = validationRequiredFields.value;
  if (policyRequired.size || validationRequired.size) {
    return policyRequired.has(node.name) || validationRequired.has(node.name);
  }
  return coreFieldNames.value.includes(node.name);
}

function collectSceneValidationPrecheckErrors(fieldLabels: Record<string, string>): string[] {
  const out: string[] = [];
  for (const field of sceneValidationRequiredFields.value) {
    if (!isFieldVisible(field)) continue;
    const value = formData[field];
    if (isMissingRequiredValue(value)) {
      out.push(`${ErrorCodes.SCENE_VALIDATION_REQUIRED}: ${fieldLabels[field] || field} 为必填项`);
    }
  }
  return Array.from(new Set(out)).slice(0, 5);
}

const layoutNodes = computed<LayoutNode[]>(() => {
  const fieldMap = contract.value?.fields || {};
  const order = contract.value?.views?.form?.layout || [];
  const v2FieldContainerStatus = collectUnifiedPageContractV2FieldContainerStatus(contract.value);
  const used = new Set<string>();
  const nodes: LayoutNode[] = [];
  const containerKeys = ['children', 'tabs', 'pages', 'nodes', 'items'];

  function pushField(nameRaw: unknown) {
    const name = String(nameRaw || '').trim();
    if (!name || used.has(name)) return;
    const descriptor = fieldMap[name];
    if (!descriptor) return;
    if (isCreateWorkflowStateField(name, String(contractFieldLabel(name) || descriptor?.string || ''))) return;
    const containerStatus = v2FieldContainerStatus[name];
    if (containerStatus?.visible === false) return;
    const resolved = evaluateFieldPolicy(
      contract.value,
      name,
      {
        required: Boolean(descriptor?.required),
        readonly: Boolean(descriptor?.readonly),
      },
      policyContext.value,
    );
    if (!resolved.visible) return;
    used.add(name);
    const state = runtimeState(name);
    nodes.push({
      key: `field_${name}`,
      kind: 'field',
      name,
      label: String(contractFieldLabel(name) || descriptor?.string || name),
      readonly: Boolean(resolved.readonly || state.readonly || containerStatus?.disabled === true || (recordId.value ? !rights.value.write : !rights.value.create)),
      required: Boolean(resolved.required || state.required),
      descriptor,
    });
  }

  function walkLayout(nodeRaw: unknown, parentKey: string) {
    if (!nodeRaw || typeof nodeRaw !== 'object') return;
    const node = nodeRaw as Record<string, unknown>;
    const kind = String(node.type || '').trim().toLowerCase();
    if (!kind) return;
    const label = String(node.string || node.label || '').trim();
    const nodeKey = `${parentKey}_${kind}_${String(node.name || label || nodes.length)}`;

    if (kind === 'header' || kind === 'sheet' || kind === 'group' || kind === 'notebook' || kind === 'page') {
      nodes.push({
        key: `layout_${nodeKey}`,
        kind: kind as LayoutNode['kind'],
        name: String(node.name || '').trim(),
        label,
        readonly: true,
        required: false,
      });
    }
    if (kind === 'field') {
      pushField(node.name);
      return;
    }
    containerKeys.forEach((key) => {
      const children = node[key];
      if (!Array.isArray(children)) return;
      children.forEach((child, index) => walkLayout(child, `${nodeKey}_${key}_${index}`));
    });
  }

  if (Array.isArray(order)) {
    order.forEach((item, index) => walkLayout(item, `root_${index}`));
  }
  if (!nodes.some((node) => node.kind === 'field')) {
    const fallback = contractVisibleFields.value.length
      ? contractVisibleFields.value
      : [...coreFieldNames.value, ...advancedFieldNames.value];
    const fallbackFields = fallback.length ? fallback : Object.keys(fieldMap).slice(0, 16);
    fallbackFields.forEach((name) => pushField(name));
  }

  return nodes;
});

const buildSectionFieldSchemas = createFormSectionFieldSchemaBuilder({
  resolveFieldType: (descriptor) => fieldType(descriptor) || 'char',
  resolveRequired: (field) => shouldShowRequiredMark(field as LayoutNode),
  resolveSpanClass: (field) => (field as LayoutNode).spanClass || resolveFieldSpanClass({
    fieldName: field.name,
    fieldType: fieldType(field.descriptor),
  }),
  resolveRawValue: (fieldName) => formData[fieldName],
  resolveMany2oneValue: many2oneValue,
  normalizeDateInputValue: toDateInputValue,
  normalizeDatetimeInputValue: toDatetimeInputValue,
  resolveTextInputValue: inputFieldValue,
  resolveInputPlaceholder: (label) => resolveInputPlaceholder(label),
  resolveSelectionOptions: (descriptor) => mapDescriptorSelectionOptions(descriptor),
  resolveRelationOptions: (fieldName) => mapRelationOptions(relationOptionsForField(fieldName)),
  resolveRelationCreateMode: (_fieldName, descriptor) => relationCreateMode(descriptor),
  resolveRelationInlineCreate: (fieldName, descriptor) => {
    const inline = relationInlineCreate(descriptor);
    return {
      enabled: inline.enabled,
      createOnNoMatch: inline.createOnNoMatch,
      nameField: inline.nameField,
      match: inline.match,
    };
  },
  resolveRelationTextValue: relationKeyword,
  resolveCanOpenRelationRecord: (fieldName, descriptor) => canOpenRelationRecordForm(fieldName, descriptor),
  resolveRelationRecordOpenLabel: (_fieldName, descriptor) => relationUiLabel(descriptor, 'open_existing', '维护当前项'),
  resolveRelationSearchLabel: (_fieldName, descriptor) => relationUiLabel(descriptor, 'search_more'),
  resolveRelationCreateLabel: (_fieldName, descriptor) => {
    const mode = relationCreateMode(descriptor);
    if (mode === 'page') return relationUiLabel(descriptor, 'create_and_edit');
    if (mode === 'quick') return relationUiLabel(descriptor, 'quick_create');
    return '';
  },
  resolveRelationInlineCreateLabel: (_fieldName, descriptor, keyword) => {
    const template = relationUiLabel(descriptor, 'inline_create');
    const label = String(keyword || '').trim();
    return template.includes('%s') ? template.replace('%s', label) : template || label;
  },
  many2oneCreateToken: MANY2ONE_CREATE_OPTION,
  many2oneSearchToken: MANY2ONE_SEARCH_MORE_OPTION,
  many2oneOpenToken: MANY2ONE_OPEN_RECORD_OPTION,
});

function onTemplateFieldChange(payload: FormSectionFieldChange) {
  if (String(payload.type || '').trim().toLowerCase() === 'many2one' && payload.action === 'query') {
    queryMany2oneInline(payload.name, payload.descriptor, String(payload.value ?? ''));
    return;
  }
  if (String(payload.type || '').trim().toLowerCase() === 'many2one' && payload.action === 'commit') {
    void commitMany2oneInline(payload.name, payload.descriptor, String(payload.value ?? ''));
    return;
  }
  dispatchTemplateFieldChange(payload, {
    onBoolean: (name, value) => setBooleanField(name, value),
    onSelection: (name, value) => setSelectionField(name, value),
    onMany2one: (name, descriptor, value) => setMany2oneField(name, descriptor, value),
    onText: (name, value) => setTextField(name, value),
  });
}

const relationFieldAdapter = computed<RelationFieldAdapter>(() => ({
  busy: busy.value,
  showOne2manyErrors: showOne2manyErrors.value,
  relationKeyword,
  setRelationKeyword,
  relationIds,
  selectedRelationOptions,
  filteredRelationOptions,
  setRelationMultiField,
  setRelationIds,
  relationCreateMode: (fieldName: string) => relationCreateMode(contract.value?.fields?.[fieldName]),
  relationCreateLabel: (fieldName: string) => {
    const descriptor = contract.value?.fields?.[fieldName];
    const mode = relationCreateMode(descriptor);
    if (mode === 'page') return relationUiLabel(descriptor, 'create_and_edit');
    if (mode === 'quick') return relationUiLabel(descriptor, 'quick_create');
    return '';
  },
  relationInlineCreateLabel: (fieldName: string) => {
    const descriptor = contract.value?.fields?.[fieldName];
    const template = relationUiLabel(descriptor, 'inline_create');
    const label = relationKeyword(fieldName).trim();
    return template.includes('%s') ? template.replace('%s', label) : template || label;
  },
  canInlineCreateRelation: (fieldName: string) => {
    const descriptor = contract.value?.fields?.[fieldName];
    const inline = relationInlineCreate(descriptor);
    const keyword = relationKeyword(fieldName).trim();
    if (!keyword || !inline.enabled || !inline.createOnNoMatch) return false;
    return !relationOptionsForField(fieldName).some((option) => option.label.trim().toLowerCase() === keyword.toLowerCase());
  },
  openRelationCreate: (fieldName: string) => {
    const descriptor = contract.value?.fields?.[fieldName];
    if (!descriptor) return;
    void openRelationCreateForm(fieldName, descriptor);
  },
  one2manyCanCreate,
  one2manyCreateLabel,
  addOne2manyRow,
  one2manySummary,
  visibleOne2manyRows,
  one2manyRowStateLabel,
  one2manyColumns,
  setOne2manyRowField,
  removeOne2manyRow,
  one2manyRowErrors,
  one2manyRowHints,
  removedOne2manyRows,
  restoreOne2manyRow,
  one2manyRowLabel,
  selectPlaceholder: resolveSelectPlaceholder,
  one2manyColumnInputType,
  one2manyColumnDisplayValue,
  inputFieldValue,
  fieldInputType,
  inputPlaceholder: resolveInputPlaceholder,
  setTextField,
}));

const contractReadiness = computed<FormContractReadiness>(() => {
  if (!contract.value) {
    return { usable: false, issues: ['contract not loaded'], fieldCount: 0, layoutFieldCount: 0, visibleCandidateCount: 0 };
  }
  return analyzeFormContractReadiness(contract.value, { requirePureFormViewType: false });
});

function comparableFieldValue(name: string, value: unknown) {
  const descriptor = contract.value?.fields?.[name];
  const ttype = fieldType(descriptor);
  if (ttype === 'many2many') {
    return JSON.stringify(normalizeRelationIds(value).sort((a, b) => a - b));
  }
  if (ttype === 'one2many') {
    const rows = one2manyFieldRows(name).map((row) => ({
      id: row.id || 0,
      isNew: row.isNew,
      removed: row.removed,
      dirty: row.dirty,
      dirtyFields: row.dirtyFields || [],
      values: row.values || {},
    }));
    return JSON.stringify(rows);
  }
  return normalizeComparable(value);
}

function isFieldWritable(name: string) {
  const node = layoutNodes.value.find((item) => item.kind === 'field' && item.name === name);
  if (node) return !node.readonly;
  const statusField = nativeStatusbar.value.field;
  return Boolean(statusField && statusField === name && !nativeStatusbar.value.readonly);
}

function normalizeFieldValue(name: string, value: unknown) {
  const descriptor = contract.value?.fields?.[name];
  const ttype = fieldType(descriptor);
  if (ttype === 'boolean') {
    return Boolean(value);
  }
  if (ttype === 'integer') {
    const parsed = parseNumeric(value);
    return parsed === null ? false : Math.trunc(parsed);
  }
  if (ttype === 'float' || ttype === 'monetary') {
    const parsed = parseNumeric(value);
    return parsed === null ? false : parsed;
  }
  if (ttype === 'many2one') {
    if (Array.isArray(value) && typeof value[0] === 'number') return value[0];
    if (typeof value === 'number') return value;
    const parsed = parseNumeric(value);
    return parsed === null ? false : Math.trunc(parsed);
  }
  if (ttype === 'many2many') {
    return buildX2ManyCommands({
      kind: 'many2many',
      current: value,
      original: originalValues.value[name],
      mode: 'write',
    });
  }
  if (ttype === 'one2many') {
    return buildOne2manyCommandValue(name, 'write');
  }
  if (ttype === 'date') {
    const normalized = toDateInputValue(value);
    return normalized || false;
  }
  if (ttype === 'datetime') {
    return fromDatetimeInputValue(value);
  }
  if (ttype === 'char' || ttype === 'text' || ttype === 'html') {
    return String(value ?? '');
  }
  return value;
}

function inputFieldValue(name: string) {
  const raw = formData[name];
  if (raw === false || raw === null || raw === undefined) return '';
  return String(raw);
}

function setBooleanField(name: string, checked: boolean) {
  const previousValue = formData[name];
  formData[name] = checked;
  if (isNativeFavoriteField(name) && recordId.value && rights.value.write) {
    void persistNativeFavoriteField(name, checked, previousValue);
    return;
  }
  markFieldChanged(name);
}

async function persistNativeFavoriteField(name: string, checked: boolean, previousValue: unknown) {
  try {
    await writeContractFormRecord({
      model: model.value,
      ids: [recordId.value],
      vals: { [name]: checked },
      context: {},
    });
    originalValues.value = {
      ...originalValues.value,
      [name]: checked,
    };
    changedFieldSet.delete(name);
    dirtyFieldSet.delete(name);
  } catch {
    formData[name] = previousValue;
    submissionFeedback.value = {
      kind: 'error',
      message: '收藏状态保存失败，请稍后重试。',
    };
  }
}

function setMany2oneField(name: string, descriptor: FieldDescriptor | undefined, value: string) {
  const normalized = String(value || '').trim();
  if (!normalized) {
    formData[name] = false;
    relationKeywords[name] = '';
    clearDynamicRelationDependents(name);
    markFieldChanged(name);
    return;
  }
  if (normalized === MANY2ONE_CREATE_OPTION) {
    void openRelationCreateForm(name, descriptor);
    return;
  }
  if (normalized === MANY2ONE_SEARCH_MORE_OPTION) {
    void openRelationSearchDialog(name, descriptor);
    return;
  }
  if (normalized === MANY2ONE_OPEN_RECORD_OPTION) {
    void openRelationRecordForm(name, descriptor);
    return;
  }
  const id = Number(normalized);
  if (!Number.isFinite(id) || id <= 0) {
    formData[name] = false;
    relationKeywords[name] = '';
    clearDynamicRelationDependents(name);
    markFieldChanged(name);
    return;
  }
  const normalizedId = Math.trunc(id);
  formData[name] = normalizedId;
  const selected = relationOptionsForField(name).find((option) => option.id === normalizedId);
  if (selected) {
    relationKeywords[name] = selected.label;
    void switchFormByRelationOption(name, selected);
  }
  clearDynamicRelationDependents(name);
  markFieldChanged(name);
}

function queryMany2oneInline(name: string, descriptor: FieldDescriptor | undefined, value: string) {
  const keyword = String(value || '').trim();
  if (keyword && clearedDynamicRelationFields[name]) {
    delete clearedDynamicRelationFields[name];
    delete invalidatedRelationKeywords[name];
  }
  if (keyword && invalidatedRelationKeywords[name] === keyword && !formData[name]) {
    relationKeywords[name] = '';
    return;
  }
  if (keyword && invalidatedRelationKeywords[name] && invalidatedRelationKeywords[name] !== keyword) {
    delete invalidatedRelationKeywords[name];
  }
  relationKeywords[name] = keyword;
  if (!keyword) {
    void queryRelationOptions(name, '');
    return;
  }
  setRelationKeyword(name, keyword);
}

async function commitMany2oneInline(name: string, descriptor: FieldDescriptor | undefined, value: string) {
  const keyword = String(value || '').trim();
  if (keyword && clearedDynamicRelationFields[name] && !formData[name]) {
    relationKeywords[name] = '';
    return;
  }
  if (keyword && invalidatedRelationKeywords[name] === keyword && !formData[name]) {
    relationKeywords[name] = '';
    return;
  }
  if (keyword && invalidatedRelationKeywords[name] && invalidatedRelationKeywords[name] !== keyword) {
    delete invalidatedRelationKeywords[name];
  }
  if (!keyword) {
    formData[name] = false;
    relationKeywords[name] = '';
    markFieldChanged(name);
    return;
  }
  const currentId = Number(formData[name] || 0);
  if (Number.isFinite(currentId) && currentId > 0) {
    const currentOption = relationOptionsForField(name).find((option) => option.id === Math.trunc(currentId));
    if (currentOption && currentOption.label.trim().toLowerCase() === keyword.toLowerCase()) {
      relationKeywords[name] = currentOption.label;
      return;
    }
  }
  const inline = relationInlineCreate(descriptor);
  const localQuickFill = resolveRelationQuickFillOption(relationOptionsForField(name), keyword, inline.match);
  if (localQuickFill) {
    setMany2oneOption(name, localQuickFill);
    return;
  }
  const localSingleMatch = singleContainingRelationOption(relationOptionsForField(name), keyword);
  if (localSingleMatch) {
    setMany2oneOption(name, localSingleMatch);
    return;
  }
  const rows = await queryRelationOptions(name, keyword);
  const remoteQuickFill = resolveRelationQuickFillOption(rows, keyword, inline.match);
  if (remoteQuickFill) {
    setMany2oneOption(name, remoteQuickFill);
    return;
  }
  if (rows.length === 1) {
    setMany2oneOption(name, rows[0]);
    return;
  }
  if (hasAmbiguousRelationMatches(rows, keyword, inline.match)) {
    relationKeywords[name] = keyword;
    formData[name] = false;
    markFieldChanged(name);
    await openRelationSearchDialog(name, descriptor);
    return;
  }
  if (!inline.enabled || !inline.createOnNoMatch) return;
  formData[name] = false;
  relationKeywords[name] = keyword;
  markFieldChanged(name);
}

async function resolvePendingInlineRelationCreates() {
  const issues: string[] = [];
  for (const node of layoutNodes.value) {
    if (node.kind !== 'field' || node.readonly) continue;
    const descriptor = contract.value?.fields?.[node.name];
    if (fieldType(descriptor) !== 'many2one') continue;
    const inline = relationInlineCreate(descriptor);
    if (!inline.enabled || !inline.createOnNoMatch) continue;
    const currentId = Number(formData[node.name] || 0);
    if (Number.isFinite(currentId) && currentId > 0) continue;
    const keyword = relationKeyword(node.name).trim();
    if (!keyword) continue;
    const localQuickFill = resolveRelationQuickFillOption(relationOptionsForField(node.name), keyword, inline.match);
    if (localQuickFill) {
      setMany2oneOption(node.name, localQuickFill);
      continue;
    }
    const rows = await queryRelationOptions(node.name, keyword);
    const remoteQuickFill = resolveRelationQuickFillOption(rows, keyword, inline.match);
    if (remoteQuickFill) {
      setMany2oneOption(node.name, remoteQuickFill);
      continue;
    }
    if (hasAmbiguousRelationMatches(rows, keyword, inline.match)) {
      relationKeywords[node.name] = keyword;
      await openRelationSearchDialog(node.name, descriptor);
      issues.push(`${node.label || descriptor?.string || node.name}存在多个匹配记录，请选择具体记录`);
      continue;
    }
    const beforeErrors = validationErrors.value.slice();
    await quickCreateRelation(node.name, descriptor, keyword);
    const resolvedId = Number(formData[node.name] || 0);
    if (!Number.isFinite(resolvedId) || resolvedId <= 0) {
      const createdErrors = validationErrors.value.length
        ? validationErrors.value.slice()
        : [relationUiLabel(descriptor, 'inline_create_failed', '保存时创建失败')];
      issues.push(...createdErrors);
      validationErrors.value = beforeErrors;
    }
  }
  return Array.from(new Set(issues)).slice(0, 5);
}

async function resolvePendingMany2manyTagCreates() {
  const issues: string[] = [];
  for (const [name, rawKeyword] of Object.entries(relationKeywords)) {
    const keyword = String(rawKeyword || '').trim();
    if (!keyword) continue;
    if (!isFieldWritable(name)) continue;
    if (!Array.isArray(formData[name])) continue;
    const descriptor = contract.value?.fields?.[name];
    if (!relationModel(name)) continue;
    const inline = relationInlineCreate(descriptor);
    if (!inline.enabled || !inline.createOnNoMatch) continue;
    const fieldLabel = layoutNodes.value.find((node) => node.kind === 'field' && node.name === name)?.label
      || descriptor?.string
      || name;
    const localQuickFill = resolveRelationQuickFillOption(relationOptionsForField(name), keyword, inline.match);
    if (localQuickFill) {
      addRelationId(name, localQuickFill);
      continue;
    }
    const rows = await queryRelationOptions(name, keyword);
    const remoteQuickFill = resolveRelationQuickFillOption(rows, keyword, inline.match);
    if (remoteQuickFill) {
      addRelationId(name, remoteQuickFill);
      continue;
    }
    if (hasAmbiguousRelationMatches(rows, keyword, inline.match)) {
      issues.push(`${fieldLabel}存在多个匹配记录，请选择具体记录`);
      continue;
    }
    const beforeErrors = validationErrors.value.slice();
    await quickCreateMany2manyTag(name);
    const created = !relationKeyword(name).trim();
    if (!created) {
      const createdErrors = validationErrors.value.length
        ? validationErrors.value.slice()
        : [relationUiLabel(descriptor, 'inline_create_failed', '保存时创建失败')];
      issues.push(...createdErrors);
      validationErrors.value = beforeErrors;
    }
  }
  return Array.from(new Set(issues)).slice(0, 5);
}

function setSelectionField(name: string, value: string) {
  formData[name] = value || false;
  markFieldChanged(name);
}

function setRelationMultiField(name: string, target: HTMLSelectElement) {
  const ids = Array.from(target.selectedOptions)
    .map((item) => Number(item.value))
    .filter((id) => Number.isFinite(id) && id > 0)
    .map((id) => Math.trunc(id));
  formData[name] = ids;
  markFieldChanged(name);
}

function setRelationIds(name: string, ids: number[]) {
  formData[name] = Array.from(new Set((ids || [])
    .map((id) => Number(id))
    .filter((id) => Number.isFinite(id) && id > 0)
    .map((id) => Math.trunc(id))));
  markFieldChanged(name);
}

function addRelationId(name: string, option: RelationOption) {
  upsertRelationOption(name, option);
  setRelationIds(name, [...relationIds(name), option.id]);
  relationKeywords[name] = '';
}

async function quickCreateMany2manyTag(name: string) {
  const descriptor = contract.value?.fields?.[name];
  const relation = relationModel(name);
  const label = relationKeyword(name).trim();
  if (!relation || !label) return;
  const inline = relationInlineCreate(descriptor);
  if (!inline.enabled || !inline.createOnNoMatch) return;
  const existing = resolveRelationQuickFillOption(relationOptionsForField(name), label, inline.match);
  if (existing) {
    addRelationId(name, existing);
    return;
  }
  const nameField = inline.nameField || 'name';
  try {
    const entry = relationEntry(descriptor);
    const vals: Record<string, unknown> = { ...(entry?.defaultVals || {}), [nameField]: label };
    if (relation === 'sc.dictionary' && typeof vals.type === 'string' && String(vals.type || '').trim()) {
      vals.code = label.toUpperCase().replace(/\s+/g, '_').slice(0, 60);
    }
    const created = await createContractFormRecord({ model: relation, vals });
    const id = Number(created?.id || 0);
    if (Number.isFinite(id) && id > 0) {
      addRelationId(name, { id: Math.trunc(id), label });
      await queryRelationOptions(name, '');
    }
  } catch (err) {
    validationErrors.value = [
      sanitizeUiErrorMessage(err instanceof Error ? err.message : err, relationUiLabel(descriptor, 'quick_create_failed')),
    ];
  }
}

function setTextField(name: string, value: string) {
  formData[name] = value;
  markFieldChanged(name);
}

function markFieldChanged(name: string) {
  const key = String(name || '').trim();
  if (!key || applyingOnchangePatch.value) return;
  dirtyFieldSet.add(key);
  changedFieldSet.add(key);
  scheduleOnchange();
}

function scheduleOnchange() {
  if (onchangeTimer) clearTimeout(onchangeTimer);
  onchangeTimer = setTimeout(() => {
    void runOnchangeRoundtrip();
  }, 300);
}

function buildOnchangeValues() {
  const out: Record<string, unknown> = {};
  Object.keys(contract.value?.fields || {}).forEach((name) => {
    const descriptor = contract.value?.fields?.[name];
    const ttype = fieldType(descriptor);
    if (ttype === 'many2many') {
      out[name] = buildX2ManyCommands({
        kind: ttype,
        current: formData[name],
        original: originalValues.value[name],
        mode: 'onchange',
      });
      return;
    }
    if (ttype === 'one2many') {
      out[name] = buildOne2manyCommandValue(name, 'onchange');
      return;
    }
    out[name] = normalizeFieldValue(name, formData[name]);
  });
  if (recordId.value) out.id = recordId.value;
  return out;
}

async function runOnchangeRoundtrip() {
  if (!model.value) return;
  if (!changedFieldSet.size) return;
  const changed = Array.from(changedFieldSet);
  changedFieldSet.clear();
  try {
    const response = await triggerOnchange({
      model: model.value,
      res_id: recordId.value,
      values: buildOnchangeValues(),
      changed_fields: changed,
      context: pickContractNavQuery(route.query as Record<string, unknown>),
    });
    const patch = response?.patch;
    const modifiersPatch = response?.modifiers_patch;
    const linePatches = Array.isArray(response?.line_patches) ? response.line_patches : [];
    const warnings = Array.isArray(response?.warnings) ? response.warnings : [];
    onchangeWarnings.value = warnings;
    onchangeLinePatches.value = linePatches;
    if (modifiersPatch && typeof modifiersPatch === 'object') {
      onchangeModifiersPatch.value = {
        ...onchangeModifiersPatch.value,
        ...(modifiersPatch as Record<string, Record<string, unknown>>),
      };
      const patchedFields = Object.keys(modifiersPatch as Record<string, Record<string, unknown>>);
      await Promise.all(
        patchedFields.map(async (name) => {
          const descriptor = contract.value?.fields?.[name];
          const ttype = fieldType(descriptor);
          if (!['many2one', 'many2many', 'one2many'].includes(ttype)) return;
          await queryRelationOptions(name, relationKeyword(name));
        }),
      );
    }
    if (patch && typeof patch === 'object') {
      applyingOnchangePatch.value = true;
      Object.entries(patch).forEach(([name, value]) => {
        if (!(name in (contract.value?.fields || {}))) return;
        const ttype = fieldType(contract.value?.fields?.[name]);
        if (ttype === 'many2many' || ttype === 'one2many') {
          formData[name] = Array.isArray(value) ? value : [];
          if (ttype === 'one2many') initOne2manyRows(name, formData[name]);
        } else if (ttype === 'many2one') {
          const option = parseMany2oneDisplay(value);
          upsertRelationOption(name, option);
          const ids = normalizeRelationIds(value);
          const nextId = ids.length ? ids[0] : false;
          if (!nextId) {
            const currentIds = relationIds(name);
            const selectedOption = currentIds.length
              ? (relationOptions.value[name] || []).find((item) => item.id === currentIds[0])
              : null;
            const staleKeyword = relationKeyword(name).trim() || String(selectedOption?.label || '').trim();
            if (staleKeyword) invalidatedRelationKeywords[name] = staleKeyword;
            clearedDynamicRelationFields[name] = true;
            if (relationQueryTimers[name]) {
              clearTimeout(relationQueryTimers[name]);
              delete relationQueryTimers[name];
            }
          }
          const node = layoutNodes.value.find((item) => item.kind === 'field' && item.name === name);
          const readonly = Boolean(node?.readonly || contract.value?.fields?.[name]?.readonly);
          formData[name] = readonly && option ? [option.id, option.label] : nextId;
          relationKeywords[name] = option?.label || (nextId ? relationKeywords[name] || `#${nextId}` : '');
        } else if (ttype === 'date') {
          formData[name] = toDateInputValue(value);
        } else if (ttype === 'datetime') {
          formData[name] = toDatetimeInputValue(value);
        } else {
          formData[name] = value;
        }
      });
      applyingOnchangePatch.value = false;
    }
    if (linePatches.length) {
      applyingOnchangePatch.value = true;
      applyOnchangeLinePatches(linePatches);
      applyingOnchangePatch.value = false;
    }
  } catch {
    // Onchange is best-effort; keep current values when roundtrip fails.
  }
}

function collectWritableValues() {
  const values = layoutNodes.value
    .filter((node) => node.kind === 'field' && !node.readonly && isWritableFieldVisible(node.name))
    .reduce<Record<string, unknown>>((acc, node) => {
      if (recordId.value && !dirtyFieldSet.has(node.name)) {
        return acc;
      }
      const value = normalizeFieldValue(node.name, formData[node.name]);
      const ttype = fieldType(node.descriptor);
      if ((ttype === 'many2many' || ttype === 'one2many') && Array.isArray(value) && !value.length) {
        return acc;
      }
      acc[node.name] = value;
      return acc;
    }, {});
  const statusField = nativeStatusbar.value.field;
  if (
    recordId.value
    && statusField
    && dirtyFieldSet.has(statusField)
    && !nativeStatusbar.value.readonly
    && statusField in (contract.value?.fields || {})
    && !(statusField in values)
  ) {
    values[statusField] = normalizeFieldValue(statusField, formData[statusField]);
  }
  return values;
}

function isRequiredFieldEmpty(value: unknown, descriptor?: FieldDescriptor | null) {
  return isRequiredFieldEmptyByType(value, fieldType(descriptor));
}

function collectRequiredFieldIssues(values: Record<string, unknown>) {
  const missing = layoutNodes.value
    .filter((node) => node.kind === 'field' && !node.readonly && isWritableFieldVisible(node.name))
    .filter((node) => {
      const descriptor = node.descriptor || contract.value?.fields?.[node.name];
      if (!descriptor?.required) return false;
      const value = Object.prototype.hasOwnProperty.call(values, node.name)
        ? values[node.name]
        : normalizeFieldValue(node.name, formData[node.name]);
      return isRequiredFieldEmpty(value, descriptor);
    })
    .map((node) => String(node.label || node.descriptor?.string || node.name).trim())
    .filter(Boolean);
  if (!missing.length) return [];
  return [`保存前请填写：${Array.from(new Set(missing)).slice(0, 5).join('、')}`];
}

function formCreateContext() {
  const storeContext = resolveContractV2SourceContext(v2ContractStore.value);
  const sourceContext = (Object.keys(storeContext).length ? storeContext : resolveUnifiedPageContractV2SourceContext(contract.value)).context || {};
  return sourceContext;
}

function resolveCreateDefaults() {
  const storeMainData = resolveContractV2MainData(v2ContractStore.value);
  const defaults: Record<string, unknown> = {
    ...(Object.keys(storeMainData).length ? storeMainData : resolveUnifiedPageContractV2MainData(contract.value)),
  };
  Object.entries(route.query as Record<string, unknown>).forEach(([key, value]) => {
    if (key.startsWith('default_')) {
      defaults[key.replace(/^default_/, '')] = normalizeRouteDefault(value);
    }
  });
  const context = formCreateContext();
  Object.entries(context).forEach(([key, value]) => {
    if (key.startsWith('default_') && !(key.replace(/^default_/, '') in defaults)) {
      defaults[key.replace(/^default_/, '')] = value;
    }
  });
  const validator = contract.value?.validator as Record<string, unknown> | undefined;
  const defaultsSample = validator?.defaults_sample;
  if (defaultsSample && typeof defaultsSample === 'object' && !Array.isArray(defaultsSample)) {
    Object.entries(defaultsSample as Record<string, unknown>).forEach(([key, value]) => {
      if (!(key in defaults)) {
        defaults[key] = value === 'dynamic' ? '' : value;
      }
    });
  }
  const selectedProject = session.projectContext?.selected;
  const selectedProjectId = Number(selectedProject?.id || 0);
  if (
    selectedProjectId > 0
    && contract.value?.fields?.project_id
    && normalizeRelationIds(defaults.project_id).length === 0
  ) {
    defaults.project_id = [
      selectedProjectId,
      selectedProject?.display_name || selectedProject?.name || `项目 ${selectedProjectId}`,
    ];
  }
  const selectedStrategy = String(selectedProject?.operation_strategy || '').trim();
  if (
    selectedStrategy
    && contract.value?.fields?.operation_strategy
    && !String(defaults.operation_strategy || '').trim()
  ) {
    defaults.operation_strategy = selectedStrategy;
  }
  const selectedOwnerId = Number(selectedProject?.owner_id || 0);
  if (
    selectedOwnerId > 0
    && contract.value?.fields?.owner_id
    && normalizeRelationIds(defaults.owner_id).length === 0
  ) {
    defaults.owner_id = [
      selectedOwnerId,
      selectedProject?.owner_name || `业主 ${selectedOwnerId}`,
    ];
  }
  return defaults;
}

function resolveNavigationUrl(url: string) {
  return resolveNavigationUrlFromOrigin(url, window.location.origin);
}

function syncContractV2ShadowStore(rawContract: unknown) {
  v2ContractStore.value = null;
  v2ContractDecodeError.value = '';
  try {
    const snapshot = decodeContractV2Snapshot(resolveUnifiedPageContractV2(rawContract) || rawContract);
    v2ContractStore.value = createContractV2Store(snapshot);
  } catch (err) {
    if (err instanceof ContractV2DecodeError) {
      v2ContractDecodeError.value = err.issues.slice(0, 4).map((issue) => `${issue.path} ${issue.message}`).join(' | ');
      return;
    }
    v2ContractDecodeError.value = err instanceof Error ? err.message : '表单配置解析失败';
  }
}

const viewOrchestrationHudSummary = computed(() => {
  const rootGovernance = contract.value && typeof contract.value === 'object'
    ? (contract.value as Record<string, unknown>).governance
    : undefined;
  const governance = rootGovernance && typeof rootGovernance === 'object' && !Array.isArray(rootGovernance)
    ? rootGovernance as Record<string, unknown>
    : {};
  const orchestration = governance.view_orchestration && typeof governance.view_orchestration === 'object' && !Array.isArray(governance.view_orchestration)
    ? governance.view_orchestration as Record<string, unknown>
    : {};
  const views = orchestration.views && typeof orchestration.views === 'object' && !Array.isArray(orchestration.views)
    ? orchestration.views as Record<string, unknown>
    : {};
  const current = (views.form || {}) as Record<string, unknown>;
  const contracts = Array.isArray(current.business_config_contracts)
    ? current.business_config_contracts as Array<Record<string, unknown>>
    : [];
  const businessConfigFormFields = Array.isArray(current.business_config_form_fields)
    ? current.business_config_form_fields.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  const skippedLegacyPolicyFields = Array.isArray(current.skipped_legacy_policy_fields)
    ? current.skipped_legacy_policy_fields.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  return {
    applied: Boolean(orchestration.applied || current.applied || contracts.length),
    owner: String(orchestration.owner_layer || current.owner_layer || '-'),
    contractCount: contracts.length,
    contractNames: contracts.map((row) => String(row.name || row.id || '').trim()).filter(Boolean).join(',') || '-',
    legacyOverlay: Boolean(current.legacy_field_policy_overlay),
    businessConfigFieldCount: businessConfigFormFields.length,
    skippedLegacyPolicyFields: skippedLegacyPolicyFields.join(',') || '-',
  };
});

const hudEntries = computed(() => [
  { label: '业务对象', value: model.value || '-' },
  { label: '操作编号', value: actionId.value || '-' },
  { label: '记录编号', value: recordIdDisplay.value },
  { label: '配置已加载', value: Boolean(contract.value) },
  { label: '配置可用', value: contractReadiness.value.usable },
  { label: '配置问题数', value: contractReadiness.value.issues.length },
  { label: '新版配置暂存可用', value: v2ShadowStoreReady.value },
  { label: '新版配置组件数', value: v2ShadowWidgetCount.value },
  { label: '新版配置操作数', value: v2ShadowActionCount.value },
  { label: '新版配置按钮状态数', value: v2ShadowButtonStatusCount.value },
  { label: '新版配置字段编码数', value: v2ShadowFieldCodeCount.value },
  { label: '新版配置字段重叠数', value: v2ShadowLegacyFieldOverlapCount.value },
  { label: '新版配置缺失字段', value: v2ShadowLegacyFieldMissingPreview.value },
  { label: '新版配置布局来源', value: v2ShadowLayoutSourceKind.value },
  { label: '新版配置全局来源', value: v2ShadowGlobalSourceKind.value },
  { label: '新版配置上下文来源', value: v2ShadowSourceContextKind.value },
  { label: '新版配置状态字段数', value: v2ShadowStatusFieldCount.value },
  { label: '新版配置值字段数', value: v2ShadowValueFieldCount.value },
  { label: '新版配置主数据字段数', value: v2ShadowMainDataFieldCount.value },
  { label: '新版配置只读值数', value: v2ShadowReadonlyValueCount.value },
  { label: '新版配置值来源', value: v2ShadowValueSourceKind.value },
  { label: '配置解析问题', value: v2ContractDecodeError.value || '-' },
  { label: '配置视图类型', value: contract.value?.head?.view_type || contract.value?.view_type || '-' },
  { label: '页面编排已应用', value: viewOrchestrationHudSummary.value.applied },
  { label: '页面编排责任层', value: viewOrchestrationHudSummary.value.owner },
  { label: '页面编排配置数', value: viewOrchestrationHudSummary.value.contractCount },
  { label: '页面编排名称', value: viewOrchestrationHudSummary.value.contractNames },
  { label: '表单配置字段数', value: viewOrchestrationHudSummary.value.businessConfigFieldCount },
  { label: '跳过策略字段', value: viewOrchestrationHudSummary.value.skippedLegacyPolicyFields },
  { label: '历史策略覆盖', value: viewOrchestrationHudSummary.value.legacyOverlay },
  { label: '渲染档位', value: renderProfile.value },
  { label: '字段数', value: Object.keys(contract.value?.fields || {}).length },
  { label: '布局节点数', value: layoutNodes.value.length },
  { label: '可写字段数', value: writableFieldCount.value },
  { label: '已变更字段数', value: changedFieldCount.value },
  { label: '操作数', value: contractActions.value.length },
  { label: '权限', value: `${rights.value.read ? 'R' : '-'}${rights.value.write ? 'W' : '-'}${rights.value.create ? 'C' : '-'}${rights.value.unlink ? 'D' : '-'}` },
  { label: '联动提醒数', value: onchangeWarnings.value.length },
  { label: '明细联动补丁数', value: onchangeLinePatches.value.length },
]);

type FormContractReadiness = {
  usable: boolean;
  issues: string[];
  fieldCount: number;
  layoutFieldCount: number;
  visibleCandidateCount: number;
};

function analyzeFormContractReadiness(
  data: unknown,
  options?: { requirePureFormViewType?: boolean },
): FormContractReadiness {
  const issues: string[] = [];
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return { usable: false, issues: ['contract payload is not an object'], fieldCount: 0, layoutFieldCount: 0, visibleCandidateCount: 0 };
  }
  const row = data as Record<string, unknown>;
  const requirePureFormViewType = options?.requirePureFormViewType !== false;
  const collectLayoutFieldNames = (layoutRaw: unknown): Set<string> => {
    const names = new Set<string>();
    type LayoutGroupLike = { fields?: Array<Record<string, unknown>>; sub_groups?: LayoutGroupLike[] };
    type LayoutPageLike = { groups?: LayoutGroupLike[] };
    type LayoutNotebookLike = { pages?: LayoutPageLike[] };

    const walkStructuredGroup = (groupRaw: unknown) => {
      if (!groupRaw || typeof groupRaw !== 'object' || Array.isArray(groupRaw)) return;
      const group = groupRaw as LayoutGroupLike;
      const fields = Array.isArray(group.fields) ? group.fields : [];
      fields.forEach((fieldRaw) => {
        const field = fieldRaw && typeof fieldRaw === 'object' ? fieldRaw : {};
        const fieldName = String((field as Record<string, unknown>).name || '').trim();
        if (fieldName) names.add(fieldName);
      });
      const subGroups = Array.isArray(group.sub_groups) ? group.sub_groups : [];
      subGroups.forEach((sub) => walkStructuredGroup(sub));
    };

    const walkLegacyNode = (nodeRaw: unknown) => {
      if (Array.isArray(nodeRaw)) {
        nodeRaw.forEach((item) => walkLegacyNode(item));
        return;
      }
      if (!nodeRaw || typeof nodeRaw !== 'object') return;
      const node = nodeRaw as Record<string, unknown>;
      const kind = String(node.type || '').trim().toLowerCase();
      if (kind === 'field') {
        const fieldName = String(node.name || '').trim();
        if (fieldName) names.add(fieldName);
      }
      ['children', 'tabs', 'pages', 'nodes', 'items'].forEach((key) => walkLegacyNode(node[key]));
    };

    if (Array.isArray(layoutRaw)) {
      walkLegacyNode(layoutRaw);
      return names;
    }
    if (!layoutRaw || typeof layoutRaw !== 'object') {
      return names;
    }

    const layout = layoutRaw as Record<string, unknown>;
    const groups = Array.isArray(layout.groups) ? layout.groups : [];
    groups.forEach((group) => walkStructuredGroup(group));
    const notebooks = Array.isArray(layout.notebooks) ? layout.notebooks : [];
    notebooks.forEach((notebookRaw) => {
      const notebook = notebookRaw && typeof notebookRaw === 'object' && !Array.isArray(notebookRaw)
        ? notebookRaw as LayoutNotebookLike
        : null;
      const pages = Array.isArray(notebook?.pages) ? notebook.pages : [];
      pages.forEach((pageRaw) => {
        const page = pageRaw && typeof pageRaw === 'object' && !Array.isArray(pageRaw)
          ? pageRaw as LayoutPageLike
          : null;
        const pageGroups = Array.isArray(page?.groups) ? page.groups : [];
        pageGroups.forEach((group) => walkStructuredGroup(group));
      });
    });

    if (!names.size) {
      walkLegacyNode(layoutRaw);
    }
    return names;
  };

  const v2 = resolveUnifiedPageContractV2(row);
  const v2FieldNames = collectUnifiedPageContractV2FieldWidgets(row)
    .map((widget) => String(widget.fieldCode || '').trim())
    .filter(Boolean);
  const v2FieldNameSet = new Set(v2FieldNames);
  const fields = row.fields;
  const fieldMap = fields && typeof fields === 'object' && !Array.isArray(fields)
    ? fields as Record<string, unknown>
    : {};
  const fieldNames = Array.from(new Set([...Object.keys(fieldMap), ...v2FieldNames]));
  if (!fieldNames.length) {
    issues.push('contract.fields is empty');
  }

  const views = row.views;
  const formView = views && typeof views === 'object' && !Array.isArray(views)
    ? (views as Record<string, unknown>).form
    : undefined;
  const hasV2Form = v2?.pageInfo?.viewType === 'form' && v2FieldNames.length > 0;
  if (!hasV2Form && (!formView || typeof formView !== 'object' || Array.isArray(formView))) {
    issues.push('contract.views.form is missing');
  }
  const layout = formView && typeof formView === 'object' && !Array.isArray(formView)
    ? (formView as Record<string, unknown>).layout
    : {};
  const layoutFieldNames = collectLayoutFieldNames(layout);

  const head = row.head;
  const headViewType = head && typeof head === 'object' && !Array.isArray(head)
    ? String((head as Record<string, unknown>).view_type || '').trim().toLowerCase()
    : '';
  const viewType = String(row.view_type || '').trim().toLowerCase();
  const v2ViewType = String(v2?.pageInfo?.viewType || '').trim().toLowerCase();
  if (requirePureFormViewType) {
    if (headViewType && headViewType !== 'form') issues.push(`页面头部视图为 ${viewTypeDisplayLabel(headViewType)}，应为表单视图`);
    if (viewType && viewType !== 'form') issues.push(`页面视图为 ${viewTypeDisplayLabel(viewType)}，应为表单视图`);
    if (v2ViewType && v2ViewType !== 'form') issues.push(`页面结构视图为 ${viewTypeDisplayLabel(v2ViewType)}，应为表单视图`);
  }

  const visible = resolveUnifiedPageContractV2VisibleFields(row);
  const visibleNameSet = new Set(visible);
  const groupNames = new Set<string>();
  const groups = resolveUnifiedPageContractV2FieldGroups(row);
  groups.forEach((item) => {
    if (!item || typeof item !== 'object') return;
    const fieldsRaw = (item as Record<string, unknown>).fields;
    if (!Array.isArray(fieldsRaw)) return;
    fieldsRaw.forEach((name) => {
      const normalized = String(name || '').trim();
      if (normalized) groupNames.add(normalized);
    });
  });
  v2FieldNames.forEach((name) => layoutFieldNames.add(name));
  if (!layoutFieldNames.size && !groupNames.size && !visibleNameSet.size) {
    issues.push('contract.views.form.layout has no field nodes');
  }
  const visibleCandidates = fieldNames.filter((name) =>
    visibleNameSet.has(name) || groupNames.has(name) || layoutFieldNames.has(name) || v2FieldNameSet.has(name),
  );
  if (fieldNames.length && !visibleCandidates.length) {
    issues.push('no visible field candidate from visible_fields/field_groups/layout');
  }

  return {
    usable: issues.length === 0,
    issues,
    fieldCount: fieldNames.length,
    layoutFieldCount: layoutFieldNames.size,
    visibleCandidateCount: visibleCandidates.length,
  };
}

function validateSurfaceMarkers(
  data: unknown,
  meta: Record<string, unknown> | null,
  expectedSurface: 'user' | 'native' | 'hud',
) {
  const issues: string[] = [];
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return { ok: false, issues: ['contract payload is not an object'] };
  }
  const row = data as Record<string, unknown>;
  const contractSurface = String(row.contract_surface || '').trim().toLowerCase();
  const renderMode = String(row.render_mode || '').trim().toLowerCase();
  const sourceMode = String(row.source_mode || '').trim().toLowerCase();
  const governedFromNative = row.governed_from_native;
  const surfaceMapping = row.surface_mapping;
  const metaSurface = String(meta?.contract_surface || '').trim().toLowerCase();

  if (!contractSurface) issues.push('missing contract_surface');
  if (!renderMode) issues.push('missing render_mode');
  if (!sourceMode) issues.push('missing source_mode');
  if (typeof governedFromNative !== 'boolean') issues.push('missing governed_from_native');
  if (!surfaceMapping || typeof surfaceMapping !== 'object' || Array.isArray(surfaceMapping)) {
    issues.push('missing surface_mapping');
  }

  if (metaSurface && contractSurface && metaSurface !== contractSurface) {
    issues.push(`meta.contract_surface=${metaSurface} mismatch data.contract_surface=${contractSurface}`);
  }
  if (contractSurface && contractSurface !== expectedSurface) {
    issues.push(`contract_surface=${contractSurface} mismatch expected=${expectedSurface}`);
  }

  if (contractSurface === 'native') {
    if (renderMode !== 'native') issues.push(`native surface requires render_mode=native, got ${renderMode || '-'}`);
    if (governedFromNative !== false) issues.push('native surface requires governed_from_native=false');
  } else if (contractSurface === 'user' || contractSurface === 'hud') {
    if (renderMode !== 'governed') issues.push(`governed surface requires render_mode=governed, got ${renderMode || '-'}`);
    if (governedFromNative !== true) issues.push('governed surface requires governed_from_native=true');
  }

  return { ok: issues.length === 0, issues };
}

function contractModelName(data: unknown) {
  if (!data || typeof data !== 'object') return '';
  const row = data as Record<string, unknown>;
  const head = row.head && typeof row.head === 'object' && !Array.isArray(row.head)
    ? row.head as Record<string, unknown>
    : {};
  return String(head.model || row.model || '').trim();
}

function routeContractContext() {
  const context: Record<string, unknown> = {};
  Object.entries(route.query as Record<string, unknown>).forEach(([key, value]) => {
    if (key.startsWith('default_')) {
      context[key] = normalizeRouteDefault(value);
    }
  });
  [
    'current_business_category_code',
    'default_business_category_code',
    'allowed_business_category_codes',
    'current_business_category_label',
    'default_business_category_label',
  ].forEach((key) => {
    const value = (route.query as Record<string, unknown>)[key];
    if (value === undefined || value === null || value === '') return;
    if (Array.isArray(value)) {
      const items = value
        .map((item) => String(item || '').trim())
        .filter((item) => item !== '');
      if (items.length) context[key] = items;
      return;
    }
    const text = String(value).trim();
    if (text) context[key] = text;
  });
  const intakeMode = String(route.query.intake_mode || '').trim().toLowerCase();
  if (intakeMode === 'quick' || intakeMode === 'standard') {
    context.intake_mode = intakeMode;
  }
  return context;
}

async function loadContract() {
  v2ContractStore.value = null;
  v2ContractDecodeError.value = '';
  const profile = recordId.value ? 'edit' : 'create';
  const currentModel = String(model.value || '').trim();
  const contractContext = routeContractContext();
  const contextRaw = String(route.query.context_raw || '').trim();
  const requestedViewId = toPositiveInt(route.query.view_id) || toPositiveInt(route.query.viewId) || 0;
  let response: Awaited<ReturnType<typeof loadActionContractRaw>> | null = null;
  if (actionId.value) {
    try {
      response = await loadActionContractRaw(actionId.value, {
        menuId: menuId.value || undefined,
        viewId: requestedViewId || undefined,
        recordId: recordId.value,
        renderProfile: profile,
        surface: requestedSurface.value,
        sourceMode: requestedSourceMode.value,
        context: contractContext,
        contextRaw,
      });
      const actionReadiness = analyzeFormContractReadiness(response?.data, { requirePureFormViewType: true });
      const actionModel = contractModelName(response?.data);
      if (!actionReadiness.usable || (currentModel && actionModel && actionModel !== currentModel)) {
        response = null;
      }
    } catch {
      response = null;
    }
  }
  if (!response && currentModel) {
    response = await loadModelContractRaw(currentModel, {
      viewType: 'form',
      viewId: requestedViewId || undefined,
      recordId: recordId.value,
      renderProfile: profile,
      surface: requestedSurface.value,
      sourceMode: requestedSourceMode.value,
      context: contractContext,
      contextRaw,
    });
  }
  if (!response?.data || typeof response.data !== 'object') {
    throw new Error('表单配置返回为空');
  }
  const markerCheck = validateSurfaceMarkers(
    response.data,
    (response.meta as Record<string, unknown> | null) || null,
    requestedSurface.value,
  );
  if (!markerCheck.ok) {
    throw new Error(`表单配置标记不完整：${markerCheck.issues.slice(0, 4).join(' | ')}`);
  }
  const readiness = analyzeFormContractReadiness(response.data, { requirePureFormViewType: false });
  if (!readiness.usable) {
    throw new Error(`表单配置暂不可渲染：${readiness.issues.slice(0, 4).join(' | ')}`);
  }
  contract.value = response.data as ActionContract;
  contractMeta.value = response.meta || null;
  syncContractV2ShadowStore(response.data);
  mergeNativeLayoutFieldDescriptorsIntoContract();
  const policy = contractAccessPolicy.value;
  if (policy.mode === 'block') {
    const message = policy.message || 'contract access policy blocked this page';
    throw new ContractAccessPolicyError(message, policy.reasonCode || 'CONTRACT_ACCESS_BLOCKED');
  }
  const hasCore = coreFieldNames.value.length > 0;
  advancedExpanded.value = renderProfile.value !== 'create' || !hasCore;
}

async function loadRecord() {
  const versionPolicy = recordVersionPolicy();
  const fieldNames = formDataFieldNames();
  if (versionPolicy?.tokenField && !fieldNames.includes(versionPolicy.tokenField)) {
    fieldNames.push(versionPolicy.tokenField);
  }
  recordVersionToken.value = '';
  closeNativeChatterComposer();
  chatterError.value = '';
  chatterTimeline.value = [];
  attachmentError.value = '';
  if (!recordId.value) {
    pendingNativeAttachments.value = [];
    nativeChatterAutoLoadKey.value = '';
  }
  Object.keys(formData).forEach((key) => {
    delete formData[key];
  });
  Object.keys(relationKeywords).forEach((key) => {
    delete relationKeywords[key];
  });
  relationOptions.value = {};
  Object.keys(one2manyRows).forEach((key) => {
    delete one2manyRows[key];
  });
  onchangeModifiersPatch.value = {};
  onchangeWarnings.value = [];
  onchangeLinePatches.value = [];
  changedFieldSet.clear();
  dirtyFieldSet.clear();
  if (onchangeTimer) {
    clearTimeout(onchangeTimer);
    onchangeTimer = null;
  }
  if (!recordId.value) {
    const defaults = resolveCreateDefaults();
    fieldNames.forEach((name) => {
      const descriptor = contract.value?.fields?.[name];
      const ttype = fieldType(descriptor);
      const incoming = name in defaults ? defaults[name] : '';
      if (ttype === 'many2many' || ttype === 'one2many') {
        formData[name] = Array.isArray(incoming) ? incoming : [];
        if (ttype === 'one2many') initOne2manyRows(name, formData[name]);
      } else if (ttype === 'many2one') {
        const option = parseMany2oneDisplay(incoming);
        upsertRelationOption(name, option);
        const ids = normalizeRelationIds(incoming);
        formData[name] = ids.length ? ids[0] : false;
        const matched = ids.length
          ? (relationOptions.value[name] || []).find((item) => item.id === ids[0])
          : null;
        relationKeywords[name] = matched?.label || option?.label || '';
      } else if (ttype === 'date') {
        formData[name] = toDateInputValue(incoming);
      } else if (ttype === 'datetime') {
        formData[name] = toDatetimeInputValue(incoming);
      } else {
        formData[name] = incoming;
      }
    });
    originalValues.value = fieldNames.reduce<Record<string, unknown>>((acc, name) => {
      const value = formData[name];
      if (Array.isArray(value)) {
        acc[name] = [...value];
      } else if (value && typeof value === 'object') {
        acc[name] = JSON.parse(JSON.stringify(value));
      } else {
        acc[name] = value;
      }
      return acc;
    }, {});
    nativeLayoutVisibilityRevision.value += 1;
    restoreIntakeAutosave();
    return;
  }
  const read = await readContractFormRecord({
    model: model.value,
    ids: [recordId.value],
    fields: fieldNames.length ? fieldNames : '*',
  });
  const row = read.records?.[0] || {};
  const storeMainData = resolveContractV2MainData(v2ContractStore.value);
  const contractMainData = Object.keys(storeMainData).length ? storeMainData : resolveUnifiedPageContractV2MainData(contract.value);
  if (versionPolicy?.tokenField) {
    recordVersionToken.value = String((row as Record<string, unknown>)[versionPolicy.tokenField] || '').trim();
  }
  fieldNames.forEach((name) => {
    if (name === versionPolicy?.tokenField && !contract.value?.fields?.[name]) return;
    const descriptor = contract.value?.fields?.[name];
    const ttype = fieldType(descriptor);
    const incoming = Object.prototype.hasOwnProperty.call(row, name)
      ? (row as Record<string, unknown>)[name]
      : (contractMainData[name] ?? '');
    if (ttype === 'many2many' || ttype === 'one2many') {
      formData[name] = Array.isArray(incoming) ? incoming : [];
      if (ttype === 'one2many') initOne2manyRows(name, formData[name]);
    } else if (ttype === 'many2one') {
      const option = parseMany2oneDisplay(incoming);
      upsertRelationOption(name, option);
      const ids = normalizeRelationIds(incoming);
      formData[name] = ids.length ? ids[0] : false;
      const matched = ids.length
        ? (relationOptions.value[name] || []).find((item) => item.id === ids[0])
        : null;
      relationKeywords[name] = matched?.label || option?.label || '';
    } else if (ttype === 'date') {
      formData[name] = toDateInputValue(incoming);
    } else if (ttype === 'datetime') {
      formData[name] = toDatetimeInputValue(incoming);
    } else {
      formData[name] = incoming;
    }
  });
  originalValues.value = fieldNames.reduce<Record<string, unknown>>((acc, name) => {
    const value = formData[name];
    if (Array.isArray(value)) {
      acc[name] = [...value];
    } else if (value && typeof value === 'object') {
      acc[name] = JSON.parse(JSON.stringify(value));
    } else {
      acc[name] = value;
    }
    return acc;
  }, {});
  nativeLayoutVisibilityRevision.value += 1;
  if (recordId.value && (nativeChatterActions.value.length || nativeAttachments.value)) {
    await loadNativeChatterTimeline(recordId.value, model.value);
  }
}

async function loadNativeChatterTimeline(targetResId = recordId.value, targetModel = model.value) {
  if (!targetResId || !targetModel) return;
  chatterLoading.value = true;
  try {
    const response = await fetchChatterTimeline({
      model: targetModel,
      res_id: targetResId,
      limit: 12,
      include_audit: false,
    });
    chatterTimeline.value = Array.isArray(response.items) ? response.items : [];
  } catch (err) {
    chatterError.value = err instanceof Error ? err.message : '协作记录加载失败';
  } finally {
    chatterLoading.value = false;
  }
}

async function loadCollaborationUsers(query = collaborationUserQuery.value) {
  collaborationUsersLoading.value = true;
  try {
    const response = await searchCollaborationUsers({ query, limit: 20 });
    const items = Array.isArray(response.items) ? response.items : [];
    const merged = new Map<number, CollaborationUserOption>();
    collaborationUserOptions.value.forEach((item) => {
      const id = Number(item.id || 0);
      if (id) merged.set(id, item);
    });
    items.forEach((item) => {
      const id = Number(item.id || 0);
      if (id) merged.set(id, item);
    });
    collaborationUserOptions.value = Array.from(merged.values());
  } catch (err) {
    chatterError.value = err instanceof Error ? err.message : '协作人员加载失败';
  } finally {
    collaborationUsersLoading.value = false;
  }
}

function collaborationUserLabel(user: CollaborationUserOption) {
  return String(user.name || user.login || user.email || user.id || '').trim();
}

function selectMentionUser(user: CollaborationUserOption) {
  const id = Number(user.id || 0);
  if (!id || selectedMentionUserIds.value.includes(id)) return;
  selectedMentionUserIds.value = [...selectedMentionUserIds.value, id];
  collaborationUserQuery.value = '';
}

function removeMentionUser(id: number) {
  selectedMentionUserIds.value = selectedMentionUserIds.value.filter((item) => Number(item) !== Number(id));
}

function selectActivityAssignee(event: Event) {
  const value = Number((event.target as HTMLSelectElement).value || 0);
  activityAssigneeId.value = Number.isFinite(value) && value > 0 ? value : 0;
}

function nextBusinessDateInputValue() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

async function openNativeChatterAction(action: NativeChatterAction) {
  if (!action.enabled) return;
  chatterError.value = '';
  const mode = action.mode || action.intent;
  if (mode === 'message' || mode === 'note' || mode === 'activity') {
    activeChatterMode.value = mode;
    activeChatterLabel.value = action.label;
    if (mode === 'activity' && !activityDeadline.value) {
      activityDeadline.value = nextBusinessDateInputValue();
    }
    if (!chatterTimeline.value.length && !chatterLoading.value) {
      await loadNativeChatterTimeline();
    }
    if (!collaborationUserOptions.value.length && !collaborationUsersLoading.value) {
      await loadCollaborationUsers('');
    }
    return;
  }
  activeChatterMode.value = '';
  activeChatterLabel.value = action.label;
  chatterError.value = `${action.label} 缺少可执行配置`;
}

function handleSceneBlockAction(payload: { action?: { target?: Record<string, unknown> } }) {
  const target = payload?.action?.target && typeof payload.action.target === 'object'
    ? payload.action.target
    : {};
  const targetKind = String(target.kind || '').trim();
  if (targetKind === 'statusbar_value') {
    const value = String(target.value || '').trim();
    if (value) {
      setStatusbarValue(value);
      return;
    }
  }
  const route = String(target.route || '').trim();
  if (route) {
    void router.push(route);
    return;
  }
  const sceneKey = String(target.scene_key || '').trim();
  if (sceneKey) {
    void router.push({ name: 'scene', params: { sceneKey } });
  }
}

function closeNativeChatterComposer() {
  activeChatterMode.value = '';
  activeChatterLabel.value = '';
  chatterDraft.value = '';
  activitySummary.value = '';
  activityDeadline.value = '';
  activityNote.value = '';
  selectedMentionUserIds.value = [];
  activityAssigneeId.value = 0;
  collaborationUserQuery.value = '';
}

async function sendNativeChatter() {
  if (activeChatterMode.value === 'activity') {
    await scheduleNativeChatterActivity();
    return;
  }
  const body = chatterDraft.value.trim();
  if (!body || !recordId.value || !model.value || chatterPosting.value) return;
  chatterPosting.value = true;
  chatterError.value = '';
  try {
    await postChatterMessage({
      model: model.value,
      res_id: recordId.value,
      body,
      subject: activeChatterLabel.value || activeChatterSubmitLabel.value,
      mode: activeChatterMode.value === 'note' ? 'note' : 'message',
      mention_user_ids: selectedMentionUserIds.value,
    });
    chatterDraft.value = '';
    selectedMentionUserIds.value = [];
    chatterError.value = '';
    await loadNativeChatterTimeline();
  } catch (err) {
    chatterError.value = err instanceof Error ? err.message : '协作消息发送失败';
  } finally {
    chatterPosting.value = false;
  }
}

async function scheduleNativeChatterActivity() {
  const summary = activitySummary.value.trim();
  if (!summary) {
    chatterError.value = '请填写计划事项';
    return;
  }
  if (!recordId.value || !model.value || chatterPosting.value) return;
  const action = activeActivityAction.value;
  chatterPosting.value = true;
  chatterError.value = '';
  try {
    await scheduleChatterActivity({
      model: model.value,
      res_id: recordId.value,
      summary,
      note: activityNote.value.trim(),
      date_deadline: activityDeadline.value,
      activity_type_xmlid: String(action?.payload?.activity_type_xmlid || '').trim() || undefined,
      user_id: activityAssigneeId.value || undefined,
    });
    activitySummary.value = '';
    activityDeadline.value = '';
    activityNote.value = '';
    activityAssigneeId.value = 0;
    chatterError.value = '';
    await loadNativeChatterTimeline();
  } catch (err) {
    chatterError.value = err instanceof Error ? err.message : '计划事项创建失败';
  } finally {
    chatterPosting.value = false;
  }
}

function activityEntryId(entry: ChatterTimelineEntry) {
  return Number(entry.activity?.id || entry.id || 0);
}

function isActivityUpdating(entry: ChatterTimelineEntry) {
  const id = activityEntryId(entry);
  return Boolean(id && activityUpdatingIds.value.includes(id));
}

async function updateNativeActivity(entry: ChatterTimelineEntry, action: 'done' | 'cancel') {
  const activityId = activityEntryId(entry);
  if (!activityId || !recordId.value || !model.value || isActivityUpdating(entry)) return;
  activityUpdatingIds.value = [...activityUpdatingIds.value, activityId];
  chatterError.value = '';
  try {
    await updateChatterActivity({
      model: model.value,
      res_id: recordId.value,
      activity_id: activityId,
      action,
      note: action === 'done' ? '计划已完成。' : '计划已取消。',
    });
    await loadNativeChatterTimeline();
  } catch (err) {
    chatterError.value = err instanceof Error ? err.message : action === 'done' ? '完成计划失败' : '取消计划失败';
  } finally {
    activityUpdatingIds.value = activityUpdatingIds.value.filter((id) => id !== activityId);
  }
}

async function onNativeAttachmentSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file || !model.value || attachmentUploading.value) return;
  attachmentError.value = '';
  if (file.size > nativeAttachmentMaxBytes.value) {
    attachmentError.value = nativeAttachmentLabel('size_exceeded', '文件过大');
    input.value = '';
    return;
  }
  if (!recordId.value) {
    pendingNativeAttachments.value = [
      ...pendingNativeAttachments.value,
      {
        key: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        name: file.name,
        size: file.size,
        file,
      },
    ];
    input.value = '';
    return;
  }
  attachmentUploading.value = true;
  try {
    const { data, mimetype } = await fileToBase64(file);
    await uploadFile({
      model: model.value,
      res_id: recordId.value,
      name: file.name,
      mimetype,
      data,
    });
    await loadNativeChatterTimeline();
  } catch (err) {
    attachmentError.value = err instanceof Error ? err.message : nativeAttachmentLabel('upload_failed', '附件上传失败');
  } finally {
    attachmentUploading.value = false;
    input.value = '';
  }
}

function removePendingNativeAttachment(key: string) {
  pendingNativeAttachments.value = pendingNativeAttachments.value.filter((item) => item.key !== key);
}

async function uploadPendingNativeAttachments(resId: number): Promise<boolean> {
  if (!pendingNativeAttachments.value.length || !model.value) return true;
  attachmentError.value = '';
  attachmentUploading.value = true;
  try {
    for (const item of pendingNativeAttachments.value) {
      const { data, mimetype } = await fileToBase64(item.file);
      await uploadFile({
        model: model.value,
        res_id: resId,
        name: item.name,
        mimetype,
        data,
      });
    }
    pendingNativeAttachments.value = [];
    await loadNativeChatterTimeline(resId, model.value);
    return true;
  } catch (err) {
    attachmentError.value = err instanceof Error ? err.message : nativeAttachmentLabel('upload_failed', '附件上传失败');
    validationErrors.value = [attachmentError.value];
    submissionFeedback.value = { kind: 'error', message: attachmentError.value };
    status.value = 'error';
    return false;
  } finally {
    attachmentUploading.value = false;
  }
}

async function openNativeAttachment(att: { id?: number; name?: string; mimetype?: string }) {
  if (!att?.id) return;
  attachmentError.value = '';
  try {
    await attachmentViewerRef.value?.open({ id: Number(att.id) }, att.name);
  } catch (err) {
    attachmentError.value = err instanceof Error ? err.message : nativeAttachmentLabel('download_failed', '附件下载失败');
  }
}

async function reload() {
  const reloadIdentity = formRouteIdentity();
  if (activeReloadPromise && reloadIdentity && reloadIdentity === activeReloadIdentity) {
    return activeReloadPromise;
  }
  const run = (async () => {
    const reloadToken = activeReloadToken + 1;
    activeReloadToken = reloadToken;
    renderErrorMessage.value = '';
    status.value = 'loading';
    errorMessage.value = '';
    validationErrors.value = [];
    showOne2manyErrors.value = false;
    try {
      await loadContract();
      if (reloadToken !== activeReloadToken) return;
      await loadRecord();
      if (reloadToken !== activeReloadToken) return;
      status.value = 'ok';
      retainedRouteIdentity.value = formRouteIdentity();
      void preloadFormAuxiliaryData(reloadToken);
    } catch (err) {
      if (reloadToken !== activeReloadToken) return;
      if (err instanceof ContractAccessPolicyError) {
        await router.push({
          name: 'workbench',
          query: pickContractNavQuery(route.query as Record<string, unknown>, {
            reason: ErrorCodes.CAPABILITY_MISSING,
            action_id: actionId.value || undefined,
            menu_id: Number(route.query.menu_id || 0) || undefined,
            diag: showHud.value ? (err.reasonCode || 'CONTRACT_ACCESS_BLOCKED') : undefined,
          }),
        });
        return;
      }
      errorMessage.value = err instanceof Error ? err.message : '表单加载失败';
      status.value = 'error';
    } finally {
      if (activeReloadIdentity === reloadIdentity) {
        activeReloadPromise = null;
        activeReloadIdentity = '';
      }
    }
  })();
  activeReloadIdentity = reloadIdentity;
  activeReloadPromise = run;
  return run;
}

function ensureFormInitialReload() {
  const identity = formRouteIdentity();
  if (!identity) return;
  if (identity === retainedRouteIdentity.value && status.value === 'ok') return;
  if (status.value === 'loading' || !contract.value) {
    void reload();
  }
}

async function preloadFormAuxiliaryData(reloadToken: number) {
  try {
    await loadRelationOptions();
    if (reloadToken !== activeReloadToken) return;
    await hydrateSelectedRelationOptions();
    if (reloadToken !== activeReloadToken) return;
    await hydrateVisibleOne2manyRows();
  } catch {
    // Auxiliary data can be completed by explicit field interactions after the form renders.
  }
}

async function discardChanges() {
  if (!hasChanges.value || busy.value) return;
  await reload();
}

onErrorCaptured((err) => {
  const message = err instanceof Error ? err.message : String(err || '系统处理问题');
  renderErrorMessage.value = `表单页面打开失败：${message}`;
  return false;
});

async function confirmActionSafety(action: ContractAction) {
  const safety = action.actionSafety;
  if (!safety || safety.classification !== 'danger' || !safety.requiresConfirm) return true;
  const message = safety.confirmMessage || action.hint || action.label;
  return actionSafetyConfirm.open({
    title: '确认执行操作',
    message: String(message || '该操作执行后将立即生效，请确认是否继续。'),
    confirmLabel: '继续',
    cancelLabel: '取消',
    tone: 'danger',
  });
}

async function ensureSavedBeforeRecordAction() {
  if (!hasChanges.value) return true;
  return Boolean(await saveRecord({ on_success: ['scene_projection'] }));
}

function applyClientMode(mode: string, toggle = true) {
  const next = String(mode || '').trim();
  if (!next) return false;
  activeContractMode.value = toggle && activeContractMode.value === next ? '' : next;
  contractModeFeedback.value = '';
  if (!activeContractMode.value) closeContractPromptAction();
  return true;
}

function applyRouteConfigMode(rawMode: unknown) {
  const mode = String(rawMode || '').trim();
  if (isBusinessConfigRuntimeModel(model.value)) {
    if (activeContractMode.value === BUSINESS_CONFIG_MODES.formFieldConfiguration || activeContractMode.value === BUSINESS_CONFIG_MODES.lowCode) {
      activeContractMode.value = '';
    }
    return;
  }
  if (isBusinessConfigMode(mode)) {
    applyClientMode(mode, false);
  }
}

function promptContractActionParams(rule: Record<string, unknown>, providedValues: Record<string, string> = {}) {
  const target = parseMaybeJsonRecord(rule.target);
  const params = { ...parseMaybeJsonRecord(target.params || rule.params) };
  const promptSchema = parseMaybeJsonRecord(target.prompt_schema || target.promptSchema || rule.prompt_schema || rule.promptSchema);
  const fields = Array.isArray(promptSchema.fields) ? promptSchema.fields : [];
  for (const raw of fields) {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) continue;
    const field = raw as Record<string, unknown>;
    const name = String(field.name || '').trim();
    if (!name) continue;
    const label = String(field.label || name).trim();
    const required = field.required !== false;
    const optionRows = Array.isArray(field.options)
      ? field.options.map((item) => parseMaybeJsonRecord(item)).filter((row) => String(row.value || '').trim())
      : [];
    const options = optionRows
      .map((row) => `${String(row.value || '').trim()}=${String(row.label || row.value || '').trim()}`)
      .filter(Boolean);
    const suffix = options.length ? ` (${options.join(', ')})` : '';
    const rawValue = String(providedValues[name] || '').trim();
    const optionMatch = optionRows.find((row) => (
      String(row.value || '').trim() === rawValue
      || String(row.label || '').trim() === rawValue
    ));
    const value = optionMatch ? String(optionMatch.value || '').trim() : rawValue;
    if (required && !value) return null;
    if (value) params[name] = value;
  }
  return params;
}

function openContractModeAction(rule: Record<string, unknown>) {
  const promptFields = rulePromptFields(rule);
  if (!promptFields.length) {
    void runContractRuleAction(rule);
    return;
  }
  Object.keys(contractPromptValues).forEach((key) => {
    delete contractPromptValues[key];
  });
  promptFields.forEach((field) => {
    contractPromptValues[field.name] = field.defaultValue;
  });
  contractPromptRule.value = rule;
  contractModeFeedback.value = '';
}

function closeContractPromptAction() {
  contractPromptRule.value = null;
  Object.keys(contractPromptValues).forEach((key) => {
    delete contractPromptValues[key];
  });
}

async function submitContractPromptAction() {
  const rule = contractPromptRule.value;
  if (!rule) return;
  const params = promptContractActionParams(rule, contractPromptValues);
  if (params === null) return;
  await runContractRuleAction(rule, params);
  closeContractPromptAction();
}

async function runContractRuleAction(rule: Record<string, unknown>, providedParams?: Record<string, unknown>) {
  const target = parseMaybeJsonRecord(rule.target);
  const mode = ruleClientMode(rule);
  const intent = String(rule.intent || target.intent || '').trim();
  if (intent === 'ui.local_mode' || intent === 'ui.mode' || (!intent && mode)) {
    applyClientMode(mode, target.toggle !== false);
    return;
  }
  if (!intent) return;
  if (!providedParams && rulePromptFields(rule).length) {
    openContractModeAction(rule);
    return;
  }
  const params = providedParams || promptContractActionParams(rule);
  if (params === null) return;
  busyKind.value = 'action';
  try {
    await intentRequest({
      intent,
      params,
      context: parseMaybeJsonRecord(target.context),
    });
    contractModeFeedback.value = String(target.success_message || '已更新').trim();
    await reload();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '表单配置操作失败';
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

async function onContractFieldAction(payload: FormSectionFieldActionPayload) {
  const fieldKey = String(payload.field.name || '').trim();
  const actionValue = String(payload.action.value || '').trim();
  if (isContractFieldOrderEditable.value && fieldKey && ['show', 'hide'].includes(actionValue)) {
    fieldVisibilityDraft[fieldKey] = actionValue === 'show';
    fieldVisibilityDirtyKeys[fieldKey] = true;
    formConfigAuditResult.value = null;
    appendFormConfigOperation(actionValue === 'show' ? '显示字段' : '隐藏字段', `${formDesignFieldLabel(fieldKey)} 设置为${actionValue === 'show' ? '显示' : '隐藏'}`);
    contractModeFeedback.value = '字段显示设置已调整，保存后生效';
    return;
  }
  const raw = payload.action.raw;
  if (!raw) return;
  await runContractRuleAction(raw);
}

function onFieldVisibilityDraftChange(fieldKey: string, value: string) {
  fieldVisibilityDraft[fieldKey] = value === 'show';
  fieldVisibilityDirtyKeys[fieldKey] = true;
  fieldVisibilityDirty.value = true;
  formConfigAuditResult.value = null;
  appendFormConfigOperation(value === 'show' ? '显示字段' : '隐藏字段', `${formDesignFieldLabel(fieldKey)} 设置为${value === 'show' ? '显示' : '隐藏'}`);
  contractModeFeedback.value = '字段显示设置已调整，保存后生效';
}

function onFormSettingsFieldSelect(payload: { field: FormSectionFieldSchema; groupTitle: string }) {
  if (!isContractFieldOrderEditable.value) return;
  const fieldKey = String(payload.field.name || payload.field.key || '').trim();
  if (!fieldKey) return;
  rememberFormConfigFieldLabel(fieldKey, payload.field.label);
  if (!Object.prototype.hasOwnProperty.call(fieldVisibilityBase.value, fieldKey)) {
    const row = activeContractModeFieldRows.value.find((item) => item.fieldKey === fieldKey);
    const checkedAction = row?.actions.find((action) => Boolean(action.checked));
    fieldVisibilityBase.value = {
      ...fieldVisibilityBase.value,
      [fieldKey]: checkedAction ? checkedAction.value === 'show' : true,
    };
    if (!Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)) {
      fieldVisibilityDraft[fieldKey] = checkedAction ? checkedAction.value === 'show' : true;
    }
  }
  selectedFormSettingsFieldKey.value = fieldKey;
  selectedFormSettingsFieldLabel.value = String(payload.field.label || fieldKey).trim();
  selectedFormSettingsFieldGroupTitleDraft.value = (
    effectiveFieldGroupTitleForDraft(fieldKey)
    || normalizeFieldGroupTitle(payload.groupTitle)
  );
  selectedFormSettingsFieldGroupTitleEdit.value = selectedFormSettingsFieldGroupTitleDraft.value;
  formSettingsActiveTab.value = 'fields';
}

function selectFormDesignerGroup(title: string) {
  const normalizedTitle = normalizeFieldGroupTitle(title);
  if (!normalizedTitle) return;
  const group = formDesignerGroupNavigatorItems.value.find((item) => fieldGroupTitleMatches(item.title, normalizedTitle));
  const orderedKeys = currentFormOrderedFieldKeys.value.length ? currentFormOrderedFieldKeys.value : currentFormDesignFieldKeys.value;
  const fieldKey = orderedKeys.find((key) => group?.fieldKeys.includes(key)) || group?.fieldKeys[0] || '';
  if (!fieldKey) return;
  onFormSettingsFieldSelect({
    field: {
      name: fieldKey,
      key: fieldKey,
      label: formDesignFieldLabel(fieldKey),
    } as FormSectionFieldSchema,
    groupTitle: normalizedTitle,
  });
}

function selectFormDesignerField(fieldKey: string) {
  const key = String(fieldKey || '').trim();
  if (!key) return;
  onFormSettingsFieldSelect({
    field: {
      name: key,
      key,
      label: formDesignFieldLabel(key),
    } as FormSectionFieldSchema,
    groupTitle: effectiveFieldGroupTitleForDraft(key) || '业务配置字段',
  });
}

function openCentralCustomFieldCreate() {
  const selectedFieldKey = selectedFormSettingsFieldKey.value;
  const groupTitle = selectedFormSettingsFieldGroupTitle.value
    || currentFormGroupOptions.value[0]
    || '业务配置字段';
  openInlineCustomFieldCreate(groupTitle, selectedFieldKey);
}

function moveFieldToGroupEnd(fieldKey: string, groupTitle: string) {
  const sourceFieldKey = String(fieldKey || '').trim();
  const normalizedTargetGroup = normalizeFieldGroupTitle(groupTitle);
  if (!sourceFieldKey || !normalizedTargetGroup) return;
  ensureFieldOrderDraftStartsFromCurrentLayout();
  const draft = fieldOrderDraft.value.filter((key) => key !== sourceFieldKey);
  const targetGroupFieldKeys = draft.filter((key) => (
    fieldGroupTitleMatches(fieldGroupBase.value[key] || fieldGroupDraft[key], normalizedTargetGroup)
  ));
  const anchorFieldKey = targetGroupFieldKeys[targetGroupFieldKeys.length - 1] || '';
  const anchorIndex = anchorFieldKey ? draft.indexOf(anchorFieldKey) : -1;
  draft.splice(anchorIndex >= 0 ? anchorIndex + 1 : draft.length, 0, sourceFieldKey);
  fieldOrderDraft.value = draft;
  fieldOrderPreviewActive.value = true;
  fieldGroupDraft[sourceFieldKey] = normalizedTargetGroup;
  fieldMoveTargetDraft[sourceFieldKey] = anchorFieldKey;
  selectedFormSettingsFieldKey.value = sourceFieldKey;
  selectedFormSettingsFieldLabel.value = draggingFieldLabel.value || formDesignFieldLabel(sourceFieldKey);
  selectedFormSettingsFieldGroupTitleDraft.value = normalizedTargetGroup;
  selectedFormSettingsFieldGroupTitleEdit.value = normalizedTargetGroup;
  formConfigAuditResult.value = null;
  appendFormConfigOperation('移动分组', `${formDesignFieldLabel(sourceFieldKey)} 移动到 ${normalizedTargetGroup}`);
}

function moveSelectedFormSettingsFieldToGroup(groupTitle: string) {
  const fieldKey = selectedFormSettingsFieldKey.value;
  if (!fieldKey) return;
  moveFieldToGroupEnd(fieldKey, groupTitle);
}

function onSelectedFormSettingsFieldGroupMoveChange(event: Event) {
  const target = event.target;
  const targetInput = target as unknown as { value?: unknown };
  const value = target && typeof targetInput.value === 'string'
    ? targetInput.value
    : '';
  moveSelectedFormSettingsFieldToGroup(value);
}

function onFormLayoutColumnsChange(event: Event) {
  const target = event.target as HTMLSelectElement | null;
  const previousColumns = formLayoutColumnsDraft.value;
  const columns = normalizeLowCodeColumns(target?.value, formLayoutColumnsDraft.value);
  if (columns === formLayoutColumnsDraft.value) return;
  const groupTitles = new Set<string>();
  currentFormGroupOptions.value.forEach((title) => {
    const key = normalizeFieldGroupTitle(title);
    if (key) groupTitles.add(key);
  });
  formDesignerGroupNavigatorItems.value.forEach((item) => {
    const key = normalizeFieldGroupTitle(item.title);
    if (key) groupTitles.add(key);
  });
  Object.keys(groupColumnsBase.value).forEach((key) => {
    const normalized = normalizeFieldGroupTitle(key);
    if (normalized) groupTitles.add(normalized);
  });
  Object.keys(groupColumnsDraft).forEach((key) => {
    const normalized = normalizeFieldGroupTitle(key);
    if (normalized) groupTitles.add(normalized);
  });
  formLayoutColumnsDraft.value = columns;
  groupTitles.forEach((key) => {
    const baseColumns = groupColumnsBase.value[key] || previousColumns;
    const draftColumns = groupColumnsDraft[key] || baseColumns;
    if (draftColumns !== previousColumns) return;
    groupColumnsDraft[key] = columns;
    const baseVisible = Object.prototype.hasOwnProperty.call(groupVisibilityBase.value, key)
      ? groupVisibilityBase.value[key] !== false
      : true;
    const draftVisible = Object.prototype.hasOwnProperty.call(groupVisibilityDraft, key)
      ? groupVisibilityDraft[key] !== false
      : baseVisible;
    if (columns === baseColumns && draftVisible === baseVisible) {
      delete groupLayoutDirtyKeys[key];
    } else {
      groupLayoutDirtyKeys[key] = true;
    }
  });
  formLayoutDirty.value = columns !== formLayoutColumnsBase.value;
  formConfigAuditResult.value = null;
  appendFormConfigOperation('调整页面列数', `页面调整为 ${columns} 栏`);
}

function onSelectedFormSettingsGroupVisibilityChange(value: string) {
  const title = selectedFormSettingsFieldGroupTitle.value;
  const key = normalizeFieldGroupTitle(title);
  if (!key) return;
  const visible = value !== 'hide';
  if (effectiveGroupVisible(key) === visible) return;
  groupVisibilityDraft[key] = visible;
  const baseVisible = Object.prototype.hasOwnProperty.call(groupVisibilityBase.value, key)
    ? groupVisibilityBase.value[key] !== false
    : true;
  if (visible === baseVisible && (groupColumnsDraft[key] || groupColumnsBase.value[key] || formLayoutColumnsBase.value) === (groupColumnsBase.value[key] || formLayoutColumnsBase.value)) {
    delete groupLayoutDirtyKeys[key];
  } else {
    groupLayoutDirtyKeys[key] = true;
  }
  formConfigAuditResult.value = null;
  appendFormConfigOperation(visible ? '显示分组' : '隐藏分组', `${key} 设置为${visible ? '显示' : '隐藏'}`);
}

function onSelectedFormSettingsGroupColumnsChange(event: Event) {
  const title = selectedFormSettingsFieldGroupTitle.value;
  const key = normalizeFieldGroupTitle(title);
  if (!key) return;
  const target = event.target as HTMLSelectElement | null;
  const columns = normalizeLowCodeColumns(target?.value, effectiveGroupColumns(key));
  if (effectiveGroupColumns(key) === columns) return;
  groupColumnsDraft[key] = columns;
  const baseColumns = groupColumnsBase.value[key] || formLayoutColumnsBase.value;
  const baseVisible = Object.prototype.hasOwnProperty.call(groupVisibilityBase.value, key)
    ? groupVisibilityBase.value[key] !== false
    : true;
  const draftVisible = Object.prototype.hasOwnProperty.call(groupVisibilityDraft, key)
    ? groupVisibilityDraft[key] !== false
    : baseVisible;
  if (columns === baseColumns && draftVisible === baseVisible) {
    delete groupLayoutDirtyKeys[key];
  } else {
    groupLayoutDirtyKeys[key] = true;
  }
  formConfigAuditResult.value = null;
  appendFormConfigOperation('调整分组列数', `${key} 调整为 ${columns} 栏`);
}

function onSelectedFormSettingsFieldSizeChange(event: Event) {
  const fieldKey = selectedFormSettingsFieldKey.value;
  if (!fieldKey) return;
  const target = event.target as HTMLSelectElement | null;
  const size = normalizeLowCodeFieldSize(target?.value);
  if (effectiveFieldSize(fieldKey) === size) return;
  fieldSizeDraft[fieldKey] = size;
  if (size === (fieldSizeBase.value[fieldKey] || 'normal')) {
    delete fieldLayoutDirtyKeys[fieldKey];
  } else {
    fieldLayoutDirtyKeys[fieldKey] = true;
  }
  formConfigAuditResult.value = null;
  appendFormConfigOperation('调整字段尺寸', `${formDesignFieldLabel(fieldKey)} 设置为${lowCodeFieldSizeLabel(size)}`);
}

async function onSelectedFormSettingsGroupTitleChange(event: Event) {
  const oldTitle = selectedFormSettingsFieldGroupTitle.value;
  const target = event.target as HTMLInputElement | null;
  const newTitle = String(selectedFormSettingsFieldGroupTitleEdit.value || target?.value || '').trim();
  if (!oldTitle || !newTitle || oldTitle === newTitle) {
    selectedFormSettingsFieldGroupTitleEdit.value = oldTitle;
    return;
  }
  await onContractInlineGroupRename({ oldTitle, newTitle });
}

function moveSelectedFormSettingsFieldToOrderTarget() {
  const fieldKey = selectedFormSettingsFieldKey.value;
  const targetFieldKey = selectedFormSettingsOrderTargetKey.value;
  if (!fieldKey || !targetFieldKey || fieldKey === targetFieldKey) return;
  const moved = moveFieldOrderTo(fieldKey, targetFieldKey, selectedFormSettingsOrderPlacement.value, '调整位置');
  if (!moved) return;
  const targetGroup = normalizeFieldGroupTitle(fieldGroupBase.value[targetFieldKey] || fieldGroupDraft[targetFieldKey]);
  if (targetGroup) {
    fieldGroupDraft[fieldKey] = targetGroup;
    fieldMoveTargetDraft[fieldKey] = targetFieldKey;
    selectedFormSettingsFieldGroupTitleDraft.value = targetGroup;
    selectedFormSettingsFieldGroupTitleEdit.value = targetGroup;
  }
  selectedFormSettingsFieldKey.value = fieldKey;
  selectedFormSettingsFieldLabel.value = formDesignFieldLabel(fieldKey);
}

function onSelectedFormSettingsFieldVisibilityChange(value: string) {
  const fieldKey = selectedFormSettingsFieldKey.value;
  if (!fieldKey) return;
  onFieldVisibilityDraftChange(fieldKey, value);
}

async function onSelectedFormSettingsFieldLabelChange(event: Event) {
  const fieldKey = selectedFormSettingsFieldKey.value;
  const target = event.target as HTMLInputElement | null;
  const label = String(target?.value || '').trim();
  if (!fieldKey || !label || label === selectedFormSettingsFieldRow.value?.label) return;
  selectedFormSettingsFieldLabel.value = label;
  await setInlineFieldPolicy(fieldKey, { label });
}

function hideSuggestedInternalFields() {
  const rows = suggestedHiddenFieldRows.value;
  if (!rows.length) return;
  rows.forEach((row) => {
    fieldVisibilityDraft[row.fieldKey] = false;
    fieldVisibilityDirtyKeys[row.fieldKey] = true;
  });
  fieldVisibilityDirty.value = true;
  formConfigAuditResult.value = null;
  appendFormConfigOperation('批量隐藏字段', `隐藏 ${rows.length} 个系统字段`);
  contractModeFeedback.value = `已标记隐藏 ${rows.length} 个系统字段，保存后生效`;
}

function contractInlineFieldOrderIndex(field: FormSectionFieldSchema) {
  const fieldKey = String(field.name || '').trim();
  if (!fieldKey) return -1;
  return fieldOrderDraft.value.indexOf(fieldKey);
}

function onContractInlineFieldOrderMove(payload: { field: FormSectionFieldSchema; delta: number }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  moveFieldOrder(fieldKey, payload.delta);
}

function onContractInlineFieldOrderDragStart(payload: { field: FormSectionFieldSchema; event: DragEvent }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  rememberFormConfigFieldLabel(fieldKey, payload.field.label);
  const fieldLabel = String(payload.field.label || '').trim();
  draggingFieldLabel.value = fieldLabel && fieldLabel !== fieldKey ? fieldLabel : formDesignFieldLabel(fieldKey);
  onFieldOrderDragStart(fieldKey, payload.event);
}

function onContractInlineFieldOrderDragOver(payload: { field: FormSectionFieldSchema; groupTitle?: string; placement?: 'before' | 'after' | '' }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  rememberFormConfigFieldLabel(fieldKey, payload.field.label);
  onFieldOrderDragOver(fieldKey, payload.placement);
}

function onContractInlineFieldOrderDragLeave(payload: { field: FormSectionFieldSchema; groupTitle?: string }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  onFieldOrderDragLeave(fieldKey);
}

function onContractInlineFieldOrderDrop(payload: { field: FormSectionFieldSchema; groupTitle?: string; placement?: 'before' | 'after' | '' }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  rememberFormConfigFieldLabel(fieldKey, payload.field.label);
  onFieldOrderDrop(fieldKey, payload.groupTitle, payload.placement);
}

function onContractInlineFieldOrderGroupDrop(payload: { groupTitle: string; groupIndex?: number }) {
  onFieldOrderGroupDrop(payload.groupTitle);
}

function onContractInlineFieldOrderDragEnd() {
  onFieldOrderDragEnd();
}

function lowCodeApplyBaseParams() {
  const configAction = contractV2ActionRules().find((rule) => ruleKey(rule) === BUSINESS_CONFIG_ACTION_KEYS.currentFormFieldOrderSave);
  const target = parseMaybeJsonRecord(configAction?.target);
  return normalizeLowCodeApplyParams({
    action_id: Number(actionId.value || route.query.action_id || 0) || 0,
    view_id: Number(routeQueryText('view_id') || routeQueryText('viewId') || 0) || 0,
    view_type: 'form',
    ...parseMaybeJsonRecord(target.params),
    model: String(model.value || ''),
  });
}

function contractFieldSequence(fieldKey: string, fallback = 100) {
  const index = fieldOrderDraft.value.indexOf(fieldKey);
  return index >= 0 ? (index + 1) * 10 : fallback;
}

async function setInlineFieldPolicy(fieldKey: string, params: Record<string, unknown>) {
  const base = lowCodeApplyBaseParams();
  if (!fieldKey || busy.value) return;
  const label = String(params.label || '').trim();
  const groupTitle = normalizeFieldGroupTitle(params.group_title);
  busyKind.value = 'action';
  try {
    await intentRequest({
      intent: FORM_FIELD_CONFIG_INTENTS.policySet,
      params: {
        ...base,
        field_name: fieldKey,
        sequence: contractFieldSequence(fieldKey),
        ...params,
      },
      context: { view: 'form' },
    });
    if (label) {
      appendFormConfigOperation('修改字段名称', `${formDesignFieldLabel(fieldKey)} 改为 ${label}`, 'done');
    }
    if (groupTitle) {
      appendFormConfigOperation('移动分组', `${label || formDesignFieldLabel(fieldKey)} 移动到 ${groupTitle}`, 'done');
    }
    contractModeFeedback.value = '字段配置已更新';
    await reload();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '字段显示规则更新失败';
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

async function onContractInlineFieldLabelChange(payload: { field: FormSectionFieldSchema; label: string }) {
  const fieldKey = String(payload.field.name || '').trim();
  const label = String(payload.label || '').trim();
  if (!fieldKey || !label) return;
  await setInlineFieldPolicy(fieldKey, { label });
}

function fieldsInNativeGroup(groupTitle: string) {
  const out = new Map<string, string>();
  const targetTitle = String(groupTitle || '').trim();
  const walk = (nodes: NativeFormLayoutNode[], activeGroup = '') => {
    nodes.forEach((node) => {
      const type = String(node?.type || (node as { containerType?: string })?.containerType || '').trim().toLowerCase();
      const title = String(node?.string || node?.label || '').trim();
      const nextGroup = title && ['group', 'page'].includes(type) ? title : activeGroup;
      const name = String(node?.name || '').trim();
      if (type === 'field' && name && nextGroup === targetTitle) {
        const descriptor = contract.value?.fields?.[name];
        out.set(name, nativeFieldLabel(node, descriptor));
      }
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeFormLayoutNode[], nextGroup);
      });
    });
  };
  walk(nativeFormLayoutNodes.value);
  return Array.from(out.entries()).map(([fieldKey, label]) => ({ fieldKey, label }));
}

function fieldsInConfiguredGroup(groupTitle: string) {
  const targetTitle = normalizeFieldGroupTitle(groupTitle);
  if (!targetTitle) return [];
  const rows = currentFormOrderedFieldKeys.value
    .filter((fieldKey) => fieldGroupTitleMatches(effectiveFieldGroupTitleForDraft(fieldKey), targetTitle))
    .map((fieldKey) => ({ fieldKey, label: formDesignFieldLabel(fieldKey) }));
  return rows.length ? rows : fieldsInNativeGroup(targetTitle);
}

async function onContractInlineGroupRename(payload: { oldTitle: string; newTitle: string }) {
  const oldTitle = String(payload.oldTitle || '').trim();
  const newTitle = String(payload.newTitle || '').trim();
  if (!oldTitle || !newTitle || oldTitle === newTitle || busy.value) return;
  const fields = fieldsInConfiguredGroup(oldTitle);
  if (!fields.length) return;
  fields.forEach((row) => {
    fieldGroupDraft[row.fieldKey] = newTitle;
  });
  selectedFormSettingsFieldGroupTitleDraft.value = newTitle;
  selectedFormSettingsFieldGroupTitleEdit.value = newTitle;
  formConfigAuditResult.value = null;
  appendFormConfigOperation('修改分组名称', `${oldTitle} 改为 ${newTitle}`);
  contractModeFeedback.value = '分组名称已调整，保存表单设置后生效';
}

function openInlineCustomFieldCreate(groupTitle: string, afterFieldKey = '') {
  lowCodeFieldCreateDialog.open = true;
  lowCodeFieldCreateDialog.afterFieldKey = afterFieldKey;
  lowCodeFieldCreateDialog.groupTitle = String(groupTitle || '').trim() || '业务配置字段';
  lowCodeFieldCreateDialog.sequence = contractFieldSequence(afterFieldKey, fieldOrderDraft.value.length ? (fieldOrderDraft.value.length + 1) * 10 : 100) + 5;
  lowCodeFieldCreateDialog.label = '';
  lowCodeFieldCreateDialog.ttype = 'char';
  void nextTick(() => lowCodeFieldCreateLabelRef.value?.focus());
}

function onContractInlineFieldAddAfter(payload: { field: FormSectionFieldSchema; groupTitle: string }) {
  openInlineCustomFieldCreate(payload.groupTitle || '业务配置字段', String(payload.field.name || '').trim());
}

function onContractInlineGroupAddField(payload: { groupTitle: string }) {
  openInlineCustomFieldCreate(payload.groupTitle || '业务配置字段');
}

function closeInlineCustomFieldCreate() {
  lowCodeFieldCreateDialog.open = false;
}

async function submitInlineCustomFieldCreate() {
  const label = String(lowCodeFieldCreateDialog.label || '').trim();
  if (!label || busy.value) return;
  busyKind.value = 'action';
  try {
    await intentRequest({
      intent: FORM_FIELD_CONFIG_INTENTS.customFieldCreate,
      params: {
        ...lowCodeApplyBaseParams(),
        label,
        ttype: lowCodeFieldCreateDialog.ttype || 'char',
        group_title: lowCodeFieldCreateDialog.groupTitle || '业务配置字段',
        sequence: lowCodeFieldCreateDialog.sequence || 100,
      },
      context: { view: 'form' },
    });
    contractModeFeedback.value = '字段已添加';
    appendFormConfigOperation('新增字段', `${label} 添加到 ${lowCodeFieldCreateDialog.groupTitle || '业务配置字段'}`, 'done');
    closeInlineCustomFieldCreate();
    await reload();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '自定义字段创建失败';
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

function onFieldOrderDragStart(fieldKey: string, event?: DragEvent) {
  if (!isContractFieldOrderEditable.value) return;
  draggingFieldKey.value = fieldKey;
  draggingFieldLabel.value = draggingFieldLabel.value || formDesignFieldLabel(fieldKey);
  dropTargetFieldKey.value = '';
  dropTargetPlacement.value = 'before';
  if (event?.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', fieldKey);
  }
}

function stopFieldDragAutoScroll() {
  fieldDragAutoScrollDirection.value = 0;
  if (fieldDragAutoScrollFrame) {
    cancelAnimationFrame(fieldDragAutoScrollFrame);
    fieldDragAutoScrollFrame = 0;
  }
}

function runFieldDragAutoScroll() {
  if (!fieldDragAutoScrollDirection.value || !draggingFieldKey.value) {
    stopFieldDragAutoScroll();
    return;
  }
  const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 0;
  const maxScrollTop = typeof document !== 'undefined'
    ? Math.max(
      document.documentElement.scrollHeight,
      document.body?.scrollHeight || 0,
    ) - viewportHeight
    : 0;
  const currentScrollTop = typeof window !== 'undefined' ? window.scrollY : 0;
  const atStart = currentScrollTop <= 0 && fieldDragAutoScrollDirection.value < 0;
  const atEnd = currentScrollTop >= maxScrollTop && fieldDragAutoScrollDirection.value > 0;
  if (atStart || atEnd) {
    stopFieldDragAutoScroll();
    return;
  }
  window.scrollBy({
    top: fieldDragAutoScrollDirection.value * 18,
    behavior: 'auto',
  });
  fieldDragAutoScrollFrame = requestAnimationFrame(runFieldDragAutoScroll);
}

function scheduleFieldDragAutoScroll(direction: number) {
  if (fieldDragAutoScrollDirection.value === direction && fieldDragAutoScrollFrame) return;
  stopFieldDragAutoScroll();
  if (!direction) return;
  fieldDragAutoScrollDirection.value = direction;
  fieldDragAutoScrollFrame = requestAnimationFrame(runFieldDragAutoScroll);
}

function onFieldOrderWindowDragOver(event: DragEvent) {
  if (!isContractFieldOrderEditable.value || !draggingFieldKey.value) return;
  const viewportHeight = window.innerHeight || 0;
  if (!viewportHeight) return;
  const edgeSize = Math.min(132, Math.max(72, Math.round(viewportHeight * 0.16)));
  if (event.clientY <= edgeSize) {
    scheduleFieldDragAutoScroll(-1);
    return;
  }
  if (event.clientY >= viewportHeight - edgeSize) {
    scheduleFieldDragAutoScroll(1);
    return;
  }
  scheduleFieldDragAutoScroll(0);
}

function onFieldOrderWindowDragStop() {
  onFieldOrderDragEnd();
}

function onFieldOrderDragOver(fieldKey: string, placement: 'before' | 'after' | '' = 'before') {
  if (!isContractFieldOrderEditable.value || !draggingFieldKey.value || draggingFieldKey.value === fieldKey) return;
  dropTargetFieldKey.value = fieldKey;
  dropTargetPlacement.value = placement === 'after' ? 'after' : 'before';
}

function onFieldOrderDragLeave(fieldKey: string) {
  if (dropTargetFieldKey.value === fieldKey) {
    dropTargetFieldKey.value = '';
    dropTargetPlacement.value = 'before';
  }
}

function onFieldOrderDrop(targetFieldKey: string, targetGroupTitle = '', requestedPlacement?: 'before' | 'after' | '') {
  if (!isContractFieldOrderEditable.value || !draggingFieldKey.value || draggingFieldKey.value === targetFieldKey) return;
  const sourceFieldKey = draggingFieldKey.value;
  const currentOrder = fieldOrderDraft.value.length ? fieldOrderDraft.value : currentFormOrderedFieldKeys.value;
  const sourceIndex = currentOrder.indexOf(sourceFieldKey);
  const targetIndex = currentOrder.indexOf(targetFieldKey);
  const placement = requestedPlacement || (sourceIndex >= 0 && targetIndex >= 0 && sourceIndex < targetIndex ? 'after' : 'before');
  moveFieldOrderTo(draggingFieldKey.value, targetFieldKey, placement, '拖拽排序');
  const normalizedTargetGroup = normalizeFieldGroupTitle(fieldGroupBase.value[targetFieldKey] || fieldGroupDraft[targetFieldKey] || targetGroupTitle);
  if (normalizedTargetGroup) {
    fieldGroupDraft[sourceFieldKey] = normalizedTargetGroup;
    fieldMoveTargetDraft[sourceFieldKey] = targetFieldKey;
    selectedFormSettingsFieldGroupTitleDraft.value = normalizedTargetGroup;
  }
  selectedFormSettingsFieldKey.value = sourceFieldKey;
  selectedFormSettingsFieldLabel.value = draggingFieldLabel.value || formDesignFieldLabel(sourceFieldKey);
  dropTargetFieldKey.value = '';
  dropTargetPlacement.value = 'before';
}

function fieldGroupTitleForDraft(fieldKey: string) {
  return effectiveFieldGroupTitleForDraft(fieldKey);
}

function onFieldOrderGroupDrop(groupTitle: string) {
  if (!isContractFieldOrderEditable.value || !draggingFieldKey.value) return;
  moveFieldToGroupEnd(draggingFieldKey.value, groupTitle);
  dropTargetFieldKey.value = '';
  dropTargetPlacement.value = 'before';
}

function moveFieldOrderTo(
  sourceFieldKey: string,
  targetFieldKey: string,
  placement: 'before' | 'after' = 'before',
  operationAction = '拖拽排序',
) {
  ensureFieldOrderDraftStartsFromCurrentLayout();
  const draft = [...fieldOrderDraft.value];
  const from = draft.indexOf(sourceFieldKey);
  const to = draft.indexOf(targetFieldKey);
  if (from < 0 || to < 0 || sourceFieldKey === targetFieldKey) return false;
  const [moved] = draft.splice(from, 1);
  const targetIndex = draft.indexOf(targetFieldKey);
  if (targetIndex < 0) return false;
  const insertIndex = placement === 'after' ? targetIndex + 1 : targetIndex;
  draft.splice(insertIndex, 0, moved);
  fieldOrderDraft.value = draft;
  fieldOrderPreviewActive.value = true;
  formConfigAuditResult.value = null;
  appendFormConfigOperation(
    operationAction,
    `${formDesignFieldLabel(sourceFieldKey)} 调整到 ${formDesignFieldLabel(targetFieldKey)} ${placement === 'after' ? '后' : '前'}`,
  );
  return true;
}

function moveFieldOrder(fieldKey: string, delta: number) {
  if (!isContractFieldOrderEditable.value) return;
  ensureFieldOrderDraftStartsFromCurrentLayout();
  const draft = [...fieldOrderDraft.value];
  const from = draft.indexOf(fieldKey);
  const to = from + delta;
  if (from < 0 || to < 0 || to >= draft.length) return;
  const [moved] = draft.splice(from, 1);
  draft.splice(to, 0, moved);
  fieldOrderDraft.value = draft;
  fieldOrderPreviewActive.value = true;
  formConfigAuditResult.value = null;
}

function onFieldOrderDragEnd() {
  draggingFieldKey.value = '';
  draggingFieldLabel.value = '';
  dropTargetFieldKey.value = '';
  dropTargetPlacement.value = 'before';
  stopFieldDragAutoScroll();
}

function resetContractFieldOrder() {
  fieldOrderDraft.value = currentFormDesignFieldKeys.value;
  fieldOrderPreviewActive.value = false;
  Object.keys(fieldGroupDraft).forEach((key) => delete fieldGroupDraft[key]);
  Object.keys(fieldMoveTargetDraft).forEach((key) => delete fieldMoveTargetDraft[key]);
  Object.entries({ ...fieldGroupBase.value, ...fieldGroupSavedBase.value }).forEach(([key, value]) => {
    if (value) fieldGroupDraft[key] = value;
  });
  formLayoutColumnsDraft.value = formLayoutColumnsBase.value;
  Object.keys(groupVisibilityDraft).forEach((key) => delete groupVisibilityDraft[key]);
  Object.entries(groupVisibilityBase.value).forEach(([key, value]) => {
    groupVisibilityDraft[key] = value;
  });
  Object.keys(groupColumnsDraft).forEach((key) => delete groupColumnsDraft[key]);
  Object.entries(groupColumnsBase.value).forEach(([key, value]) => {
    groupColumnsDraft[key] = value;
  });
  Object.keys(fieldSizeDraft).forEach((key) => delete fieldSizeDraft[key]);
  Object.entries(fieldSizeBase.value).forEach(([key, value]) => {
    fieldSizeDraft[key] = value;
  });
  formLayoutDirty.value = false;
  Object.keys(groupLayoutDirtyKeys).forEach((key) => delete groupLayoutDirtyKeys[key]);
  Object.keys(fieldLayoutDirtyKeys).forEach((key) => delete fieldLayoutDirtyKeys[key]);
  formVisibilityDraftFieldKeys.value.forEach((fieldKey) => {
    if (Object.prototype.hasOwnProperty.call(fieldVisibilityBase.value, fieldKey)) {
      fieldVisibilityDraft[fieldKey] = fieldVisibilityBase.value[fieldKey];
      return;
    }
    const row = contractModeBaseFieldRows.value.find((item) => item.fieldKey === fieldKey);
    const selected = row?.actions.find((action) => Boolean(action.checked));
    fieldVisibilityDraft[fieldKey] = selected ? selected.value === 'show' : true;
  });
  fieldVisibilityDirty.value = false;
  Object.keys(fieldVisibilityDirtyKeys).forEach((key) => {
    delete fieldVisibilityDirtyKeys[key];
  });
  formConfigAuditResult.value = null;
  markPendingFormConfigOperations('reverted');
  appendFormConfigOperation('放弃表单调整', '撤销当前页面未保存的表单配置调整', 'done');
  contractModeFeedback.value = '';
}

function routeQueryText(key: string) {
  const value = route.query[key];
  if (Array.isArray(value)) return String(value[0] || '').trim();
  return String(value || '').trim();
}

function lowCodeReturnQuery() {
  const query: Record<string, string> = {};
  ['root_menu_xmlid', 'db', 'menu_id'].forEach((key) => {
    const value = routeQueryText(key);
    if (value) query[key] = value;
  });
  if (model.value) query.model = model.value;
  if (actionId.value) query.action_id = String(actionId.value);
  query[BUSINESS_CONFIG_ROUTE_FLAGS.openPages] = '1';
  const pageLabel = routeQueryText('page_label');
  if (pageLabel) query.page_label = pageLabel;
  const viewId = routeQueryText('view_id');
  if (viewId) query.view_id = viewId;
  const roleKey = routeQueryText('role_key');
  if (roleKey) query.role_key = roleKey;
  return query;
}

function previewLowCodeConfiguredPage() {
  const query: Record<string, string | string[]> = {};
  Object.entries(route.query as Record<string, unknown>).forEach(([key, raw]) => {
    if (['config_mode', 'activity_page_id'].includes(key)) return;
    if (Array.isArray(raw)) {
      const values = raw.map((item) => String(item || '').trim()).filter(Boolean);
      if (values.length) query[key] = values;
      return;
    }
    const value = String(raw || '').trim();
    if (value) query[key] = value;
  });
  query[BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig] = '1';
  query[BUSINESS_CONFIG_ROUTE_FLAGS.openPages] = '1';
  router.push({ path: route.path, query });
}

async function previewCurrentFormConfiguration() {
  if (hasCurrentFormFieldDraftChanges.value) {
    const saved = await saveContractFieldOrder();
    if (!saved) return;
  }
  previewLowCodeConfiguredPage();
}

function returnToBusinessConfigDesigner() {
  router.push({
    path: '/admin/business-config',
    query: lowCodeReturnQuery(),
  });
}

function formConfigSaveOperationSummary(changedVisibility: Record<string, boolean>, changedGroups: Record<string, string>) {
  const parts: string[] = [];
  if (hasFieldOrderChanges.value) parts.push('字段顺序');
  const groupCount = Object.keys(changedGroups).length;
  if (groupCount) parts.push(`${groupCount} 个字段分组`);
  const visibilityCount = Object.keys(changedVisibility).length;
  if (visibilityCount) parts.push(`${visibilityCount} 个字段显示状态`);
  if (hasFormLayoutChanges.value || hasGroupLayoutChanges.value || hasFieldLayoutChanges.value) parts.push('表单布局');
  return parts.length ? `保存并发布：${parts.join('、')}` : '保存并发布表单设置';
}

async function saveContractFieldOrder() {
  if (!hasCurrentFormFieldDraftChanges.value) return true;
  const configAction = contractV2ActionRules().find((rule) => ruleKey(rule) === BUSINESS_CONFIG_ACTION_KEYS.currentFormFieldOrderSave);
  const target = parseMaybeJsonRecord(configAction?.target);
  const baseParams = normalizeLowCodeApplyParams(parseMaybeJsonRecord(target.params));
  const changedVisibility = changedFieldVisibilityDraft();
  const changedGroups = changedFieldGroupDraft();
  const saveOperationSummary = formConfigSaveOperationSummary(changedVisibility, changedGroups);
  const applyParams: Record<string, unknown> = { ...baseParams };
  if (hasFieldOrderChanges.value) {
    applyParams.field_order = [...fieldOrderDraft.value];
  }
  if (Object.keys(changedGroups).length) {
    applyParams.field_groups = changedGroups;
  }
  if (Object.keys(changedVisibility).length) {
    applyParams.field_visibility = changedVisibility;
  }
  const hasFieldApplyParams = 'field_order' in applyParams || 'field_visibility' in applyParams || 'field_groups' in applyParams;
  if (!hasFieldApplyParams && !hasFormLayoutChanges.value && !hasGroupLayoutChanges.value && !hasFieldLayoutChanges.value) {
    fieldVisibilityDirty.value = false;
    contractModeFeedback.value = '';
    return true;
  }
  busyKind.value = 'action';
  try {
    if (hasFieldApplyParams) {
      await intentRequest({
        intent: BUSINESS_CONFIG_INTENTS.lowCodeApply,
        params: applyParams,
        context: { view: 'form' },
      });
    }
    const saveResult = await intentRequest<{
      precheck?: { warnings?: string[]; errors?: string[] }
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractSave,
      params: {
        ...baseParams,
        name: lowCodeScopedContractName(String(model.value || 'unknown'), baseParams),
        model: String(model.value || ''),
        view_type: 'form',
        publish: true,
        contract_json: {
          view_orchestration: buildLowCodeViewOrchestration(),
        },
      },
    });
    const warnings = Array.isArray(saveResult?.precheck?.warnings) ? saveResult.precheck?.warnings || [] : [];
    lowCodePrecheckWarnings.value = warnings.map((item) => String(item || '').trim()).filter(Boolean);
    if (Object.keys(changedVisibility).length) {
      fieldVisibilityBase.value = {
        ...fieldVisibilityBase.value,
        ...changedVisibility,
      };
      Object.keys(changedVisibility).forEach((key) => {
        delete fieldVisibilityDirtyKeys[key];
      });
    }
    if (Object.keys(changedGroups).length) {
      fieldGroupSavedBase.value = {
        ...fieldGroupSavedBase.value,
        ...changedGroups,
      };
      fieldGroupBase.value = {
        ...fieldGroupBase.value,
        ...changedGroups,
      };
    }
    formLayoutColumnsBase.value = formLayoutColumnsDraft.value;
    groupVisibilityBase.value = { ...groupVisibilityDraft };
    groupColumnsBase.value = { ...groupColumnsDraft };
    fieldSizeBase.value = { ...fieldSizeDraft };
    formLayoutDirty.value = false;
    Object.keys(groupLayoutDirtyKeys).forEach((key) => delete groupLayoutDirtyKeys[key]);
    Object.keys(fieldLayoutDirtyKeys).forEach((key) => delete fieldLayoutDirtyKeys[key]);
    fieldVisibilityDirty.value = false;
    lowCodeContractLoaded.value = false;
    formConfigAuditResult.value = null;
    contractModeFeedback.value = '表单设置已保存并发布，刷新页面后按新配置生效';
    markPendingFormConfigOperations('saved');
    appendFormConfigOperation('保存发布', saveOperationSummary, 'done');
    await reload();
    await hydrateLowCodeDraftFromContract();
    return true;
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '表单字段顺序更新失败';
    status.value = 'error';
    return false;
  } finally {
    busyKind.value = null;
  }
}

async function runAction(action: ContractAction) {
  if (!action.enabled) return;
  if (!await confirmActionSafety(action)) return;
  if (action.intent === 'ui.local_mode' || action.intent === 'ui.mode' || action.clientMode) {
    applyClientMode(action.clientMode, true);
    return;
  }
  const actionKey = String(action.key || '').trim().toLowerCase();
  if (actionKey === 'submit_intake' || actionKey === 'save_draft') {
    await saveRecord(action.refreshPolicy);
    return;
  }
  if (actionKey === 'cancel' && !action.methodName) {
    await router.push({
      name: 'workbench',
      query: pickContractNavQuery(route.query as Record<string, unknown>, {
        scene: undefined,
      }),
    });
    return;
  }
  if (action.kind === 'open') {
    if (action.actionId) {
      await router.push({
        name: 'action',
        params: { actionId: String(action.actionId) },
        query: pickContractNavQuery(route.query as Record<string, unknown>, {
          action_id: action.actionId,
          target: action.target || undefined,
          domain_raw: action.domainRaw || undefined,
        }),
      });
      return;
    }
    if (action.url) {
      const navUrl = resolveNavigationUrl(action.url);
      window.open(navUrl, action.target === 'self' ? '_self' : '_blank', 'noopener,noreferrer');
      return;
    }
    errorMessage.value = '打开操作缺少目标页面';
    status.value = 'error';
    return;
  }
  if (action.mutation) {
    const params = await collectActionParams(action);
    if (params === null) return;
    busyKind.value = 'action';
    try {
      await executeSceneMutation({
        mutation: action.mutation,
        actionKey: action.key,
        recordId: recordId.value,
        model: action.targetModel || model.value,
        context: action.context,
        params,
      });
      submissionFeedback.value = {
        kind: 'success',
        message: '操作已完成，页面数据已刷新。',
      };
      await applyProjectionRefreshPolicy(action.refreshPolicy);
      return;
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : '场景操作执行失败';
      status.value = 'error';
      return;
    } finally {
      busyKind.value = null;
    }
  }
  if ((action.kind === 'object' || action.kind === 'server') && action.methodName && recordId.value) {
    if (!await ensureSavedBeforeRecordAction()) return;
    busyKind.value = 'action';
    try {
      const response = await executeButton({
        model: action.targetModel || model.value,
        res_id: recordId.value,
        button: { name: action.methodName, type: action.kind === 'server' ? 'server' : 'object' },
        context: action.context,
        meta: {
          menu_id: Number(route.query.menu_id || 0) || undefined,
          action_id: actionId.value || undefined,
        },
      });
      const result = response?.result;
      if (result?.entry_target) {
        await router.push(actionResponseRouteTarget(buildEntryTargetRouteTarget(result.entry_target, {
          query: actionResponseNavQuery(result),
          actionId: result.action_id,
        }), result) as never);
        if (action.refreshPolicy) {
          await applyProjectionRefreshPolicy(action.refreshPolicy);
        }
        return;
      }
      const nextActionId = toPositiveInt(result?.action_id);
      if (nextActionId) {
        await router.push({
          name: 'action',
          params: { actionId: String(nextActionId) },
          query: actionResponseNavQuery(result, { action_id: nextActionId }),
        });
        if (action.refreshPolicy) {
          await applyProjectionRefreshPolicy(action.refreshPolicy);
        }
        return;
      }
      const refresh = result?.type;
      if (refresh === 'refresh' && !action.refreshPolicy) {
        await reload();
        return;
      }
      if (action.refreshPolicy) {
        await applyProjectionRefreshPolicy(action.refreshPolicy);
      } else {
        await reload();
      }
      return;
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : '操作执行失败';
      status.value = 'error';
    } finally {
      busyKind.value = null;
    }
  }
}

async function runPrimaryFormAction() {
  const footerAction = primaryCreateFooterAction.value;
  if (footerAction) {
    const saved = await saveRecord(footerAction.refreshPolicy);
    if (!saved) return;
    await nextTick();
    const submittedRecordId = typeof saved === 'number' ? saved : recordId.value;
    if (!submittedRecordId) {
      errorMessage.value = '操作失败：请先保存记录后再执行';
      status.value = 'error';
      return;
    }
    await executePrimarySubmitAction({
      ...footerAction,
      enabled: true,
      hint: '',
    }, submittedRecordId);
    return;
  }
  const submitAction = primarySubmitAction.value;
  if (!submitAction) {
    await saveRecord();
    return;
  }
  const saved = await saveRecord(submitAction.refreshPolicy);
  if (!saved) return;
  await nextTick();
  const submittedRecordId = typeof saved === 'number' ? saved : recordId.value;
  if (!submittedRecordId) {
    errorMessage.value = '提交失败：请先保存记录后再提交';
    status.value = 'error';
    return;
  }
  await executePrimarySubmitAction({
    ...submitAction,
    enabled: true,
    hint: '',
  }, submittedRecordId);
}

async function executePrimarySubmitAction(action: ContractAction, resId: number) {
  if (!await confirmActionSafety(action)) return;
  busyKind.value = 'action';
  try {
    const response = await executeButton({
      model: action.targetModel || model.value,
      res_id: resId,
      button: { name: action.methodName, type: action.kind === 'server' ? 'server' : 'object' },
      context: action.context,
      meta: {
        menu_id: Number(route.query.menu_id || 0) || undefined,
        action_id: actionId.value || undefined,
      },
    });
    const result = response?.result;
    if (result?.entry_target) {
      await router.push(actionResponseRouteTarget(buildEntryTargetRouteTarget(result.entry_target, {
        query: actionResponseNavQuery(result),
        actionId: result.action_id,
      }), result) as never);
      return;
    }
    const nextActionId = toPositiveInt(result?.action_id);
    if (nextActionId) {
      await router.push({
        name: 'action',
        params: { actionId: String(nextActionId) },
        query: actionResponseNavQuery(result, { action_id: nextActionId }),
      });
      return;
    }
    submissionFeedback.value = { kind: 'success', message: '提交成功' };
    await applyProjectionRefreshPolicy(action.refreshPolicy || { on_success: ['scene_projection'] });
    await reload();
  } catch (err) {
    const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, '提交失败，请检查填写内容');
    validationErrors.value = [message];
    submissionFeedback.value = { kind: 'error', message: '提交失败，请检查填写内容' };
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

function isTierValidationActionHidden(methodName: string): boolean {
  const method = String(methodName || '').trim();
  const validationStatus = String(formData.validation_status || '').trim();
  if ((method === 'validate_tier' || method === 'reject_tier') && !formData.can_review) {
    return true;
  }
  if (
    (method === 'action_confirm' || method === 'action_submit' || method === 'button_confirm')
    && ['waiting', 'pending', 'validated'].includes(validationStatus)
  ) {
    return true;
  }
  return false;
}

async function applyProjectionRefreshPolicy(policy?: ContractAction['refreshPolicy']) {
  if (!policy || !Array.isArray(policy.on_success) || !policy.on_success.length) {
    return;
  }
  await executeProjectionRefresh({
    policy,
    refreshScene: async () => {
      await reload();
    },
    refreshWorkbench: async () => {
      await session.loadAppInit();
    },
    refreshRoleSurface: async () => {
      await session.loadAppInit();
    },
    recordTrace: ({ intent, writeMode, latencyMs }) => {
      session.recordIntentTrace({ intent, writeMode, latencyMs });
    },
  });
}

async function openFilter(filterKey: string) {
  if (!actionId.value) return;
  const selected = searchFilters.value.find((item) => item.key === filterKey);
  activeFilterKey.value = filterKey;
  await router.push({
    name: 'action',
    params: { actionId: String(actionId.value) },
    query: pickContractNavQuery(route.query as Record<string, unknown>, {
      action_id: actionId.value,
      preset_filter: filterKey,
      domain_raw: selected?.domainRaw || undefined,
      context_raw: selected?.contextRaw || undefined,
    }),
  });
}

async function cancelIntake() {
  if (!isProjectIntakeCreateMode.value) return;
  const target = session.resolveLandingPath('/');
  await router.replace({ path: target, query: resolveWorkspaceContextQuery() });
}

async function returnToProjectIntakeList(createdId: number | string) {
  const queryActionId = Number(route.query.action_id || actionId.value || 0) || 0;
  if (queryActionId > 0) {
    await router.replace({
      path: `/a/${queryActionId}`,
      query: pickContractNavQuery(route.query as Record<string, unknown>, {
        project_id: String(createdId),
        view_mode: 'tree',
      }),
    });
    return true;
  }
  return false;
}

async function saveRecord(refreshPolicy?: ContractAction['refreshPolicy']): Promise<boolean | number> {
  if (!canSave.value || !model.value) return false;
  submissionFeedback.value = null;
  validationErrors.value = [];
  const standardCreateMode = isProjectStandardIntakeMode.value;
  if (standardCreateMode) {
    const draftErrors: string[] = [];
    const projectName = String(formData.name || '').trim();
    const managerId = Number(formData.manager_id || 0);
    if (!projectName) draftErrors.push('请填写项目名称');
    if (!Number.isFinite(managerId) || managerId <= 0) draftErrors.push('请填写项目经理');
    if (draftErrors.length) {
      validationErrors.value = draftErrors;
      submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
      return false;
    }
  }
  const one2manyIssues = one2manyValidation.value.issues;
  if (one2manyIssues.length) {
    showOne2manyErrors.value = true;
    validationErrors.value = one2manyIssues.slice(0, 5);
    submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
    return false;
  }
  showOne2manyErrors.value = false;
  const labels = layoutNodes.value.reduce<Record<string, string>>((acc, node) => {
    if (node.kind === 'field') acc[node.name] = node.label || node.name;
    return acc;
  }, {});
  const scenePrecheckIssues = collectSceneValidationPrecheckErrors(labels);
  if (scenePrecheckIssues.length) {
    validationErrors.value = scenePrecheckIssues;
    submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
    return false;
  }
  const relationCreateIssues = await resolvePendingInlineRelationCreates();
  if (relationCreateIssues.length) {
    validationErrors.value = relationCreateIssues;
    submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
    return false;
  }
  const tagCreateIssues = await resolvePendingMany2manyTagCreates();
  if (tagCreateIssues.length) {
    validationErrors.value = tagCreateIssues;
    submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
    return false;
  }
  const editableMap = collectWritableValues();
  if (!recordId.value) {
    const requiredIssues = collectRequiredFieldIssues(editableMap);
    if (requiredIssues.length) {
      validationErrors.value = requiredIssues;
      submissionFeedback.value = { kind: 'warn', message: '请先补充必填信息，再保存草稿或提交。' };
      return false;
    }
  }
  if (!standardCreateMode) {
    const issues = validateContractFormData({
      contract: contract.value,
      fieldLabels: labels,
      values: editableMap,
    });
    const basePolicyIssues = collectPolicyValidationErrors(contract.value, policyContext.value);
    const submittedPolicyIssues = collectPolicyValidationErrors(contract.value, {
      ...policyContext.value,
      submittedFields: new Set(Object.keys(editableMap)),
    });
    const policyIssues = [...basePolicyIssues, ...submittedPolicyIssues];
    if (policyIssues.length) {
      validationErrors.value = Array.from(new Set(policyIssues)).slice(0, 5);
      submissionFeedback.value = { kind: 'warn', message: '请先补充必填信息，再保存草稿或提交。' };
      return false;
    }
    if (issues.length) {
      validationErrors.value = Array.from(new Set(issues.map((item) => item.message))).slice(0, 5);
      submissionFeedback.value = { kind: 'warn', message: '请先补充必填信息，再保存草稿或提交。' };
      return false;
    }
  }
  busyKind.value = 'save';
  try {
    const values = Object.entries(editableMap).reduce<Record<string, unknown>>((acc, [key, value]) => {
      if (!recordId.value) {
        acc[key] = value;
        return acc;
      }
      const ttype = fieldType(contract.value?.fields?.[key]);
      if (ttype === 'many2many' || ttype === 'one2many') {
        if (Array.isArray(value) && value.length) {
          acc[key] = value;
        }
        return acc;
      }
      if (!dirtyFieldSet.has(key)) {
        return acc;
      }
      if (comparableFieldValue(key, formData[key]) !== comparableFieldValue(key, originalValues.value[key])) {
        acc[key] = value;
      }
      return acc;
    }, {});
    if (recordId.value && !Object.keys(values).length) {
      busyKind.value = null;
      dirtyFieldSet.clear();
      return true;
    }
    if (recordId.value) {
      await writeContractFormRecord({
        model: model.value,
        ids: [recordId.value],
        vals: values,
        ifMatch: recordVersionPolicy() ? recordVersionToken.value : undefined,
      });
      submissionFeedback.value = { kind: 'success', message: formUiLabel('save_success') };
      dirtyFieldSet.clear();
      await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection'] });
      return true;
    }
    const created = await createContractFormRecord({ model: model.value, vals: values, context: formCreateContext() });
    if (created?.id) {
      const attachmentsUploaded = await uploadPendingNativeAttachments(Number(created.id));
      if (!attachmentsUploaded) {
        return false;
      }
      const title = String(contract.value?.head?.title || '').trim();
      submissionFeedback.value = { kind: 'success', message: `${title || '记录'}已创建` };
      clearIntakeAutosave();
      const nextSceneRoute = String(sceneReadyFormSurface.value.nextSceneRoute || '').trim();
      const nextSceneKey = String(sceneReadyFormSurface.value.nextSceneKey || '').trim();
      const resolvedNextRoute = nextSceneRoute || (nextSceneKey ? `/s/${nextSceneKey}` : '');
      if (isProjectQuickIntakeMode.value && model.value === 'project.project') {
        await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection', 'workbench_projection'] });
        if (await returnToProjectIntakeList(created.id)) return;
        const routePath = resolvedNextRoute || '/s/project.management';
        await router.replace({
          path: routePath,
          query: {
            project_id: String(created.id),
            ...resolveWorkspaceContextQuery(),
          },
        });
        return true;
      }
      if (isProjectStandardIntakeMode.value && resolvedNextRoute) {
        await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection', 'workbench_projection'] });
        if (await returnToProjectIntakeList(created.id)) return true;
        await router.replace({
          path: resolvedNextRoute,
          query: {
            project_id: String(created.id),
            ...resolveWorkspaceContextQuery(),
          },
        });
        return true;
      }
      if (isProjectStandardIntakeMode.value && model.value === 'project.project') {
        await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection', 'workbench_projection'] });
        if (await returnToProjectIntakeList(created.id)) return true;
      }
      const createdRoute = router.resolve({
        name: 'model-form',
        params: { model: model.value, id: String(created.id) },
        query: pickContractNavQuery(route.query as Record<string, unknown>),
      });
      window.location.replace(new URL(createdRoute.href, window.location.origin).toString());
      await new Promise<never>(() => {});
    }
  } catch (err) {
    const fallback = recordId.value ? '保存失败，请检查填写内容' : '创建失败，请检查填写内容';
    const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, fallback);
    validationErrors.value = [message];
    submissionFeedback.value = { kind: 'error', message: message && message !== fallback ? message : fallback };
    return false;
  } finally {
    busyKind.value = null;
  }
  return false;
}

async function copyContractJson() {
  if (!contract.value) return;
  const payload = JSON.stringify(
    {
      action_id: actionId.value,
      model: model.value,
      contract: contract.value,
      meta: contractMeta.value || {},
    },
    null,
    2,
  );
  try {
    await navigator.clipboard.writeText(payload);
  } catch {
    // ignore clipboard failure in locked environments
  }
}

function exportContractJson() {
  if (!contract.value) return;
  const payload = JSON.stringify(
    {
      action_id: actionId.value,
      model: model.value,
      contract: contract.value,
      meta: contractMeta.value || {},
    },
    null,
    2,
  );
  const blob = new Blob([payload], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `contract_form_${model.value || 'unknown'}_${actionId.value || 'na'}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

watch(
  () => formRouteIdentity(),
  (identity) => {
    if (!isComponentActive.value) return;
    if (!instanceRouteIdentity.value && identity) instanceRouteIdentity.value = identity;
    if (instanceRouteIdentity.value && identity !== instanceRouteIdentity.value) {
      instanceRouteIdentity.value = identity;
    }
    if (identity && identity === retainedRouteIdentity.value && status.value === 'ok') return;
    void reload();
  },
  { immediate: true },
);

watch(
  () => route.query.config_mode,
  (mode) => {
    applyRouteConfigMode(mode);
  },
  { immediate: true },
);

watch(
  () => ({
    label: currentBusinessCategoryLabel.value,
    code: currentBusinessCategoryCode.value,
  }),
  (state) => {
    if (!isComponentActive.value) return;
    if (!state.label) return;
    const hasRouteLabel = String(route.query.current_business_category_label || route.query.default_business_category_label || '').trim();
    if (hasRouteLabel) return;
    const query: Record<string, string | string[]> = {
      ...Object.fromEntries(
        Object.entries(route.query).map(([key, value]) => [
          key,
          Array.isArray(value)
            ? value.filter((item): item is string => typeof item === 'string')
            : String(value || ''),
        ]),
      ),
      current_business_category_label: state.label,
      default_business_category_label: state.label,
    };
    if (state.code) {
      query.current_business_category_code = String(route.query.current_business_category_code || state.code);
      query.default_business_category_code = String(route.query.default_business_category_code || state.code);
    }
    void router.replace({ query });
  },
);

function projectContextChangedProjectId(event: Event): number {
  const detail = event instanceof CustomEvent && event.detail && typeof event.detail === 'object'
    ? event.detail as Record<string, unknown>
    : {};
  return Number(detail.selected_project_id || session.projectContext?.selected?.id || 0) || 0;
}

function projectContextChangedPreviousProjectId(event: Event): number {
  const detail = event instanceof CustomEvent && event.detail && typeof event.detail === 'object'
    ? event.detail as Record<string, unknown>
    : {};
  return Number(detail.previous_project_id || 0) || 0;
}

function handleProjectContextChanged(event: Event): void {
  if (!isComponentActive.value) return;
  const selectedProjectId = projectContextChangedProjectId(event);
  const previousProjectId = projectContextChangedPreviousProjectId(event);
  if (selectedProjectId > 0 && previousProjectId === selectedProjectId) return;
  if (model.value === 'project.project' && recordId.value === selectedProjectId) return;
  if (model.value === 'project.project' && selectedProjectId > 0) {
    void router.replace({
      name: 'record',
      params: { model: 'project.project', id: String(selectedProjectId) },
      query: resolveWorkspaceContextQuery(),
    });
    return;
  }
  void router.replace(buildCanonicalSceneRouteTarget('projects.list', {
    query: {
      ...resolveWorkspaceContextQuery(),
      ...(selectedProjectId > 0 ? { project_id: String(selectedProjectId) } : {}),
    },
  }));
}

watch(
  () => [
    intakeAutosaveKey.value,
    formData.name,
    formData.manager_id,
    formData.owner_id,
    formData.project_type_id,
    formData.project_category_id,
    formData.location,
    formData.start_date,
    formData.end_date,
  ],
  () => {
    persistIntakeAutosave();
  },
);

watch(
  () => ({
    model: model.value,
    recordId: recordId.value,
    collaborationReady: Boolean(nativeChatterActions.value.length || nativeAttachments.value),
    projectIntake: isProjectIntakeCreateMode.value,
  }),
  (state) => {
    if (!isComponentActive.value) return;
    if (state.projectIntake || !state.model || !state.recordId || !state.collaborationReady) return;
    const key = `${state.model}:${state.recordId}`;
    if (nativeChatterAutoLoadKey.value === key || chatterLoading.value) return;
    nativeChatterAutoLoadKey.value = key;
    void loadNativeChatterTimeline();
  },
  { immediate: true },
);

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener(PROJECT_CONTEXT_CHANGED_EVENT, handleProjectContextChanged);
    window.addEventListener('dragover', onFieldOrderWindowDragOver);
    window.addEventListener('drop', onFieldOrderWindowDragStop);
    window.addEventListener('dragend', onFieldOrderWindowDragStop);
  }
  if (typeof document !== 'undefined') {
    document.addEventListener('keydown', onRelationDialogDocumentKeydown);
  }
  void nextTick(() => ensureFormInitialReload());
});

onActivated(() => {
  isComponentActive.value = true;
  const identity = formRouteIdentity();
  if (identity && identity !== retainedRouteIdentity.value) {
    void reload();
  }
  void nextTick(() => ensureFormInitialReload());
});

onDeactivated(() => {
  isComponentActive.value = false;
});

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener(PROJECT_CONTEXT_CHANGED_EVENT, handleProjectContextChanged);
    window.removeEventListener('dragover', onFieldOrderWindowDragOver);
    window.removeEventListener('drop', onFieldOrderWindowDragStop);
    window.removeEventListener('dragend', onFieldOrderWindowDragStop);
  }
  if (typeof document !== 'undefined') {
    document.removeEventListener('keydown', onRelationDialogDocumentKeydown);
  }
  stopFieldDragAutoScroll();
});
</script>

<style scoped>
.page {
  display: grid;
  gap: 6px;
  min-width: 0;
  padding-bottom: 24px;
}

.page--flow {
  max-width: min(1080px, 100%);
  margin: 0 auto;
  padding: 24px 32px;
  box-sizing: border-box;
}

.header {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-start;
  min-width: 0;
}

.header--flow {
  border-bottom: 1px solid var(--sc-app-border);
  padding-bottom: 12px;
  margin-bottom: 16px;
}

.header-main {
  display: grid;
  gap: 0;
  min-width: 0;
  flex: 1 1 320px;
}

.page-subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.page-status-line {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--sc-semantic-text-muted);
}

.header-main h1 {
  margin: 0;
  font-size: 36px;
  line-height: 1.12;
  overflow-wrap: anywhere;
}

.meta {
  margin: 1px 0;
  color: var(--sc-semantic-text-muted);
  font-size: 12px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.actions:empty {
  display: none;
}

.header-status {
  display: grid;
  gap: 4px;
  margin-left: auto;
  text-align: right;
  min-width: min(240px, 100%);
  padding-top: 3px;
}

.header-status-item {
  margin: 0;
  font-size: 12px;
  color: var(--sc-semantic-text-muted);
  line-height: 1.3;
}

.header-status-item--danger {
  color: var(--sc-app-warning-text);
}

.action-hint {
  width: 100%;
  margin: 0;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
  text-align: right;
}

.card {
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-product-panel-radius);
  padding: 18px 20px 20px;
  background: var(--sc-app-panel);
  max-width: 1360px;
  width: 100%;
  min-width: 0;
  margin: 0 auto;
  box-sizing: border-box;
}

.card--flow {
  max-width: 1280px;
  width: 100%;
  border: 0;
  background: transparent;
  padding: 0;
  box-shadow: none;
}

.block {
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 10px;
  background: var(--sc-app-muted-bg);
  min-width: 0;
}

.block.warn {
  border-color: var(--sc-app-warning-border);
  background: var(--sc-app-warning-bg);
}

.workflow-evidence-block {
  border-color: var(--sc-app-warning-border);
  background: var(--sc-app-warning-bg);
}

.workflow-evidence-list {
  margin: 6px 0 0;
  padding-left: 18px;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
  line-height: 1.55;
}

.workflow-evidence-list__item--block {
  color: var(--sc-app-warning-text);
}

.contract-missing-block {
  border-color: var(--sc-app-danger-border);
  background: var(--sc-app-danger-bg);
}

.contract-missing-summary,
.contract-missing-defaults {
  margin: 4px 0 0;
  color: var(--sc-app-danger-text);
  font-size: 12px;
}

.block h3 {
  margin: 0 0 8px;
  font-size: 12px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
}

.chip-btn {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  cursor: pointer;
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
}

.chip-btn.active {
  border-color: var(--sc-semantic-surface-interactive);
  box-shadow: inset 0 0 0 1px var(--sc-semantic-surface-interactive);
}

.native-chatter-compose {
  margin-top: 10px;
  display: grid;
  gap: 8px;
}

.native-chatter-field {
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.native-collab-selected,
.native-collab-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.native-collab-options {
  margin-top: -2px;
}

.native-chatter-input {
  min-height: 82px;
  resize: vertical;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 13px;
  line-height: 1.45;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
}

.native-chatter-compose-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.native-chatter-message {
  margin-top: 8px;
}

.native-chatter-empty {
  margin: 6px 0 0;
  padding: 8px 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-muted-bg);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.native-chatter-timeline {
  display: grid;
  gap: 6px;
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
}

.native-chatter-entry {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: baseline;
  gap: 8px;
  padding: 7px 8px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel);
  font-size: 12px;
}

.native-chatter-type {
  color: var(--sc-app-success-text);
  font-weight: 600;
  white-space: nowrap;
}

.native-chatter-body {
  min-width: 0;
  color: var(--sc-app-text-primary);
  overflow-wrap: anywhere;
}

.native-chatter-meta {
  color: var(--sc-app-text-secondary);
  white-space: nowrap;
}

.native-chatter-entry-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.native-chatter-entry-action {
  min-height: 26px;
  padding: 3px 8px;
  font-size: 12px;
}

.native-attachment-tools {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.native-attachment-upload {
  position: relative;
  overflow: hidden;
}

.native-attachment-upload input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.native-attachment-download {
  padding: 4px 8px;
  font-size: 12px;
  white-space: nowrap;
}

.native-pending-attachments {
  display: grid;
  gap: 6px;
  width: 100%;
  margin: 2px 0 0;
  padding: 0;
  list-style: none;
}

.native-pending-attachments li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 8px;
  border: 1px solid var(--border-subtle, #d9e2ec);
  border-radius: 6px;
  color: var(--text-secondary, #475569);
  font-size: 12px;
  background: var(--surface-muted, #f8fafc);
}

.native-pending-attachments span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-grid {
  display: grid;
  gap: 16px;
}

.form-grid--designer-workspace {
  grid-template-columns: 240px minmax(0, 1fr) 360px;
  align-items: start;
  gap: var(--sc-product-workspace-gap);
}

.card--flow .form-grid {
  max-width: 100%;
  margin: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.form-flow-guide {
  grid-column: 1 / -1;
  margin: 0;
  padding: 0;
  border: 0;
}

.form-flow-guide-main {
  margin: 0;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.validation-error {
  grid-column: 1 / -1;
  margin: 0;
  color: var(--sc-app-danger-text);
  font-size: 12px;
}

.validation-warn {
  grid-column: 1 / -1;
  margin: 0;
  color: var(--sc-app-warning-text);
  font-size: 12px;
}

.submission-feedback {
  grid-column: 1 / -1;
  margin: 0;
  font-size: 12px;
  border-radius: 8px;
  padding: 8px 10px;
}

.submission-feedback--success {
  color: var(--sc-app-success-text);
  background: var(--sc-app-success-bg);
  border: 1px solid var(--sc-app-success-border);
}

.submission-feedback--warn {
  color: var(--sc-app-warning-text);
  background: var(--sc-app-warning-bg);
  border: 1px solid var(--sc-app-warning-border);
}

.submission-feedback--error {
  color: var(--sc-app-danger-text);
  background: var(--sc-app-danger-bg);
  border: 1px solid var(--sc-app-danger-border);
}

.layout-divider {
  grid-column: 1 / -1;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
  border-bottom: 1px dashed var(--sc-app-border-strong);
  padding-bottom: 4px;
}

.layout-divider.advanced-toggle {
  display: flex;
  justify-content: flex-start;
  border-bottom: 0;
  padding-bottom: 0;
  margin-top: 2px;
}

.native-statusbar {
  grid-column: 1 / -1;
  display: flex;
  align-items: stretch;
  gap: 0;
  width: 100%;
  min-width: 0;
  overflow-x: auto;
  padding: 2px 0;
  background: transparent;
  scrollbar-width: thin;
}

.native-statusbar--header {
  grid-column: auto;
  justify-content: flex-end;
  width: auto;
  max-width: 100%;
  padding: 0;
}

.contract-form-native-shell :deep(.template-page-header) {
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 12px 14px;
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-product-panel-radius);
  background: var(--sc-app-panel);
  box-shadow: var(--sc-app-shadow);
}

.contract-form-native-shell :deep(.template-page-header--title-hidden:not(:has(.template-page-header-status > *))) {
  justify-content: flex-end;
  width: 100%;
  max-width: none;
  margin-bottom: 10px;
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}

.contract-form-native-shell :deep(.template-page-header-main) {
  min-width: 220px;
  max-width: 360px;
}

.contract-form-native-shell :deep(.template-page-header-main h1) {
  color: var(--sc-app-text-primary);
  font-size: 21px;
  font-weight: 700;
  line-height: 1.2;
}

.contract-form-native-shell :deep(.template-page-header-status) {
  flex: 1 1 auto;
  min-width: 0;
  margin-left: 0;
  padding-top: 0;
}

.contract-form-native-shell :deep(.template-page-header-actions) {
  flex: 0 0 auto;
  gap: 6px;
  align-items: center;
  padding: 3px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel-muted);
}

.contract-header-action-label {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 7px;
  color: var(--sc-app-text-secondary);
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.contract-form-native-shell :deep(.template-page-header-actions .sc-btn) {
  min-height: 30px;
  padding: 5px 11px;
  font-weight: 600;
}

.contract-form-native-shell :deep(.template-page-header-actions .sc-btn-primary) {
  min-width: 76px;
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.16);
}

.contract-form-native-shell :deep(.template-page-header-actions .contract-header-config-action) {
  font-weight: 500;
  opacity: 0.78;
}

.contract-header-action-separator {
  align-self: center;
  width: 1px;
  height: 16px;
  background: var(--sc-app-border);
}

.contract-header-config-action {
  color: var(--sc-semantic-text-muted);
}

.native-statusbar--header .native-statusbar-step {
  min-width: 68px;
  min-height: 30px;
  padding: 0 10px;
}

@media (max-width: 860px) {
  .contract-form-native-shell :deep(.template-page-header) {
    align-items: stretch;
    flex-direction: column;
    flex-wrap: nowrap;
  }

  .contract-form-native-shell :deep(.template-page-header--title-hidden:not(:has(.template-page-header-status > *))) {
    justify-content: flex-start;
  }

  .contract-form-native-shell :deep(.template-page-header-status) {
    flex: 1 1 0;
    width: auto;
    min-width: 0;
    text-align: left;
  }

  .contract-form-native-shell :deep(.template-page-header-actions) {
    flex: 0 0 auto;
    justify-content: flex-start;
    width: auto;
  }
}

.native-form-notice {
  grid-column: 1 / -1;
  margin: 0;
  border-radius: 4px;
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
  padding: 9px 14px;
  font-size: 14px;
  line-height: 1.45;
}

.native-default-section-head {
  grid-column: 1 / -1;
  border-bottom: 1px solid var(--sc-app-border);
  padding: 0 0 6px;
}

.native-default-section-head h3 {
  margin: 0;
  color: var(--sc-app-text-primary);
  font-size: 14px;
  font-weight: 700;
}

.contract-readonly-value {
  display: inline-flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  min-height: 36px;
  padding: 7px 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-input-radius);
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
  font-size: 13px;
  line-height: 1.35;
  overflow-wrap: anywhere;
  box-sizing: border-box;
}

.contract-form-native-shell :deep(.native-form-tree) {
  gap: 18px;
}

.contract-form-native-shell :deep(.native-container--sheet) {
  gap: 18px;
}

.contract-form-native-shell :deep(.native-container--group) {
  gap: 14px;
  padding: 14px 14px 16px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: color-mix(in srgb, var(--sc-app-panel) 86%, var(--sc-app-muted-bg));
}

.contract-form-native-shell :deep(.native-container--group > .native-container-head) {
  min-height: 28px;
  margin: -2px 0 0;
  padding-left: 10px;
  border-left: 3px solid var(--sc-semantic-surface-interactive);
}

.contract-form-native-shell :deep(.native-container--group > .native-container-head h3) {
  font-size: 14px;
  font-weight: 700;
}

.contract-form-native-shell :deep(.native-tabs) {
  border-radius: 8px;
  padding: 5px;
  border: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel-muted);
}

.contract-form-native-shell :deep(.native-tab) {
  min-height: 30px;
  padding: 6px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
}

.contract-form-native-shell :deep(.native-tab--active) {
  border-color: var(--sc-app-border);
  background: var(--sc-app-panel);
  box-shadow: 0 1px 2px var(--sc-app-shadow);
}

.contract-mode-actions {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 0 0;
  border-top: 1px solid var(--sc-app-border);
}

.contract-mode-feedback {
  margin: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-mode-prompt,
.contract-form-settings,
.contract-field-governance {
  grid-column: 1 / -1;
  border-top: 1px solid var(--sc-app-border);
}

.contract-form-settings {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
}

.form-grid--designer-workspace .contract-form-settings,
.form-grid--designer-workspace .contract-form-settings-fields,
.form-grid--designer-workspace .contract-form-designer-control-grid {
  display: contents;
}

.contract-form-settings-head {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  min-height: 44px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--sc-app-border);
}

.contract-form-settings-head h4,
.contract-form-settings-head p {
  margin: 0;
}

.contract-form-settings-head h4 {
  color: var(--sc-app-text-primary);
  font-size: 14px;
  font-weight: 700;
}

.contract-form-settings-head p {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  line-height: 1.45;
}

.contract-form-settings-field-count {
  flex: 0 0 auto;
  min-height: 28px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-form-design-strip {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 8px;
}

.contract-form-design-strip > div {
  display: grid;
  gap: 3px;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel-muted);
}

.contract-form-design-strip span {
  color: var(--sc-app-text-secondary);
  font-size: 11px;
}

.contract-form-design-strip strong {
  color: var(--sc-app-text-primary);
  font-size: 12px;
  font-weight: 650;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.contract-form-settings-section-head,
.contract-form-settings-placeholder {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-form-settings-section-head > div {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.contract-form-settings-section-head strong,
.contract-form-settings-placeholder strong {
  color: var(--sc-app-text-primary);
  font-size: 13px;
}

.contract-form-settings-section-head .ghost {
  flex: 0 0 auto;
}

.contract-form-settings-section-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.contract-form-settings-fields {
  display: grid;
  gap: 10px;
}

.contract-form-designer-control-grid {
  display: grid;
  grid-template-columns: minmax(220px, 0.72fr) minmax(320px, 1.28fr);
  align-items: start;
  gap: var(--sc-product-workspace-gap);
}

.contract-form-designer-sidebar {
  display: grid;
  gap: 0;
  align-content: start;
  min-width: 0;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-bg);
  overflow: hidden;
}

.form-grid--designer-workspace .contract-form-designer-sidebar {
  grid-column: 1;
  grid-row: 4 / span 2;
  align-self: start;
}

.contract-form-designer-sidebar-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
  padding: 12px;
  border-bottom: 1px solid var(--sc-app-border);
}

.contract-form-designer-sidebar-head div {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.contract-form-designer-sidebar-head span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-form-designer-sidebar-head strong {
  color: var(--sc-app-text-primary);
  font-size: 14px;
}

.contract-form-designer-sidebar-head em {
  flex: 0 0 auto;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  padding: 3px 8px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-secondary);
  font-size: 11px;
  font-style: normal;
  line-height: 1.4;
  white-space: nowrap;
}

.contract-form-field-search {
  display: grid;
  gap: 8px;
  padding: 10px;
  border-bottom: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
}

.contract-form-field-search label {
  display: grid;
  gap: 5px;
}

.contract-form-field-search label span,
.contract-form-field-search-summary {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-form-field-search input {
  min-width: 0;
  height: 34px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 10px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-primary);
  font: inherit;
}

.contract-form-field-search-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.contract-form-field-search-results {
  display: grid;
  gap: 5px;
  max-height: 228px;
  overflow: auto;
}

.contract-form-field-search-item {
  min-width: 0;
  min-height: 34px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 8px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-primary);
  cursor: pointer;
  font: inherit;
  text-align: left;
}

.contract-form-field-search-item:hover,
.contract-form-field-search-item--active {
  border-color: var(--sc-app-accent);
  background: var(--sc-app-panel-muted);
}

.contract-form-field-search-item span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contract-form-field-search-item em {
  min-width: 0;
  max-width: 92px;
  overflow: hidden;
  color: var(--sc-app-text-secondary);
  font-size: 11px;
  font-style: normal;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contract-form-field-search-empty {
  margin: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-form-field-navigator {
  display: grid;
  gap: 6px;
  align-content: start;
  max-height: calc(100vh - 220px);
  overflow: auto;
  padding: 10px;
  background: transparent;
}

.contract-form-field-navigator header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--sc-app-border);
}

.contract-form-field-navigator strong {
  color: var(--sc-app-text-primary);
  font-size: 13px;
}

.contract-form-field-navigator header span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-form-field-nav-item {
  min-width: 0;
  min-height: 34px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  border: 1px solid transparent;
  border-radius: 6px;
  padding: 0 8px;
  background: transparent;
  color: var(--sc-app-text-secondary);
  cursor: pointer;
  font: inherit;
  text-align: left;
}

.contract-form-field-nav-item:hover {
  border-color: var(--sc-app-border);
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-primary);
}

.contract-form-field-nav-item--active {
  border-color: var(--sc-app-accent);
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-primary);
  box-shadow: inset 3px 0 0 var(--sc-app-accent);
}

.contract-form-field-nav-item span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contract-form-field-nav-item em {
  min-width: 24px;
  min-height: 20px;
  display: inline-grid;
  place-items: center;
  border-radius: 999px;
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
  font-size: 11px;
  font-style: normal;
}

.contract-form-layout-tools {
  display: grid;
  gap: 10px;
  align-content: start;
  padding: 10px;
  border-top: 1px solid var(--sc-app-border);
  background: transparent;
}

.contract-form-layout-tools header {
  display: grid;
  gap: 3px;
}

.contract-form-layout-tools header strong {
  color: var(--sc-app-text-primary);
  font-size: 13px;
}

.contract-form-layout-tools header span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  line-height: 1.35;
}

.contract-form-layout-tools label {
  display: inline-grid;
  gap: 4px;
  min-width: 128px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-form-layout-tools select {
  height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 5px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 0 8px;
}

.contract-form-inspector {
  min-width: 0;
  display: grid;
  gap: 10px;
  align-content: start;
}

.form-grid--designer-workspace .contract-form-inspector {
  grid-column: 3;
  grid-row: 4 / span 2;
  align-self: start;
}

.contract-field-selection-panel {
  display: grid;
  gap: 8px;
}

.contract-field-selection-card,
.contract-field-selection-empty {
  display: grid;
  gap: 12px;
  min-width: 0;
  padding: 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-bg);
}

.contract-field-selection-main,
.contract-field-selection-empty {
  min-width: 0;
}

.contract-field-selection-main {
  display: grid;
  gap: 2px;
}

.contract-field-selection-main span,
.contract-field-selection-main small,
.contract-field-selection-empty span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  line-height: 1.35;
}

.contract-field-selection-main strong,
.contract-field-selection-empty strong {
  color: var(--sc-app-text-primary);
  font-size: 14px;
  overflow-wrap: anywhere;
}

.contract-field-selection-tools {
  display: grid;
  grid-template-columns: 1fr;
  align-items: start;
  gap: 12px;
  min-width: 0;
}

.contract-field-inspector-section {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  min-width: 0;
  padding: 10px 0 0;
  border-top: 1px solid var(--sc-app-border);
}

.contract-field-inspector-section:first-child {
  padding-top: 0;
  border-top: 0;
}

.contract-field-inspector-section header {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.contract-field-inspector-section header strong {
  color: var(--sc-app-text-primary);
  font-size: 12px;
}

.contract-field-label-edit {
  display: grid;
  gap: 4px;
  min-width: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-field-label-edit input {
  width: 100%;
  max-width: 100%;
  height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 5px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 0 8px;
}

.contract-field-group-move {
  display: grid;
  gap: 4px;
  min-width: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-field-group-move select {
  width: 100%;
  min-width: 0;
  max-width: none;
  height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 5px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 0 8px;
}

.contract-field-group-rename {
  display: grid;
  gap: 4px;
  min-width: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-field-group-rename input {
  width: 100%;
  max-width: 100%;
  height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 5px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 0 8px;
}

.contract-field-group-columns,
.contract-field-size-control {
  display: grid;
  gap: 4px;
  min-width: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-field-group-columns select,
.contract-field-size-control select {
  width: 100%;
  min-width: 0;
  max-width: none;
  height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 5px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 0 8px;
}

.contract-field-group-visibility {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 30px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-field-group-visibility label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--sc-app-text-primary);
}

.contract-field-position-move {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  align-items: end;
  gap: 8px;
  min-width: 0;
}

.contract-field-position-move label {
  display: grid;
  gap: 4px;
  min-width: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-field-position-move select {
  width: 100%;
  min-width: 0;
  max-width: none;
  height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 5px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 0 8px;
}

.contract-mode-prompt {
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px 0 0;
}

.contract-mode-prompt-field {
  display: grid;
  gap: 5px;
  min-width: 180px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-mode-prompt-field input,
.contract-mode-prompt-field select {
  height: 34px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  padding: 0 10px;
  font-size: 13px;
}

.contract-field-create-backdrop {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgb(15 23 42 / 32%);
}

.contract-field-create-dialog {
  display: grid;
  gap: 14px;
  width: min(420px, 100%);
  padding: 18px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  box-shadow: 0 18px 44px rgb(15 23 42 / 18%);
}

.contract-field-create-head,
.contract-field-create-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.contract-field-create-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.contract-field-create-close {
  width: 30px;
  height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.contract-field-create-close:hover {
  color: var(--sc-app-text-primary);
}

.contract-field-create-actions {
  justify-content: flex-end;
}

.contract-field-governance {
  display: grid;
  gap: 12px;
  padding: 12px 0 0;
}

.contract-field-governance-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 8px 14px;
  padding: 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-bg);
}

.contract-field-governance-group-head {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--sc-app-border);
}

.contract-field-governance-group-head strong {
  color: var(--sc-app-text-primary);
  font-size: 13px;
}

.contract-field-governance-group-head span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-field-governance-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 44px;
  padding: 6px 8px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel);
  transition: border-color 120ms ease, box-shadow 120ms ease, opacity 120ms ease, transform 120ms ease;
}

.contract-field-governance-row--draggable {
  cursor: grab;
}

.contract-field-governance-row--draggable:active {
  cursor: grabbing;
}

.contract-field-governance-row--dragging {
  opacity: 0.55;
}

.contract-field-governance-row--drop-target {
  border-color: var(--sc-semantic-surface-interactive);
  box-shadow: inset 3px 0 0 var(--sc-semantic-surface-interactive);
}

.contract-field-governance-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.contract-field-governance-handle {
  flex: 0 0 auto;
  min-width: 38px;
  height: 28px;
  padding: 0 6px;
  display: inline-grid;
  place-items: center;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  color: var(--sc-app-text-secondary);
  background: var(--sc-app-bg);
  font-size: 16px;
  line-height: 1;
}

.contract-field-governance-label {
  min-width: 0;
  color: var(--sc-app-text-primary);
  font-size: 13px;
  overflow-wrap: anywhere;
}

.contract-field-governance-actions,
.contract-field-governance-action {
  display: inline-flex;
  align-items: center;
}

.contract-field-governance-actions {
  gap: 8px;
  flex: 0 0 auto;
}

.contract-field-inspector-section .contract-field-governance-actions {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
}

.contract-field-governance-order-tools {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.contract-field-governance-order-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  display: inline-grid;
  place-items: center;
  font-size: 13px;
  line-height: 1;
}

.contract-field-governance-action {
  gap: 4px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.contract-field-governance-action input {
  margin: 0;
}

.contract-form-operation-log {
  display: grid;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-bg);
}

.contract-form-operation-log header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.contract-form-operation-log header > div {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.contract-form-operation-log strong {
  color: var(--sc-app-text-primary);
  font-size: 13px;
}

.contract-form-operation-log header span,
.contract-form-operation-log-empty {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-form-operation-log-list {
  display: grid;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.contract-form-operation-log-list li {
  display: grid;
  grid-template-columns: auto auto auto;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-form-operation-log-list li > span:not(.contract-form-operation-log-status) {
  grid-column: 1 / -1;
  min-width: 0;
  overflow-wrap: anywhere;
}

.contract-form-designer-canvas {
  grid-column: 1 / -1;
  display: grid;
  gap: 0;
  overflow: hidden;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-bg);
  box-shadow: inset 0 0 0 1px rgb(148 163 184 / 6%);
}

.form-grid--designer-workspace .contract-form-designer-canvas {
  grid-column: 2;
  grid-row: 4 / span 2;
  min-width: 0;
  min-height: 520px;
}

.contract-form-canvas-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 48px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
}

.contract-form-canvas-head > div {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.contract-form-canvas-head strong {
  color: var(--sc-app-text-primary);
  font-size: 13px;
}

.contract-form-canvas-head span {
  min-width: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contract-form-canvas-head em {
  flex: 0 0 auto;
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  padding: 0 8px;
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  font-style: normal;
}

.contract-form-canvas-body {
  padding: 14px;
}

.contract-form-operation-log-list time {
  color: var(--sc-semantic-text-muted);
  font-variant-numeric: tabular-nums;
}

.contract-form-operation-log-status {
  display: inline-flex;
  align-items: center;
  min-height: 20px;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  padding: 1px 7px;
  color: var(--sc-app-text-secondary);
  background: var(--sc-app-muted-bg);
  white-space: nowrap;
}

.contract-form-operation-log-status--pending {
  border-color: var(--sc-app-warning-border);
  color: var(--sc-app-warning-text);
  background: var(--sc-app-warning-bg);
}

.contract-form-operation-log-status--saved,
.contract-form-operation-log-status--done {
  border-color: var(--sc-app-success-border);
  color: var(--sc-app-success-text);
  background: var(--sc-app-success-bg);
}

.contract-form-operation-log-status--reverted {
  color: var(--sc-semantic-text-muted);
}

.contract-form-operation-log-empty {
  margin: 0;
}

.contract-field-governance-footer {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 52px;
  padding: 10px 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
}

.form-grid--designer-workspace .contract-field-governance-footer {
  position: sticky;
  bottom: 0;
  z-index: 5;
  box-shadow: 0 -8px 18px rgb(15 23 42 / 8%);
}

.contract-field-governance-dirty {
  margin-right: auto;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-field-governance-audit {
  flex: 1 1 280px;
  min-width: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contract-field-governance-audit--warning {
  color: var(--sc-app-warning-text);
}

.contract-lowcode-warnings {
  grid-column: 1 / -1;
  margin: 8px 0 0;
  padding: 8px 12px;
  border: 1px solid var(--sc-app-warning-border);
  background: var(--sc-app-warning-bg);
  color: var(--sc-app-warning-text);
  border-radius: 6px;
}

.native-statusbar-step {
  position: relative;
  min-width: 124px;
  flex: 1 0 auto;
  border: 0;
  margin-left: -12px;
  background: var(--sc-app-subtle-bg);
  color: var(--sc-app-text-secondary);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
  padding: 10px 22px 10px 30px;
  cursor: pointer;
  clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 50%, calc(100% - 14px) 100%, 0 100%, 14px 50%);
  box-shadow: inset 0 0 0 1px var(--sc-app-border);
  transition: background-color 0.16s ease, color 0.16s ease, transform 0.16s ease;
  white-space: normal;
  overflow-wrap: anywhere;
}

.native-statusbar-step:first-child {
  margin-left: 0;
  padding-left: 18px;
  border-radius: 6px 0 0 6px;
  clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 50%, calc(100% - 14px) 100%, 0 100%);
}

.native-statusbar-step:last-child {
  border-radius: 0 6px 6px 0;
}

.native-statusbar-step:hover:not(:disabled) {
  background: var(--sc-app-hover-bg);
  color: var(--sc-app-text-primary);
}

.native-statusbar-step--done {
  z-index: 1;
  background: var(--sc-app-success-bg);
  color: var(--sc-app-success-text);
}

.native-statusbar-step--active {
  z-index: 2;
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
  box-shadow: inset 0 0 0 1px var(--sc-semantic-surface-interactive), 0 2px 8px var(--sc-app-shadow);
}

.native-statusbar-step:disabled {
  cursor: default;
}

.relation-dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--sc-semantic-backdrop);
}

.relation-dialog {
  width: min(920px, 100%);
  max-height: min(760px, calc(100vh - 48px));
  display: grid;
  grid-template-rows: auto auto auto minmax(0, 1fr) auto;
  gap: 0;
  border-radius: 8px;
  background: var(--sc-app-panel);
  border: 1px solid var(--sc-app-border);
  box-shadow: 0 18px 50px var(--sc-app-shadow);
  overflow: hidden;
}

.relation-dialog-head,
.relation-dialog-search,
.relation-dialog-footer {
  display: flex;
  align-items: center;
  gap: 10px;
}

.relation-dialog-head {
  justify-content: space-between;
  min-height: 50px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
}

.relation-dialog-head h3 {
  margin: 0;
  font-size: 16px;
  color: var(--sc-app-text-primary);
  font-weight: 600;
}

.relation-dialog-close {
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--sc-app-text-secondary);
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.relation-dialog-close:hover:not(:disabled) {
  background: var(--sc-app-hover-bg);
  color: var(--sc-app-text-primary);
}

.relation-dialog-search {
  align-items: stretch;
  flex-wrap: wrap;
  padding: 12px 16px;
  border-bottom: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
}

.relation-dialog-search .input {
  flex: 1 1 auto;
}

.relation-dialog-table-wrap {
  overflow: auto;
  min-height: 160px;
  border: 0;
  border-radius: 0;
}

.relation-dialog-table {
  width: max(100%, 720px);
  min-width: 720px;
  border-collapse: collapse;
  background: var(--sc-app-panel);
  font-size: 13px;
}

.relation-dialog-table th,
.relation-dialog-table td {
  border-bottom: 1px solid var(--sc-app-border);
  padding: 8px 10px;
  text-align: left;
  vertical-align: middle;
  color: var(--sc-app-text-primary);
  white-space: normal;
  overflow-wrap: anywhere;
}

.relation-dialog-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--sc-app-muted-bg);
  color: var(--sc-app-text-secondary);
  font-weight: 600;
}

.relation-dialog-table tbody tr {
  cursor: pointer;
}

.relation-dialog-table tbody tr:hover,
.relation-dialog-row--active {
  background: var(--sc-app-hover-bg);
}

.relation-dialog-select-col {
  width: 34px;
  text-align: center !important;
}

.relation-dialog-empty {
  margin: 12px;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.relation-dialog-footer {
  min-height: 54px;
  padding: 10px 16px;
  border-top: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
}

.relation-dialog-count {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.relation-dialog-footer-spacer {
  flex: 1 1 auto;
}

@media (max-width: 860px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .contract-form-designer-control-grid,
  .contract-field-selection-tools,
  .contract-field-inspector-section,
  .contract-field-position-move {
    grid-template-columns: 1fr;
  }

  .form-grid--designer-workspace,
  .contract-form-designer-control-grid {
    row-gap: var(--sc-product-workspace-stack-gap);
  }

  .form-grid--designer-workspace .contract-form-designer-sidebar,
  .form-grid--designer-workspace .contract-form-inspector,
  .form-grid--designer-workspace .contract-form-designer-canvas {
    grid-column: 1;
    grid-row: auto;
    position: static;
    max-height: none;
    overflow: visible;
  }

  .form-grid--designer-workspace .contract-field-governance-footer {
    position: static;
    box-shadow: none;
  }

  .contract-form-canvas-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .contract-form-settings {
    padding: 10px;
  }

  .page--flow {
    padding: 14px 12px 20px;
  }

  .header-status {
    margin-left: 0;
    text-align: left;
  }

  .native-chatter-entry {
    grid-template-columns: 1fr;
  }

  .relation-dialog-backdrop {
    padding: 12px;
  }

  .relation-dialog-search,
  .relation-dialog-footer {
    align-items: stretch;
    flex-direction: column;
  }
}

.ghost,
.primary {
  border-radius: 6px;
  padding: 8px 10px;
  border: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
  font-weight: 500;
}

.primary {
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
  border-color: var(--sc-semantic-surface-interactive);
}

.ghost {
  color: var(--sc-app-text-secondary);
}
</style>
