/* eslint-disable @typescript-eslint/no-unused-vars, no-extra-boolean-cast, vue/attributes-order */
<template>
  <LayoutShell
    :flow="isProjectIntakeCreateMode"
    :class="{ 'contract-form-native-shell': useNativeFormTree }"
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
    <PageHeaderTemplate :title="pageDisplayTitle" :subtitle="pageDisplaySubtitle || undefined">
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
        <button
          v-for="action in headerActionsVisible"
          :key="`hdr-${action.key}`"
          :class="action.semantic === 'primary_action' ? 'primary' : 'ghost'"
          :disabled="busy || !action.enabled"
          :title="action.hint"
          @click="runAction(action)"
        >
          {{ action.label }}
        </button>
        <button
          v-if="!isProjectIntakeCreateMode"
          class="primary"
          :disabled="isQuickSubmitDisabled"
          @click="() => saveRecord()"
        >
          {{ submitButtonLabel }}
        </button>
        <button
          v-if="showDiscardAction"
          class="ghost"
          :disabled="busy"
          @click="discardChanges"
        >
          {{ formUiLabel('discard') }}
        </button>
        <button v-if="showDebugActionsVisible && !isProjectIntakeCreateMode" class="ghost" :disabled="busy || !contract" @click="copyContractJson">复制契约</button>
        <button v-if="showDebugActionsVisible && !isProjectIntakeCreateMode" class="ghost" :disabled="busy || !contract" @click="exportContractJson">导出契约</button>
        <button v-if="showDebugActionsVisible && !isProjectIntakeCreateMode" class="ghost" :disabled="busy" @click="reload">{{ formUiLabel('reload') }}</button>
      </template>
    </PageHeaderTemplate>

    <StatusPanel v-if="renderErrorMessage" title="页面渲染失败" :message="renderErrorMessage" variant="error" :on-retry="reload" />
    <StatusPanel v-else-if="status === 'loading'" title="正在加载页面..." variant="info" />
    <StatusPanel v-else-if="status === 'error'" title="页面加载失败" :message="errorMessage" variant="error" :on-retry="reload" />

    <section v-else :class="['card', { 'card--flow': isProjectIntakeCreateMode }]">
      <section v-if="warnings.length && !isProjectIntakeCreateMode" class="block warn">
        <h3>提示信息</h3>
        <ul>
          <li v-for="item in warnings" :key="item">{{ item }}</li>
        </ul>
      </section>
      <section v-if="strictContractMissingSummary && !isProjectIntakeCreateMode" class="block contract-missing-block">
        <h3>契约缺口提示</h3>
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

      <section class="form-grid">
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
              <h4>当前表单设置</h4>
              <p>{{ formFieldConfigScope.summary }}</p>
            </div>
            <nav class="contract-form-settings-tabs" aria-label="表单设置范围">
              <button
                v-for="tab in formSettingsTabs"
                :key="tab.key"
                type="button"
                class="contract-form-settings-tab"
                :class="{ 'contract-form-settings-tab--active': formSettingsActiveTab === tab.key }"
                @click="formSettingsActiveTab = tab.key"
              >
                {{ tab.label }}
              </button>
            </nav>
          </header>
          <dl class="contract-form-settings-scope">
            <div>
              <dt>配置范围</dt>
              <dd>{{ formFieldConfigScope.scope }}</dd>
            </div>
            <div>
              <dt>字段来源</dt>
              <dd>{{ formFieldConfigScope.fieldSource }}</dd>
            </div>
            <div>
              <dt>保存位置</dt>
              <dd>{{ formFieldConfigScope.saveTarget }}</dd>
            </div>
            <div>
              <dt>系统标识</dt>
              <dd>{{ formFieldConfigScope.systemKey }}</dd>
            </div>
          </dl>
          <section v-if="formSettingsActiveTab === 'structure'" class="contract-form-settings-placeholder">
            <strong>页面结构</strong>
            <span>{{ formSettingsStructureSummary }}</span>
          </section>
          <section v-else-if="formSettingsActiveTab === 'fields'" class="contract-form-settings-fields">
            <header class="contract-form-settings-section-head">
              <strong>字段</strong>
              <span>在下方表单里点选字段，然后调整这个字段。</span>
            </header>
            <section class="contract-field-selection-panel">
              <div v-if="selectedFormSettingsFieldRow" class="contract-field-selection-card">
                <div class="contract-field-selection-main">
                  <span>已选字段</span>
                  <strong>{{ selectedFormSettingsFieldRow.label }}</strong>
                  <small>{{ selectedFormSettingsFieldGroupTitle }}</small>
                </div>
                <div class="contract-field-selection-tools">
                  <button
                    class="ghost contract-field-selection-order-btn"
                    type="button"
                    :disabled="busy || !canMoveSelectedFormSettingsField(-1)"
                    title="上移"
                    @click="moveSelectedFormSettingsField(-1)"
                  >↑</button>
                  <button
                    class="ghost contract-field-selection-order-btn"
                    type="button"
                    :disabled="busy || !canMoveSelectedFormSettingsField(1)"
                    title="下移"
                    @click="moveSelectedFormSettingsField(1)"
                  >↓</button>
                  <button
                    class="ghost"
                    type="button"
                    :disabled="busy"
                    @click="addFieldAfterSelectedFormSettingsField"
                  >新增字段</button>
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
                </div>
              </div>
              <div v-else class="contract-field-selection-empty">
                <strong>先在表单中选择一个字段</strong>
                <span>被选中的字段会高亮显示，再调整显示、隐藏、顺序或新增字段。</span>
              </div>
            </section>
          </section>
          <section v-else-if="formSettingsActiveTab === 'details'" class="contract-form-settings-placeholder">
            <strong>明细表</strong>
            <span>下一步在这里调整明细表列显示、列顺序和是否允许添加行。</span>
          </section>
          <section v-else class="contract-form-settings-placeholder">
            <strong>按钮</strong>
            <span>下一步在这里调整业务按钮显示、顺序和更多菜单。</span>
          </section>
          <div class="contract-field-governance-footer">
            <span v-if="hasCurrentFormFieldDraftChanges" class="contract-field-governance-dirty">表单设置已调整，保存后生效</span>
            <button class="chip-btn" type="button" :disabled="busy || !hasCurrentFormFieldDraftChanges" @click="saveContractFieldOrder">保存表单设置</button>
            <button class="ghost" type="button" :disabled="busy || !hasCurrentFormFieldDraftChanges" @click="resetContractFieldOrder">重置</button>
          </div>
        </section>
        <NativeFormTreeRenderer
          v-if="useNativeFormTree"
          :nodes="nativeFormLayoutNodes"
          :field-schemas-for-nodes="nativeFieldSchemasForNodes"
          :is-node-visible="isNativeLayoutNodeVisible"
          :button-label-resolver="resolveNativeButtonLabel"
          :native-action-handler="runNativeLayoutAction"
          :relation-adapter="relationFieldAdapter"
          :field-actions="isContractFieldOrderEditable ? undefined : contractFieldActions"
          :field-order-editable="false"
          :field-order-index="contractInlineFieldOrderIndex"
          :field-order-count="fieldOrderDraft.length"
          :field-order-dragging-key="draggingFieldKey"
          :field-order-drop-target-key="dropTargetFieldKey"
          :field-config-editable="false"
          :field-selection-mode="isContractFieldOrderEditable"
          :selected-field-key="selectedFormSettingsFieldKey"
          :columns="2"
          @field-change="onTemplateFieldChange"
          @field-action="onContractFieldAction"
          @field-order-move="onContractInlineFieldOrderMove"
          @field-order-drag-start="onContractInlineFieldOrderDragStart"
          @field-order-drag-over="onContractInlineFieldOrderDragOver"
          @field-order-drag-leave="onContractInlineFieldOrderDragLeave"
          @field-order-drop="onContractInlineFieldOrderDrop"
          @field-order-drag-end="onContractInlineFieldOrderDragEnd"
          @field-label-change="onContractInlineFieldLabelChange"
          @field-add-after="onContractInlineFieldAddAfter"
          @field-select="onFormSettingsFieldSelect"
          @group-rename="onContractInlineGroupRename"
          @group-add-field="onContractInlineGroupAddField"
          @native-action="runNativeLayoutAction"
        >
          <template #readonly="{ field }">
            <FieldValue :value="field.value" :field="field.descriptor" />
          </template>
          <template #chatter>
            <section v-if="(nativeChatterActions.length || nativeAttachments) && !isProjectIntakeCreateMode" class="block native-chatter-block">
              <h3>{{ nativeCollaborationTitle }}</h3>
              <div class="chips">
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
              <section v-if="activeChatterMode" class="native-chatter-compose">
                <template v-if="activeChatterIsActivity">
                  <label class="native-chatter-field">
                    <span>{{ activitySummaryLabel }}</span>
                    <input v-model="activitySummary" class="input" type="text" :disabled="chatterPosting" />
                  </label>
                  <label class="native-chatter-field">
                    <span>{{ activityDeadlineLabel }}</span>
                    <input v-model="activityDeadline" class="input" type="date" :disabled="chatterPosting" />
                  </label>
                  <label class="native-chatter-field">
                    <span>{{ activityNoteLabel }}</span>
                    <textarea v-model="activityNote" class="native-chatter-input" :disabled="chatterPosting" />
                  </label>
                </template>
                <textarea
                  v-else
                  v-model="chatterDraft"
                  class="native-chatter-input"
                  :placeholder="activeChatterPlaceholder"
                  :disabled="chatterPosting"
                />
                <div class="native-chatter-compose-actions">
                  <button class="primary" type="button" :disabled="isNativeChatterSubmitDisabled" @click="sendNativeChatter">
                    {{ chatterPosting ? '发布中...' : activeChatterSubmitLabel }}
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
              <ul v-if="chatterTimeline.length" class="native-chatter-timeline">
                <li v-for="entry in chatterTimeline" :key="entry.key" class="native-chatter-entry">
                  <span class="native-chatter-type">{{ entry.typeLabel }}</span>
                  <span class="native-chatter-body">{{ entry.type === 'activity' ? entry.title : (entry.body || entry.title) }}</span>
                  <span class="native-chatter-meta">{{ entry.meta }}</span>
                  <button
                    v-if="entry.type === 'attachment' && entry.attachment"
                    class="ghost native-attachment-download"
                    type="button"
                    @click="downloadNativeAttachment(entry.attachment)"
                  >
                    {{ nativeAttachmentDownloadLabel }}
                  </button>
                </li>
              </ul>
            </section>
          </template>
        </NativeFormTreeRenderer>
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
              <button type="button" class="contract-field-create-close" :disabled="busy" aria-label="关闭" @click="closeInlineCustomFieldCreate">x</button>
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
        <section v-if="isContractFieldOrderEditable && !useNativeFormTree" class="contract-lowcode-objects">
          <header class="contract-lowcode-objects-head">
            <h4>业务对象配置</h4>
            <div class="contract-lowcode-contract-switch">
              <select v-model="lowCodeSelectedContractName" class="input" @change="switchLowCodeContractByName">
                <option value="">当前草稿</option>
                <option v-for="item in lowCodeContractList" :key="`contract-${item.id}`" :value="item.name">
                  {{ item.name }} (v{{ item.version_no }} · {{ item.status }})
                </option>
              </select>
            </div>
            <button type="button" class="chip-btn" :disabled="busy || !lowCodeSelectedContractName" @click="publishSelectedLowCodeContract">发布契约</button>
            <button type="button" class="ghost" :disabled="busy || !lowCodeSelectedContractName" @click="rollbackSelectedLowCodeContract">回滚版本</button>
            <button type="button" class="ghost" :disabled="busy" @click="addLowCodeObject">新增对象</button>
          </header>
          <div v-for="(obj, objIndex) in lowCodeObjectsDraft" :key="`lc-obj-${objIndex}`" class="contract-lowcode-object">
            <div class="contract-lowcode-object-head">
              <input v-model="obj.name" class="input" placeholder="对象名称" />
              <button type="button" class="ghost" :disabled="busy" @click="removeLowCodeObject(objIndex)">删除对象</button>
              <button type="button" class="ghost" :disabled="busy" @click="addLowCodeField(objIndex)">新增字段</button>
            </div>
            <div v-for="(field, fieldIndex) in obj.fields" :key="`lc-field-${objIndex}-${fieldIndex}`" class="contract-lowcode-field">
              <input v-model="field.name" class="input" placeholder="字段名" />
              <select v-model="field.type" class="input">
                <option value="string">string</option>
                <option value="float">float</option>
                <option value="date">date</option>
                <option value="selection">selection</option>
                <option value="integer">integer</option>
                <option value="boolean">boolean</option>
              </select>
              <label class="contract-lowcode-flag"><input v-model="field.required" type="checkbox" />必填</label>
              <label class="contract-lowcode-flag"><input v-model="field.readonly" type="checkbox" />只读</label>
              <input v-model="field.default" class="input" placeholder="默认值" />
              <input v-if="field.type === 'selection'" v-model="field.options" class="input" placeholder="选项（value:label,逗号分隔）" />
              <button type="button" class="ghost" :disabled="busy" @click="removeLowCodeField(objIndex, fieldIndex)">删除字段</button>
            </div>
          </div>
        </section>
        <section v-if="isContractFieldOrderEditable && !useNativeFormTree" class="contract-lowcode-objects">
          <header class="contract-lowcode-objects-head">
            <h4>布局配置</h4>
            <div class="chips">
              <button type="button" class="ghost" :disabled="busy" @click="addLowCodeLayoutNode('form')">新增 Form</button>
              <button type="button" class="ghost" :disabled="busy" @click="addLowCodeLayoutNode('list')">新增 List</button>
              <button type="button" class="ghost" :disabled="busy" @click="addLowCodeLayoutNode('kanban')">新增 Kanban</button>
            </div>
          </header>
          <div v-for="(node, nodeIndex) in lowCodeLayoutDraft" :key="`lc-layout-${nodeIndex}`" class="contract-lowcode-field">
            <select v-model="node.section" class="input">
              <option value="form">form</option>
              <option value="list">list</option>
              <option value="kanban">kanban</option>
            </select>
            <input v-model="node.object" class="input" placeholder="对象名" />
            <input v-model="node.field" class="input" placeholder="字段名" />
            <button type="button" class="ghost" :disabled="busy" @click="removeLowCodeLayoutNode(nodeIndex)">删除</button>
          </div>
        </section>
        <section v-if="isContractFieldOrderEditable && !useNativeFormTree" class="contract-lowcode-objects">
          <header class="contract-lowcode-objects-head">
            <h4>规则配置</h4>
            <button type="button" class="ghost" :disabled="busy" @click="addLowCodeRule">新增规则</button>
          </header>
          <div v-for="(rule, ruleIndex) in lowCodeRulesDraft" :key="`lc-rule-${ruleIndex}`" class="contract-lowcode-field">
            <input v-model="rule.name" class="input" placeholder="规则名称" />
            <select v-model="rule.trigger" class="input">
              <option value="on_create">on_create</option>
              <option value="on_update">on_update</option>
              <option value="scheduled">scheduled</option>
            </select>
            <input v-model="rule.object" class="input" placeholder="动作对象" />
            <input v-model="rule.field" class="input" placeholder="动作字段" />
            <input v-if="rule.trigger === 'scheduled'" v-model="rule.cron" class="input" placeholder="cron" />
            <button type="button" class="ghost" :disabled="busy" @click="removeLowCodeRule(ruleIndex)">删除</button>
          </div>
        </section>
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
        <div class="chips">
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
        <section v-if="activeChatterMode" class="native-chatter-compose">
          <template v-if="activeChatterIsActivity">
            <label class="native-chatter-field">
              <span>{{ activitySummaryLabel }}</span>
              <input v-model="activitySummary" class="input" type="text" :disabled="chatterPosting" />
            </label>
            <label class="native-chatter-field">
              <span>{{ activityDeadlineLabel }}</span>
              <input v-model="activityDeadline" class="input" type="date" :disabled="chatterPosting" />
            </label>
            <label class="native-chatter-field">
              <span>{{ activityNoteLabel }}</span>
              <textarea v-model="activityNote" class="native-chatter-input" :disabled="chatterPosting" />
            </label>
          </template>
          <textarea
            v-else
            v-model="chatterDraft"
            class="native-chatter-input"
            :placeholder="activeChatterPlaceholder"
            :disabled="chatterPosting"
          />
          <div class="native-chatter-compose-actions">
            <button class="primary" type="button" :disabled="isNativeChatterSubmitDisabled" @click="sendNativeChatter">
              {{ chatterPosting ? '发布中...' : activeChatterSubmitLabel }}
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
        <ul v-if="chatterTimeline.length" class="native-chatter-timeline">
          <li v-for="entry in chatterTimeline" :key="entry.key" class="native-chatter-entry">
            <span class="native-chatter-type">{{ entry.typeLabel }}</span>
            <span class="native-chatter-body">{{ entry.type === 'activity' ? entry.title : (entry.body || entry.title) }}</span>
            <span class="native-chatter-meta">{{ entry.meta }}</span>
            <button
              v-if="entry.type === 'attachment' && entry.attachment"
              class="ghost native-attachment-download"
              type="button"
              @click="downloadNativeAttachment(entry.attachment)"
            >
              {{ nativeAttachmentDownloadLabel }}
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
  </LayoutShell>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onErrorCaptured, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import FieldValue from '../components/FieldValue.vue';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
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
import { intentRequest } from '../api/intents';
import { loadActionContractRaw, loadModelContractRaw } from '../api/contract';
import { ApiError } from '../api/client';
import { executeButton } from '../api/executeButton';
import { fetchChatterTimeline, postChatterMessage, scheduleChatterActivity, type ChatterTimelineEntry } from '../api/chatter';
import { downloadFile, fileToBase64, uploadFile } from '../api/files';
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
import { findActionMeta } from '../app/menu';
import { pickContractNavQuery } from '../app/navigationContext';
import { buildEntryTargetRouteTarget } from '../app/routeQuery';
import { readWorkspaceContext } from '../app/workspaceContext';
import { collectPolicyValidationErrors, evaluateActionPolicy, evaluateFieldPolicy } from '../app/contractPolicies';
import { buildRuntimeFieldStates } from '../app/modifierEngine';
import { buildOne2ManyInlineCommands, buildX2ManyCommands, extractX2ManyIds } from '../app/x2manyCommands';
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
  resolveContractV2GlobalStatus,
  resolveContractV2MainData,
  resolveContractV2SourceContext,
  resolveContractV2ValueSource,
  type ContractV2ButtonStatus,
  type ContractV2NormalizedStore,
} from '../app/contracts/v2';
import { executeSceneMutation } from '../app/sceneMutationRuntime';
import { isCoreSceneStrictMode } from '../app/contractStrictMode';
import {
  collectUnifiedPageContractV2ButtonStatus,
  collectUnifiedPageContractV2FieldContainerStatus,
  collectUnifiedPageContractV2FieldStatus,
  collectUnifiedPageContractV2FieldWidgets,
  resolveUnifiedPageContractV2MainData,
  resolveUnifiedPageContractV2,
  resolveUnifiedPageContractV2GlobalStatus,
  resolveUnifiedPageContractV2SourceContext,
} from '../app/contracts/unifiedPageContractV2';

type UiStatus = 'loading' | 'ok' | 'error';
type BusyKind = 'save' | 'action' | null;
const MANY2ONE_CREATE_OPTION = '__create__';
const MANY2ONE_SEARCH_MORE_OPTION = '__search_more__';
const MANY2ONE_OPEN_RECORD_OPTION = '__open_record__';

type ContractAction = {
  key: string;
  label: string;
  kind: string;
  level: string;
  selection: 'none' | 'single' | 'multi';
  actionId: number | null;
  methodName: string;
  targetModel: string;
  context: Record<string, unknown>;
  domainRaw: string;
  target: string;
  url: string;
  enabled: boolean;
  hint: string;
  intent: string;
  semantic: string;
  sourceWidgetId: string;
  clientMode: string;
  visibleProfiles: Array<'create' | 'edit' | 'readonly'>;
  requiredParams: string[];
  requiresReason: boolean;
  actionSafety?: {
    classification: 'safe' | 'danger';
    requiresConfirm: boolean;
    confirmMessage: string;
    reasonCode: string;
  };
  mutation?: {
    type: string;
    model: string;
    operation: string;
    payload_schema?: Record<string, unknown>;
  };
  refreshPolicy?: {
    on_success: string[];
    on_failure?: string[];
    mode?: string;
    scope?: string;
    debounce_ms?: number;
  };
};

function normalizeActionSafety(value: unknown): ContractAction['actionSafety'] | undefined {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return undefined;
  const row = value as Record<string, unknown>;
  const classificationRaw = String(row.classification || '').trim().toLowerCase();
  const classification = classificationRaw === 'danger' ? 'danger' : classificationRaw === 'safe' ? 'safe' : '';
  if (!classification) return undefined;
  return {
    classification,
    requiresConfirm: row.requires_confirm === true,
    confirmMessage: String(row.confirm_message || '').trim(),
    reasonCode: String(row.reason_code || '').trim(),
  };
}

function normalizeRequiredParams(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => String(item || '').trim())
    .filter(Boolean);
}

function stableContractId(value: unknown, fallback: string) {
  const raw = String(value || fallback || '').trim();
  const normalized = raw
    .split('')
    .map((char) => {
      if (/^[A-Za-z0-9_.:-]$/.test(char)) return char;
      if (char === ' ' || char === '/') return '.';
      return '';
    })
    .join('')
    .replace(/^\.+|\.+$/g, '');
  const safe = normalized || fallback || 'action';
  return /^[A-Za-z]/.test(safe) ? safe : `id.${safe}`;
}

function resolveV2ButtonStatus(
  key: string,
  statusById: Record<string, ContractV2ButtonStatus>,
): ContractV2ButtonStatus | null {
  const stableKey = stableContractId(key, 'action');
  const candidates = [`btn.${stableKey}`, key, stableKey].filter(Boolean);
  for (const candidate of candidates) {
    if (statusById[candidate]) return statusById[candidate];
  }
  return null;
}

function collectActionParams(action: ContractAction): Record<string, unknown> | null {
  const requiredParams = new Set((action.requiredParams || []).map((item) => item.toLowerCase()));
  if (!action.requiresReason && !requiredParams.has('reason')) return {};
  const reason = window.prompt(`${action.label || '操作'}原因`)?.trim() || '';
  if (!reason) {
    errorMessage.value = '请填写操作原因';
    status.value = 'error';
    return null;
  }
  return { reason };
}

type NativeChatterAction = {
  key: string;
  label: string;
  intent: string;
  mode: string;
  payload: Record<string, unknown>;
  enabled: boolean;
  hint: string;
};

type LayoutNode = {
  key: string;
  kind: 'header' | 'sheet' | 'group' | 'notebook' | 'page' | 'field';
  name: string;
  label: string;
  readonly: boolean;
  required: boolean;
  widget?: string;
  widgetSemantics?: Record<string, unknown>;
  descriptor?: FieldDescriptor;
};

type RelationOption = {
  id: number;
  label: string;
  color?: number | null;
};

type RelationSearchColumn = {
  name: string;
  label: string;
};

type RelationSearchRow = {
  id: number;
  label: string;
  values: Record<string, unknown>;
};

type RelationUiLabels = Record<string, string>;

type StatusbarState = {
  value: string | number;
  label: string;
};

type One2ManyInlineRow = {
  key: string;
  id: number | null;
  isNew: boolean;
  removed: boolean;
  dirty: boolean;
  dirtyFields: string[];
  values: Record<string, unknown>;
};

type One2ManyColumn = {
  name: string;
  label: string;
  ttype: string;
  required: boolean;
  readonly?: boolean;
  selection?: Array<[string, string]>;
};

type ContractAccessPolicy = {
  mode: 'allow' | 'degrade' | 'block';
  reasonCode: string;
  message: string;
  blockedFields: Array<{ field: string; model: string; reasonCode: string }>;
  degradedFields: Array<{ field: string; model: string; reasonCode: string }>;
};

type ContractPromptField = {
  name: string;
  label: string;
  required: boolean;
  defaultValue: string;
  options: Array<{ value: string; label: string }>;
};

type ContractFieldGovernanceAction = {
  key: string;
  label: string;
  value: string;
  checked: boolean;
  disabled: boolean;
  title: string;
  raw: Record<string, unknown>;
};

type ContractFieldGovernanceRow = {
  fieldKey: string;
  label: string;
  actions: ContractFieldGovernanceAction[];
};

class ContractAccessPolicyError extends Error {
  reasonCode: string;

  constructor(message: string, reasonCode: string) {
    super(message);
    this.name = 'ContractAccessPolicyError';
    this.reasonCode = reasonCode;
  }
}

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const PROJECT_CONTEXT_CHANGED_EVENT = 'sc:project-context-changed';

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
}

const status = ref<UiStatus>('loading');
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
const contract = ref<ActionContract | null>(null);
const contractMeta = ref<Record<string, unknown> | null>(null);
const v2ContractStore = ref<ContractV2NormalizedStore | null>(null);
const v2ContractDecodeError = ref('');
const v2ShadowStoreReady = computed(() => Boolean(v2ContractStore.value));
const v2ShadowWidgetCount = computed(() => v2ContractStore.value?.widgetsById.size || 0);
const v2ShadowActionCount = computed(() => v2ContractStore.value?.actionsById.size || 0);
const v2ShadowButtonStatusCount = computed(() => v2ContractStore.value?.buttonStatusById.size || 0);
const v2ShadowFieldCodes = computed(() => Array.from(v2ContractStore.value?.widgetsByFieldCode.keys() || []));
const v2ShadowFieldCodeCount = computed(() => v2ShadowFieldCodes.value.length);
const v2ShadowLegacyFieldMissing = computed(() => {
  const legacyFields = contract.value?.fields || {};
  return v2ShadowFieldCodes.value.filter((fieldCode) => !(fieldCode in legacyFields));
});
const v2ShadowLegacyFieldOverlapCount = computed(() => v2ShadowFieldCodeCount.value - v2ShadowLegacyFieldMissing.value.length);
const v2ShadowLegacyFieldMissingPreview = computed(() => v2ShadowLegacyFieldMissing.value.slice(0, 8).join(',') || '-');
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
const advancedExpanded = ref(false);
const relationOptions = ref<Record<string, RelationOption[]>>({});
const relationFieldDescriptors = ref<Record<string, Record<string, FieldDescriptor>>>({});
const relationKeywords = reactive<Record<string, string>>({});
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
const chatterPosting = ref(false);
const chatterLoading = ref(false);
const chatterError = ref('');
const chatterTimeline = ref<ChatterTimelineEntry[]>([]);
const attachmentUploading = ref(false);
const attachmentError = ref('');
let activeReloadToken = 0;

const model = computed(() => String(route.params.model || contract.value?.head?.model || contract.value?.model || ''));
const actionId = computed(() => {
  return resolveActionIdFromContext({
    routeQuery: route.query as Record<string, unknown>,
    currentActionId: session.currentAction?.action_id,
    currentActionModel: session.currentAction?.model,
    model: model.value,
  });
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
    const inline = relationInlineCreate(node.name, descriptor);
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
    const inline = relationInlineCreate(name, descriptor);
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
  if (total <= 0) return '当前契约未提供必填字段约束。';
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
  const title = String(contract.value?.head?.title || '').trim();
  if (title && !isTechnicalViewTitle(title)) return title;
  const recordTitle = String(formData.display_name || formData.name || '').trim();
  if (recordTitle) return recordTitle;
  return '业务表单';
});

const pageDisplayTitle = computed(() => {
  if (isProjectIntakeCreateMode.value) return '创建项目';
  return pageTitle.value;
});

const pageDisplaySubtitle = computed(() => {
  if (isProjectIntakeCreateMode.value) {
    return '填写核心信息即可完成项目立项';
  }
  return '';
});

const intakeCreateButtonLabel = computed(() => {
  if (!isProjectIntakeCreateMode.value) return '创建项目';
  return busy.value && busyKind.value === 'save' ? '创建中…' : '创建项目';
});

const submitButtonLabel = computed(() => {
  if (busy.value && busyKind.value === 'save') {
    return isProjectQuickIntakeMode.value ? '创建中...' : formUiLabel('saving');
  }
  if (isProjectQuickIntakeMode.value && !recordId.value) {
    return '创建并进入项目驾驶舱';
  }
  return formUiLabel('save');
});
const showDiscardAction = computed(() => !isProjectIntakeCreateMode.value && Boolean(recordId.value) && hasChanges.value);

const headerActionsVisible = computed(() => {
  if (isProjectIntakeCreateMode.value) return [];
  if (useNativeFormTree.value) {
    return headerActions.value.filter((action) => action.sourceWidgetId === 'page.header');
  }
  return headerActions.value;
});

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

const contractPromptFields = computed(() => (contractPromptRule.value ? rulePromptFields(contractPromptRule.value) : []));

const activeContractModeActions = computed(() => {
  const mode = activeContractMode.value;
  if (!mode) return [];
  const source = `mode.${mode}`;
  return contractV2ActionRules()
    .filter((rule) => {
      if (ruleKey(rule) === 'current_form_field_order_save') return false;
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
const draggingFieldKey = ref('');
const dropTargetFieldKey = ref('');
const selectedFormSettingsFieldKey = ref('');
const selectedFormSettingsFieldGroupTitleDraft = ref('');
const isContractFieldOrderEditable = computed(() => (
  activeContractMode.value === 'form_field_configuration'
  || activeContractMode.value === 'business_config_lowcode'
));
const fieldVisibilityBase = ref<Record<string, boolean>>({});
const fieldVisibilityDirty = ref(false);
const fieldVisibilityDraft = reactive<Record<string, boolean>>({});
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
const lowCodePrecheckWarnings = ref<string[]>([]);
const lowCodeContractList = ref<Array<{ id: number; name: string; model: string; status: string; version_no: number }>>([]);
const lowCodeSelectedContractName = ref('');
const lowCodeObjectsDraft = ref<Array<{
  name: string;
  fields: Array<{
    name: string;
    type: string;
    required?: boolean;
    readonly?: boolean;
    default?: string;
    options?: string;
  }>
}>>([]);
const lowCodeLayoutDraft = ref<Array<{ section: 'form' | 'list' | 'kanban'; object: string; field: string }>>([]);
const lowCodeRulesDraft = ref<Array<{ name: string; trigger: 'on_create' | 'on_update' | 'scheduled'; object: string; field: string; cron?: string }>>([]);

function parseSelectionOptions(raw: string): Array<{ value: string; label: string }> {
  return String(raw || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => {
      const parts = item.split(':').map((part) => part.trim()).filter(Boolean);
      if (parts.length >= 2) return { value: parts[0], label: parts.slice(1).join(':') };
      return { value: item, label: item };
    });
}

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
    nextVisibilityBase[row.fieldKey] = visible;
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
    selectedFormSettingsFieldGroupTitleDraft.value = '';
    fieldVisibilityDirty.value = false;
    return;
  }
  formSettingsActiveTab.value = 'fields';
  void loadLowCodeContractList();
  void hydrateLowCodeDraftFromContract();
}, { immediate: true });

const hasFieldOrderChanges = computed(() => {
  if (!fieldOrderPreviewActive.value) return false;
  const rows = contractModeBaseFieldRows.value.map((row) => row.fieldKey);
  if (!rows.length || !fieldOrderDraft.value.length) return false;
  return rows.some((key, index) => fieldOrderDraft.value[index] !== key);
});

const hasFieldVisibilityChanges = computed(() => contractModeBaseFieldRows.value.some((row) => {
  if (!Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, row.fieldKey)) return false;
  if (!Object.prototype.hasOwnProperty.call(fieldVisibilityBase.value, row.fieldKey)) return false;
  return fieldVisibilityDraft[row.fieldKey] !== fieldVisibilityBase.value[row.fieldKey];
}));

const hasCurrentFormFieldDraftChanges = computed(() => (
  hasFieldOrderChanges.value || hasFieldVisibilityChanges.value || fieldVisibilityDirty.value
));

const formFieldSettingsGovernance = computed(() => {
  const root = contract.value && typeof contract.value === 'object'
    ? (contract.value as Record<string, unknown>).governance
    : undefined;
  const governance = root && typeof root === 'object' && !Array.isArray(root)
    ? root as Record<string, unknown>
    : {};
  const settings = governance.current_form_field_settings;
  return settings && typeof settings === 'object' && !Array.isArray(settings)
    ? settings as Record<string, unknown>
    : {};
});

const showCurrentFormFieldConfigScope = computed(() => (
  isContractFieldOrderEditable.value && activeContractModeFieldRows.value.length > 0
));

const formFieldConfigScope = computed(() => {
  const settings = formFieldSettingsGovernance.value;
  const action = Number(settings.action_id || actionId.value || 0) || 0;
  const page = pageDisplayTitle.value || '当前表单';
  const objectLabel = String(settings.model_label || '').trim();
  const modelName = String(settings.model || model.value || '-');
  return {
    scope: `${page}这个页面`,
    fieldSource: '当前页面已有字段和管理员新增字段',
    saveTarget: '当前页面的表单设置',
    systemKey: action > 0 ? `${objectLabel || modelName} / action_id=${action}` : (objectLabel || modelName),
    summary: `本页只调整${page}的字段显示、顺序和新增字段，保存后只影响这个页面。`,
  };
});

const formSettingsTabs = computed(() => [
  { key: 'structure' as const, label: '结构' },
  { key: 'fields' as const, label: `字段 ${activeContractModeFieldRows.value.length}` },
  { key: 'details' as const, label: '明细表' },
  { key: 'actions' as const, label: '按钮' },
]);

const formSettingsStructureSummary = computed(() => {
  const tabCount = nativeNotebookPageCount.value;
  const groupCount = nativeGroupCount.value;
  if (!tabCount && !groupCount) return '当前表单未识别到可配置的页签或分组，先在字段页调整字段。';
  const parts = [];
  if (tabCount) parts.push(`${tabCount} 个页签`);
  if (groupCount) parts.push(`${groupCount} 个分组`);
  return `当前表单包含 ${parts.join('、')}。本次先把结构作为设置入口展示，后续支持直接排序和改名。`;
});

const selectedFormSettingsFieldRow = computed(() => {
  const fieldKey = selectedFormSettingsFieldKey.value;
  if (!fieldKey) return undefined;
  return activeContractModeFieldRows.value.find((row) => row.fieldKey === fieldKey);
});

function fieldStructureTitle(pageTitle: string, groupTitle: string) {
  const page = String(pageTitle || '').trim();
  const group = String(groupTitle || '').trim();
  if (page && group && page !== group) return `${page} / ${group}`;
  return page || group || '主表区域';
}

const nativeFieldStructureGroups = computed<Array<{ key: string; title: string; fieldKeys: string[] }>>(() => {
  const groups = new Map<string, { key: string; title: string; fieldKeys: string[] }>();
  const fieldSeen = new Set<string>();
  const addField = (title: string, fieldKey: string) => {
    const normalizedField = String(fieldKey || '').trim();
    if (!normalizedField || fieldSeen.has(normalizedField)) return;
    fieldSeen.add(normalizedField);
    const groupTitle = title || '主表区域';
    const groupKey = groupTitle;
    if (!groups.has(groupKey)) groups.set(groupKey, { key: groupKey, title: groupTitle, fieldKeys: [] });
    groups.get(groupKey)?.fieldKeys.push(normalizedField);
  };
  const walk = (nodes: NativeFormLayoutNode[], pageTitle = '', groupTitle = '') => {
    nodes.forEach((node) => {
      const type = String(node?.type || (node as { containerType?: string })?.containerType || '').trim().toLowerCase();
      const title = String(node?.string || node?.label || '').trim();
      const nextPage = type === 'page' && title ? title : pageTitle;
      const nextGroup = type === 'group' && title ? title : groupTitle;
      const name = String(node?.name || '').trim();
      if (type === 'field' && name) addField(fieldStructureTitle(nextPage, nextGroup), name);
      (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeFormLayoutNode[], nextPage, nextGroup);
      });
    });
  };
  walk(nativeFormLayoutNodes.value);
  return Array.from(groups.values());
});

const selectedFormSettingsFieldGroupTitle = computed(() => {
  const fieldKey = selectedFormSettingsFieldKey.value;
  if (!fieldKey) return '';
  const nativeGroup = nativeFieldStructureGroups.value.find((group) => group.fieldKeys.includes(fieldKey));
  return nativeGroup?.title || selectedFormSettingsFieldGroupTitleDraft.value || '业务配置字段';
});

async function hydrateLowCodeDraftFromContract() {
  if (!isContractFieldOrderEditable.value || lowCodeContractLoaded.value) return;
  const modelName = String(model.value || '').trim();
  if (!modelName) return;
  try {
    const base = lowCodeApplyBaseParams();
    const scopedName = lowCodeScopedContractName(modelName, base);
    const legacyName = legacyLowCodeContractName(modelName);
    let res = await intentRequest<{
      contract_json?: {
        objects?: Array<{ name?: string; fields?: Array<{ name?: string; visible?: boolean; order?: number }> }>;
      }
    }>({
      intent: 'ui.business_config.contract.get',
      params: { ...base, model: modelName, name: scopedName, view_type: 'form' },
    }).catch(() => null);
    if (!res && scopedName !== legacyName) {
      res = await intentRequest<{
        contract_json?: {
          objects?: Array<{ name?: string; fields?: Array<{ name?: string; visible?: boolean; order?: number }> }>;
        }
      }>({
        intent: 'ui.business_config.contract.get',
        params: { model: modelName, name: legacyName },
      }).catch(() => null);
    }
    if (!res) return;
    const objects = Array.isArray(res?.contract_json?.objects) ? res.contract_json?.objects || [] : [];
    const viewOrchestration = res?.contract_json && typeof res.contract_json === 'object' && !Array.isArray(res.contract_json)
      ? (res.contract_json as { view_orchestration?: Record<string, unknown> }).view_orchestration || {}
      : {};
    const orchestrationViews = viewOrchestration && typeof viewOrchestration === 'object' && !Array.isArray(viewOrchestration)
      ? ((viewOrchestration as Record<string, unknown>).views || {}) as Record<string, unknown>
      : {};
    const matched = objects.find((row) => String(row?.name || '').trim() === modelName) || objects[0];
    const fields = Array.isArray(matched?.fields) ? matched?.fields || [] : [];
    if (fields.length) {
      const orderNames = fields
        .map((row) => ({ name: String(row?.name || '').trim(), order: Number(row?.order || 0) }))
        .filter((row) => row.name)
        .sort((a, b) => a.order - b.order)
        .map((row) => row.name);
      if (orderNames.length) fieldOrderDraft.value = orderNames;
      fields.forEach((row) => {
        const key = String(row?.name || '').trim();
        if (!key) return;
        const visible = row?.visible !== false;
        fieldVisibilityBase.value = { ...fieldVisibilityBase.value, [key]: visible };
        fieldVisibilityDraft[key] = visible;
      });
    }
    if (!fields.length) {
      const formSpec = orchestrationViews.form && typeof orchestrationViews.form === 'object' && !Array.isArray(orchestrationViews.form)
        ? orchestrationViews.form as Record<string, unknown>
        : {};
      const formFields = Array.isArray(formSpec.fields) ? formSpec.fields as Array<Record<string, unknown>> : [];
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
        fieldVisibilityBase.value = { ...fieldVisibilityBase.value, [key]: visible };
        fieldVisibilityDraft[key] = visible;
      });
    }
    lowCodeObjectsDraft.value = objects.map((obj) => ({
      name: String(obj?.name || '').trim(),
      fields: Array.isArray(obj?.fields)
        ? (obj?.fields || []).map((row) => ({
          name: String(row?.name || '').trim(),
          type: String((row as { type?: unknown })?.type || 'string').trim() || 'string',
          required: Boolean((row as { required?: unknown })?.required === true),
          readonly: Boolean((row as { readonly?: unknown })?.readonly === true),
          default: String((row as { default?: unknown })?.default || '').trim(),
          options: Array.isArray((row as { options?: unknown })?.options)
            ? ((row as { options?: unknown[] })?.options || []).map((item) => String(item || '').trim()).filter(Boolean).join(',')
            : '',
        }))
        : [],
    })).filter((obj) => obj.name);
    const layout = res?.contract_json && typeof res.contract_json === 'object' && !Array.isArray(res.contract_json)
      ? (res.contract_json as { layout?: Record<string, unknown> }).layout || {}
      : {};
    const collectLayout = (section: 'form' | 'list' | 'kanban') => (
      Array.isArray((layout as Record<string, unknown>)[section])
        ? ((layout as Record<string, unknown>)[section] as unknown[])
          .filter((node) => node && typeof node === 'object')
          .map((node) => node as Record<string, unknown>)
          .map((node) => ({
            section,
            object: String(node.object || '').trim(),
            field: String(node.field || '').trim(),
          }))
          .filter((node) => node.object && node.field)
        : []
    );
    const legacyLayoutDraft = [...collectLayout('form'), ...collectLayout('list'), ...collectLayout('kanban')];
    lowCodeLayoutDraft.value = legacyLayoutDraft.length ? legacyLayoutDraft : collectLowCodeLayoutFromViewOrchestration(orchestrationViews, modelName);
    const rules = Array.isArray((res?.contract_json as { rules?: unknown[] } | undefined)?.rules)
      ? ((res?.contract_json as { rules?: unknown[] }).rules || [])
      : [];
    lowCodeRulesDraft.value = rules
      .filter((row) => row && typeof row === 'object')
      .map((row) => row as Record<string, unknown>)
      .map((row) => ({
        name: String(row.name || '').trim(),
        trigger: (['on_create', 'on_update', 'scheduled'].includes(String(row.trigger || ''))
          ? String(row.trigger || 'on_update')
          : 'on_update') as 'on_create' | 'on_update' | 'scheduled',
        object: String((row.action as Record<string, unknown> | undefined)?.object || '').trim(),
        field: String((row.action as Record<string, unknown> | undefined)?.field || '').trim(),
        cron: String(row.cron || '').trim(),
      }));
  } catch {
    // ignore low-code contract hydrate failure in form runtime
  } finally {
    lowCodeContractLoaded.value = true;
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
      intent: 'ui.business_config.contract.list',
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
        objects?: Array<{ name?: string; fields?: Array<{ name?: string; visible?: boolean; order?: number; type?: string; required?: boolean; readonly?: boolean; default?: string; options?: unknown[] }> }>;
        layout?: Record<string, unknown>;
        rules?: unknown[];
      }
    }>({
      intent: 'ui.business_config.contract.get',
      params: { ...base, model: modelName, name, view_type: 'form' },
    });
    lowCodeContractLoaded.value = false;
    const json = res?.contract_json;
    if (!json || typeof json !== 'object' || Array.isArray(json)) return;
    const viewOrchestration = (json as { view_orchestration?: Record<string, unknown> }).view_orchestration || {};
    const orchestrationViews = viewOrchestration && typeof viewOrchestration === 'object' && !Array.isArray(viewOrchestration)
      ? ((viewOrchestration as Record<string, unknown>).views || {}) as Record<string, unknown>
      : {};
    const objects = Array.isArray(json.objects) ? json.objects : [];
    lowCodeObjectsDraft.value = objects
      .filter((obj) => obj && typeof obj === 'object')
      .map((obj) => ({
        name: String(obj?.name || '').trim(),
        fields: Array.isArray(obj?.fields)
          ? (obj?.fields || []).map((row) => ({
            name: String(row?.name || '').trim(),
            type: String(row?.type || 'string').trim() || 'string',
            required: Boolean(row?.required === true),
            readonly: Boolean(row?.readonly === true),
            default: String(row?.default || '').trim(),
            options: Array.isArray(row?.options) ? row.options.map((item) => {
              const rec = item as Record<string, unknown>;
              const value = String(rec?.value || '').trim();
              const label = String(rec?.label || '').trim();
              return value && label ? `${value}:${label}` : value || label;
            }).filter(Boolean).join(',') : '',
          }))
          : [],
      }))
      .filter((obj) => obj.name);
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
      intent: 'ui.business_config.contract.publish',
      params: { ...base, name, model: modelName, view_type: 'form' },
    });
    contractModeFeedback.value = '低代码契约已发布';
    await loadLowCodeContractList();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'contract publish failed';
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
      intent: 'ui.business_config.contract.rollback',
      params: { ...base, name, model: modelName, view_type: 'form' },
    });
    contractModeFeedback.value = '低代码契约已回滚到上一版本';
    await loadLowCodeContractList();
    await switchLowCodeContractByName();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'contract rollback failed';
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

function addLowCodeLayoutNode(section: 'form' | 'list' | 'kanban') {
  lowCodeLayoutDraft.value.push({ section, object: '', field: '' });
}
function removeLowCodeLayoutNode(index: number) {
  lowCodeLayoutDraft.value.splice(index, 1);
}
function addLowCodeRule() {
  lowCodeRulesDraft.value.push({ name: `rule_${lowCodeRulesDraft.value.length + 1}`, trigger: 'on_update', object: '', field: '', cron: '' });
}
function removeLowCodeRule(index: number) {
  lowCodeRulesDraft.value.splice(index, 1);
}

function addLowCodeObject() {
  lowCodeObjectsDraft.value.push({ name: `object_${lowCodeObjectsDraft.value.length + 1}`, fields: [] });
}

function removeLowCodeObject(index: number) {
  lowCodeObjectsDraft.value.splice(index, 1);
}

function addLowCodeField(objectIndex: number) {
  const target = lowCodeObjectsDraft.value[objectIndex];
  if (!target) return;
  target.fields.push({ name: `field_${target.fields.length + 1}`, type: 'string', required: false, readonly: false, default: '', options: '' });
}

function removeLowCodeField(objectIndex: number, fieldIndex: number) {
  const target = lowCodeObjectsDraft.value[objectIndex];
  if (!target) return;
  target.fields.splice(fieldIndex, 1);
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

function normalizedLowCodeDefault(field: { type?: string; default?: string }): unknown {
  const raw = String(field.default ?? '').trim();
  if (!raw) return undefined;
  if (field.type === 'integer') {
    const parsed = Number.parseInt(raw, 10);
    return Number.isNaN(parsed) ? raw : parsed;
  }
  if (field.type === 'float') {
    const parsed = Number.parseFloat(raw);
    return Number.isNaN(parsed) ? raw : parsed;
  }
  if (field.type === 'boolean') {
    if (['1', 'true', 'yes', '是'].includes(raw.toLowerCase())) return true;
    if (['0', 'false', 'no', '否'].includes(raw.toLowerCase())) return false;
    return raw;
  }
  return raw;
}

function buildLowCodeViewOrchestration() {
  const availableFields = contract.value?.fields || {};
  const fieldLabel = (name: string) => {
    const descriptor = availableFields[name];
    return String(descriptor?.string || name).trim() || name;
  };
  const sectionFields = (section: 'form' | 'list' | 'kanban') => lowCodeLayoutDraft.value
    .filter((row) => row.section === section)
    .map((row) => String(row.field || '').trim())
    .filter((name) => name && availableFields[name]);
  const formNames = sectionFields('form').length ? sectionFields('form') : fieldOrderDraft.value.filter((name) => availableFields[name]);
  const listNames = sectionFields('list');
  const kanbanNames = sectionFields('kanban');
  const views: Record<string, unknown> = {};
  if (formNames.length) {
    views.form = {
      fields: formNames.map((name, index) => ({
        name,
        label: fieldLabel(name),
        visible: fieldVisibilityDraft[name] !== false,
        sequence: (index + 1) * 10,
      })),
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

function normalizeLowCodeFieldDraft(field: {
  name?: string;
  type?: string;
  readonly?: boolean;
  required?: boolean;
  default?: string;
  options?: string;
}, index: number): Record<string, unknown> {
  const fieldName = String(field.name || '').trim();
  const row: Record<string, unknown> = {
    name: fieldName,
    type: String(field.type || 'string').trim() || 'string',
    readonly: field.readonly === true,
    required: field.required === true,
    visible: fieldVisibilityDraft[fieldName] !== false,
    order: index + 1,
  };
  const defaultValue = normalizedLowCodeDefault(field);
  if (defaultValue !== undefined) row.default = defaultValue;
  if (row.type === 'selection') row.options = parseSelectionOptions(String(field.options || ''));
  return row;
}

function currentFormContractFieldRows(): Array<Record<string, unknown>> {
  const baseByKey = new Map(contractModeBaseFieldRows.value.map((row) => [row.fieldKey, row]));
  const orderedKeys = fieldOrderDraft.value.length
    ? fieldOrderDraft.value
    : contractModeBaseFieldRows.value.map((row) => row.fieldKey);
  return orderedKeys
    .filter((key) => baseByKey.has(key))
    .map((key, index) => ({
      name: key,
      label: baseByKey.get(key)?.label || key,
      type: 'string',
      visible: fieldVisibilityDraft[key] !== false,
      order: index + 1,
    }));
}

function buildLowCodeContractObjects(): Array<Record<string, unknown>> {
  const modelName = String(model.value || '').trim();
  const formFields = currentFormContractFieldRows();
  const objects = lowCodeObjectsDraft.value
    .map((obj) => ({
      name: String(obj.name || '').trim(),
      fields: (obj.fields || [])
        .map((field, index) => normalizeLowCodeFieldDraft(field, index))
        .filter((field) => String(field.name || '').trim()),
    }))
    .filter((obj) => obj.name);
  if (!modelName) return objects;
  const existing = objects.find((obj) => obj.name === modelName);
  if (!existing) {
    objects.unshift({ name: modelName, fields: formFields });
    return objects;
  }
  const formNames = new Set(formFields.map((field) => String(field.name || '').trim()));
  const existingFields = Array.isArray(existing.fields) ? existing.fields : [];
  existing.fields = [
    ...formFields,
    ...existingFields.filter((field) => !formNames.has(String(field.name || '').trim())),
  ];
  return objects;
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

function legacyLowCodeContractName(modelName: string) {
  return `lowcode.${modelName}`;
}

const isQuickSubmitDisabled = computed(() => {
  if (busy.value) return true;
  if (!canSave.value) return true;
  if (isProjectQuickIntakeMode.value) return !quickRequiredReady.value;
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
  return `mode=${mode} · surface=${surface} · view_type=${viewType} · profile=${renderProfile.value} · filters=${filters} · transitions=${transitions} · rights=${rights.value.read ? 'R' : '-'}${rights.value.write ? 'W' : '-'}${rights.value.create ? 'C' : '-'}${rights.value.unlink ? 'D' : '-'}`;
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
const policyContext = computed(() => ({
  profile: renderProfile.value,
  formData: formData as Record<string, unknown>,
  capabilities: runtimeCapabilities.value,
  userGroups: new Set<string>(),
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
  const row = raw && typeof raw === 'object' && !Array.isArray(raw)
    ? (raw as Record<string, unknown>)
    : {};
  const modeRaw = String(row.mode || '').trim().toLowerCase();
  const mode: 'allow' | 'degrade' | 'block' = modeRaw === 'block' || modeRaw === 'degrade' ? modeRaw : 'allow';
  const normalizeRows = (value: unknown) => {
    if (!Array.isArray(value)) return [];
    return value
      .map((item) => {
        if (!item || typeof item !== 'object' || Array.isArray(item)) return null;
        const v = item as Record<string, unknown>;
        return {
          field: String(v.field || '').trim(),
          model: String(v.model || '').trim(),
          reasonCode: String(v.reason_code || '').trim(),
        };
      })
      .filter((item): item is { field: string; model: string; reasonCode: string } => Boolean(item));
  };
  return {
    mode,
    reasonCode: String(row.reason_code || '').trim(),
    message: String(row.message || '').trim(),
    blockedFields: normalizeRows(row.blocked_fields),
    degradedFields: normalizeRows(row.degraded_fields),
  };
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

function fieldType(descriptor?: FieldDescriptor | null) {
  return String(descriptor?.ttype || descriptor?.type || '').trim().toLowerCase();
}

function toDateInputValue(value: unknown) {
  const raw = String(value ?? '').trim();
  if (!raw) return '';
  if (raw.length >= 10) return raw.slice(0, 10);
  return raw;
}

function toDatetimeInputValue(value: unknown) {
  const raw = String(value ?? '').trim();
  if (!raw) return '';
  const normalized = raw.replace(' ', 'T');
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized;
}

function fromDatetimeInputValue(value: unknown) {
  const raw = String(value ?? '').trim();
  if (!raw) return false;
  const normalized = raw.replace('T', ' ');
  return normalized.length === 16 ? `${normalized}:00` : normalized;
}

function normalizeRelationIds(value: unknown): number[] {
  return extractX2ManyIds(value);
}

function relationIds(name: string): number[] {
  return normalizeRelationIds(formData[name]);
}

function cleanRelationDisplayLabel(value: unknown, id: number) {
  const label = String(value || '').trim();
  if (!label || label === 'display_name' || label === 'name') return `#${id}`;
  return label;
}

function relationColorField(descriptor?: FieldDescriptor) {
  const row = descriptor && typeof descriptor === 'object' ? descriptor as Record<string, unknown> : {};
  const options = row.widget_options && typeof row.widget_options === 'object' && !Array.isArray(row.widget_options)
    ? row.widget_options as Record<string, unknown>
    : row.options && typeof row.options === 'object' && !Array.isArray(row.options)
      ? row.options as Record<string, unknown>
      : {};
  const colorField = String(options.color_field || '').trim();
  return colorField || '';
}

function relationReadFields(descriptor?: FieldDescriptor) {
  const fields = new Set(['id', 'name', 'display_name']);
  const colorField = relationColorField(descriptor);
  if (colorField) fields.add(colorField);
  return Array.from(fields);
}

function relationOptionFromRow(row: Record<string, unknown>, descriptor?: FieldDescriptor): RelationOption | null {
  const id = Number(row.id);
  if (!Number.isFinite(id) || id <= 0) return null;
  const label = String(row.display_name || row.name || `#${id}`).trim();
  const colorField = relationColorField(descriptor);
  const colorValue = colorField ? Number(row[colorField]) : NaN;
  return {
    id: Math.trunc(id),
    label: cleanRelationDisplayLabel(label, id),
    ...(Number.isFinite(colorValue) ? { color: Math.trunc(colorValue) } : {}),
  };
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

function parseMany2oneDisplay(value: unknown): RelationOption | null {
  if (Array.isArray(value)) {
    const id = Number(value[0]);
    if (!Number.isFinite(id) || id <= 0) return null;
    const label = cleanRelationDisplayLabel(value[1], id);
    return { id: Math.trunc(id), label };
  }
  if (value && typeof value === 'object') {
    const row = value as Record<string, unknown>;
    const id = Number(row.id);
    if (!Number.isFinite(id) || id <= 0) return null;
    const label = cleanRelationDisplayLabel(row.display_name || row.name, id);
    return { id: Math.trunc(id), label };
  }
  return null;
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
  const byId = new Map<number, RelationOption>();
  for (const item of current) byId.set(item.id, item);
  for (const item of options) byId.set(item.id, item);
  relationOptions.value = {
    ...relationOptions.value,
    [fieldName]: Array.from(byId.values()),
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

function nativeNodeFieldInfo(node?: Record<string, unknown> | NativeFormLayoutNode | null): Record<string, unknown> {
  const row = node as Record<string, unknown> | undefined;
  const fieldInfo = row?.fieldInfo && typeof row.fieldInfo === 'object' && !Array.isArray(row.fieldInfo)
    ? row.fieldInfo as Record<string, unknown>
    : {};
  if (Object.keys(fieldInfo).length) return fieldInfo;
  return row?.field_info && typeof row.field_info === 'object' && !Array.isArray(row.field_info)
    ? row.field_info as Record<string, unknown>
    : {};
}

function nativeFieldSubview(name: string): Record<string, unknown> | null {
  const target = String(name || '').trim();
  if (!target) return null;
  const walk = (nodes: NativeFormLayoutNode[]): Record<string, unknown> | null => {
    for (const node of nodes) {
      const nodeName = String(node?.name || '').trim();
      const nodeType = String(node?.type || '').trim().toLowerCase();
      if (nodeType === 'field' && nodeName === target) {
        const fieldInfo = nativeNodeFieldInfo(node);
        const subview = fieldInfo?.subview;
        if (subview && typeof subview === 'object' && !Array.isArray(subview)) {
          return subview as Record<string, unknown>;
        }
      }
      for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
        const children = node?.[key];
        if (!Array.isArray(children)) continue;
        const found = walk(children as NativeFormLayoutNode[]);
        if (found) return found;
      }
    }
    return null;
  };
  return walk(nativeFormLayoutNodes.value);
}

function subviewColumnCount(subview: unknown): number {
  if (!subview || typeof subview !== 'object' || Array.isArray(subview)) return 0;
  const tree = (subview as Record<string, unknown>).tree;
  if (!tree || typeof tree !== 'object' || Array.isArray(tree)) return 0;
  const columns = (tree as Record<string, unknown>).columns;
  if (!Array.isArray(columns)) return 0;
  return columns.length;
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
  const fieldSubview = subviews && typeof subviews === 'object'
    ? (subviews as Record<string, unknown>)[name]
    : undefined;
  const policies = fieldSubview && typeof fieldSubview === 'object'
    ? (fieldSubview as Record<string, unknown>).policies
    : undefined;
  return policies && typeof policies === 'object'
    ? policies as Record<string, unknown>
    : {};
}

function one2manyCanCreate(name: string) {
  return one2manyPolicies(name).can_create !== false;
}

function one2manyCreateLabel(name: string) {
  const policies = one2manyPolicies(name);
  const labels = policies.ui_labels && typeof policies.ui_labels === 'object' && !Array.isArray(policies.ui_labels)
    ? policies.ui_labels as Record<string, unknown>
    : {};
  return String(labels.add_row || labels.create || '添加行').trim() || '添加行';
}

function one2manyPrimaryColumn(name: string) {
  const cols = one2manyColumns(name);
  return cols.length ? cols[0].name : 'name';
}

function one2manyRowLabel(fieldName: string, row: One2ManyInlineRow) {
  const primary = one2manyPrimaryColumn(fieldName);
  const value = String(row.values?.[primary] ?? row.values?.name ?? '').trim();
  if (value) return value;
  if (row.id) return `#${row.id}`;
  return '未命名';
}

function one2manyRowStateLabel(row: One2ManyInlineRow) {
  if (row.removed) return '待删除';
  if (row.isNew) return '新增';
  if (row.dirty) return '已修改';
  return '未变更';
}

function one2manySummary(name: string) {
  const rows = one2manyFieldRows(name);
  if (!rows.length) return '';
  let created = 0;
  let updated = 0;
  let removed = 0;
  rows.forEach((row) => {
    if (row.removed) {
      removed += 1;
      return;
    }
    if (row.isNew) {
      created += 1;
      return;
    }
    if (row.dirty) updated += 1;
  });
  const parts: string[] = [];
  if (created) parts.push(`新增 ${created}`);
  if (updated) parts.push(`修改 ${updated}`);
  if (removed) parts.push(`删除 ${removed}`);
  return parts.length ? `待提交：${parts.join(' / ')}` : '待提交：无变更';
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

function normalizeOne2manyColumnValue(column: One2ManyColumn, value: unknown) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (ttype === 'boolean') return Boolean(value);
  if (ttype === 'integer') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? Math.trunc(parsed) : false;
  }
  if (ttype === 'float' || ttype === 'monetary') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : false;
  }
  if (ttype === 'date') return toDateInputValue(value) || false;
  if (ttype === 'datetime') return fromDatetimeInputValue(value);
  if (ttype === 'selection') return String(value ?? '').trim() || false;
  return String(value ?? '');
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

function one2manyColumnInputType(column: One2ManyColumn) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (ttype === 'integer' || ttype === 'float' || ttype === 'monetary') return 'number';
  if (ttype === 'date') return 'date';
  if (ttype === 'datetime') return 'datetime-local';
  return 'text';
}

function one2manyColumnDisplayValue(column: One2ManyColumn, value: unknown) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (value === false || value === null || value === undefined) return '';
  if (ttype === 'date') return toDateInputValue(value);
  if (ttype === 'datetime') return toDatetimeInputValue(value);
  return String(value ?? '');
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
  const rows = one2manyFieldRows(name);
  return buildOne2ManyInlineCommands({
    original: originalValues.value[name],
    draftRows: rows.map((row) => ({
      id: row.id,
      isNew: row.isNew,
      removed: row.removed,
      dirty: row.dirty,
      values: row.isNew
        ? row.values || {}
        : Object.fromEntries((row.dirtyFields || []).map((key) => [key, row.values?.[key]])),
    })),
    mode,
  });
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

function isOne2manyEmptyValue(column: One2ManyColumn, value: unknown) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (ttype === 'boolean') return value === false || value === null || value === undefined;
  if (ttype === 'integer' || ttype === 'float' || ttype === 'monetary') {
    return value === false || value === null || value === undefined || Number.isNaN(Number(value));
  }
  if (ttype === 'date' || ttype === 'datetime' || ttype === 'selection') {
    return !String(value ?? '').trim() || value === false;
  }
  return !String(value ?? '').trim();
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
      if (reasonCode) messages.push(`原因码: ${reasonCode}`);
    });
    const rowState = String(patch.row_state || '').trim().toLowerCase();
    if (rowState) {
      messages.push(`联动状态: ${rowState}`);
    }
    if (Array.isArray(patch.command_hint) && patch.command_hint.length) {
      messages.push(`命令提示: ${patch.command_hint.join('/')}`);
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
  const descriptor = contract.value?.fields?.[name];
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

function exactRelationOption(rows: RelationOption[], keyword: string) {
  const normalized = String(keyword || '').trim().toLowerCase();
  if (!normalized) return null;
  return rows.find((row) => row.label.trim().toLowerCase() === normalized) || null;
}

function resolveRelationQuickFillOption(rows: RelationOption[], keyword: string, matchMode = 'exact_label') {
  const normalized = String(keyword || '').trim();
  if (!normalized) return null;
  const lowered = normalized.toLowerCase();
  const candidates = rows.filter((row) => row.label.trim().toLowerCase().includes(lowered));
  const exact = exactRelationOption(candidates, normalized);
  if (exact) return exact;
  return matchMode === 'single_contains_or_exact' && candidates.length === 1 ? candidates[0] : null;
}

function hasAmbiguousRelationMatches(rows: RelationOption[], keyword: string, matchMode = 'exact_label') {
  const normalized = String(keyword || '').trim().toLowerCase();
  if (!normalized) return false;
  const candidates = rows.filter((row) => row.label.trim().toLowerCase().includes(normalized));
  const exactCount = candidates.filter((row) => row.label.trim().toLowerCase() === normalized).length;
  if (exactCount > 1) return true;
  if (exactCount === 1) return false;
  return matchMode === 'single_contains_or_exact' && candidates.length > 1;
}

function filteredRelationOptions(name: string) {
  const rows = relationOptionsForField(name);
  const kw = relationKeyword(name).trim().toLowerCase();
  if (!kw) return rows;
  return rows.filter((row) => row.label.toLowerCase().includes(kw) || String(row.id).includes(kw));
}

function relationModel(name: string) {
  const descriptor = contract.value?.fields?.[name] as Record<string, unknown> | undefined;
  const entry = descriptor?.relation_entry && typeof descriptor.relation_entry === 'object' && !Array.isArray(descriptor.relation_entry)
    ? descriptor.relation_entry as Record<string, unknown>
    : {};
  return String(descriptor?.relation || entry.model || '').trim();
}

function sanitizeUiErrorMessage(raw: unknown, fallback: string) {
  const text = String(raw || '').trim();
  if (!text) return fallback;
  const lower = text.toLowerCase();
  if (
    lower.includes('duplicate key value')
    || lower.includes('unique constraint')
    || lower.includes('already exists')
    || text.includes('唯一')
    || text.includes('已存在')
  ) {
    return fallback || text;
  }
  if (lower.includes('psycopg2') || lower.includes('traceback') || lower.includes('sql')) {
    return fallback;
  }
  // Do not expose raw success envelopes as UI errors.
  if (text.startsWith('{') && text.includes('"ok"') && text.includes('"data"')) {
    if (text.includes('"ok": true') || text.includes('"records"')) {
      return fallback;
    }
  }
  return text;
}

function relationEntry(descriptor?: FieldDescriptor) {
  const entry = (descriptor as Record<string, unknown> | undefined)?.relation_entry;
  if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return null;
  const row = entry as Record<string, unknown>;
  const actionId = toPositiveInt(row.action_id);
  const menuId = toPositiveInt(row.menu_id);
  const createModeRaw = String(row.create_mode || '').trim().toLowerCase();
  const createMode = createModeRaw === 'page' || createModeRaw === 'quick' ? createModeRaw : 'disabled';
  const defaultVals = row.default_vals && typeof row.default_vals === 'object' && !Array.isArray(row.default_vals)
    ? (row.default_vals as Record<string, unknown>)
    : {};
  const inlineRaw = row.inline_create && typeof row.inline_create === 'object' && !Array.isArray(row.inline_create)
    ? row.inline_create as Record<string, unknown>
    : {};
  return {
    model: String(row.model || '').trim(),
    actionId,
    menuId,
    canRead: row.can_read !== false,
    canCreate: Boolean(row.can_create),
    createMode,
    defaultVals,
    reasonCode: String(row.reason_code || '').trim(),
    inlineCreate: {
      enabled: inlineRaw.enabled === true,
      createOnNoMatch: inlineRaw.create_on_no_match === true,
      nameField: String(inlineRaw.name_field || 'name').trim() || 'name',
      match: String(inlineRaw.match || '').trim() || 'exact_label',
    },
  };
}

function relationSearchDialogContract(name: string): Record<string, unknown> {
  const descriptor = contract.value?.fields?.[name] as Record<string, unknown> | undefined;
  const entry = descriptor?.relation_entry;
  if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return {};
  const dialog = (entry as Record<string, unknown>).search_dialog;
  if (!dialog || typeof dialog !== 'object' || Array.isArray(dialog)) return {};
  return dialog as Record<string, unknown>;
}

function relationUiLabels(descriptor?: FieldDescriptor): RelationUiLabels {
  const entry = (descriptor as Record<string, unknown> | undefined)?.relation_entry;
  const labels = entry && typeof entry === 'object' && !Array.isArray(entry)
    ? (entry as Record<string, unknown>).ui_labels
    : null;
  if (!labels || typeof labels !== 'object' || Array.isArray(labels)) return {};
  return Object.entries(labels as Record<string, unknown>).reduce<RelationUiLabels>((acc, [key, value]) => {
    const label = String(value || '').trim();
    if (key && label) acc[key] = label;
    return acc;
  }, {});
}

function relationUiLabel(descriptor: FieldDescriptor | undefined, key: string, fallback = '') {
  return relationUiLabels(descriptor)[key] || fallback || key;
}

function formUiLabels(): Record<string, string> {
  const formView = contract.value?.views?.form as (Record<string, unknown> | undefined);
  const labels = formView?.ui_labels;
  if (!labels || typeof labels !== 'object' || Array.isArray(labels)) return {};
  return Object.entries(labels as Record<string, unknown>).reduce<Record<string, string>>((acc, [key, value]) => {
    const label = String(value || '').trim();
    if (key && label) acc[key] = label;
    return acc;
  }, {});
}

function formUiLabel(key: string) {
  return formUiLabels()[key] || key;
}

function relationCreateMode(_fieldName: string, descriptor?: FieldDescriptor): 'page' | 'quick' | 'none' {
  const entry = relationEntry(descriptor);
  if (!entry) return 'none';
  if (entry.createMode === 'page' && entry.actionId) return 'page';
  if (entry.createMode === 'quick' && entry.canCreate) return 'quick';
  if (entry.model === 'sc.dictionary' && entry.canCreate && Object.keys(entry.defaultVals || {}).length) {
    return 'quick';
  }
  return 'none';
}

function relationInlineCreate(_fieldName: string, descriptor?: FieldDescriptor) {
  const entry = relationEntry(descriptor);
  if (!entry?.inlineCreate?.enabled) {
    return {
      enabled: false,
      createOnNoMatch: false,
      nameField: '',
      match: entry?.inlineCreate?.match || 'exact_label',
    };
  }
  return {
    enabled: true,
    createOnNoMatch: entry.inlineCreate.createOnNoMatch,
    nameField: entry.inlineCreate.nameField,
    match: entry.inlineCreate.match,
  };
}

function relationDomain(descriptor?: FieldDescriptor) {
  const entry = relationEntry(descriptor);
  const out: unknown[] = [];
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
  if (Array.isArray(base)) out.push(...base);
  if (Array.isArray(runtime)) out.push(...runtime);
  return out.length ? out : undefined;
}

async function queryRelationOptions(name: string, keyword: string): Promise<RelationOption[]> {
  const descriptor = contract.value?.fields?.[name];
  const relation = relationModel(name);
  if (!relation) return [];
  const entry = relationEntry(descriptor);
  if (entry && entry.canRead === false) {
    deniedRelationModels.add(relation);
    return [];
  }
  if (deniedRelationModels.has(relation)) return [];
  const search = String(keyword || '').trim();
  const domain = mergedRelationDomain(name, descriptor);
  try {
    const listed = await listContractFormRecords({
      model: relation,
      fields: relationReadFields(descriptor),
      limit: search ? 40 : 80,
      order: 'id desc',
      domain,
      search_term: search || undefined,
      silentErrors: true,
    });
    const records = Array.isArray(listed?.records) ? listed.records : [];
    const mapped = records
      .map((row) => relationOptionFromRow(row as Record<string, unknown>, descriptor))
      .filter((item): item is RelationOption => Boolean(item));
    relationOptions.value = {
      ...relationOptions.value,
      [name]: mapped,
    };
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
  const descriptor = contract.value?.fields?.[name];
  const relation = relationModel(name);
  if (!relation) return [];
  const entry = relationEntry(descriptor);
  if (entry && entry.canRead === false) return [];
  const domain = mergedRelationDomain(name, descriptor);
  const listed = await listContractFormRecords({
    model: relation,
    fields: relationReadFields(descriptor),
    limit,
    order: 'id desc',
    domain,
    search_term: String(keyword || '').trim() || undefined,
    silentErrors: true,
  });
  const records = Array.isArray(listed?.records) ? listed.records : [];
  return records
    .map((row) => relationOptionFromRow(row as Record<string, unknown>, descriptor))
    .filter((item): item is RelationOption => Boolean(item));
}

function fallbackRelationSearchColumns(name: string): RelationSearchColumn[] {
  const descriptor = contract.value?.fields?.[name];
  return [{
    name: 'display_name',
    label: String(descriptor?.string || '名称'),
  }];
}

function relationSearchColumnsFromContract(fieldName: string): RelationSearchColumn[] {
  const dialog = relationSearchDialogContract(fieldName);
  const columns = Array.isArray(dialog.columns) ? dialog.columns : [];
  const out: RelationSearchColumn[] = [];
  for (const item of columns) {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    const name = String(row.name || row.field || '').trim();
    if (!name || name === 'id') continue;
    const label = String(row.label || row.string || name).trim() || name;
    out.push({ name, label });
    if (out.length >= 8) break;
  }
  return out;
}

function normalizeRelationSearchColumns(data: Record<string, unknown> | undefined, fieldName: string): RelationSearchColumn[] {
  const fields = data?.fields && typeof data.fields === 'object'
    ? data.fields as Record<string, FieldDescriptor>
    : {};
  const views = data?.views && typeof data.views === 'object'
    ? data.views as Record<string, unknown>
    : {};
  const tree = views.tree && typeof views.tree === 'object'
    ? views.tree as Record<string, unknown>
    : {};
  const rawColumns = Array.isArray(tree.columns_schema) && tree.columns_schema.length
    ? tree.columns_schema
    : Array.isArray(tree.columns)
      ? tree.columns
      : [];
  const out: RelationSearchColumn[] = [];
  for (const item of rawColumns) {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : null;
    const name = String(row?.name || item || '').trim();
    if (!name || name === 'id') continue;
    const field = fields[name];
    const label = String(row?.label || row?.string || field?.string || name).trim();
    out.push({ name, label });
    if (out.length >= 6) break;
  }
  if (!out.length) return fallbackRelationSearchColumns(fieldName);
  return out;
}

async function loadRelationSearchColumns(fieldName: string): Promise<RelationSearchColumn[]> {
  const contractColumns = relationSearchColumnsFromContract(fieldName);
  if (contractColumns.length) return contractColumns;
  const relation = relationModel(fieldName);
  if (!relation) return fallbackRelationSearchColumns(fieldName);
  try {
    const response = await loadModelContractRaw(relation, {
      viewType: 'tree',
      renderProfile: 'readonly',
    });
    const data = response?.data && typeof response.data === 'object'
      ? response.data as Record<string, unknown>
      : response as unknown as Record<string, unknown>;
    return normalizeRelationSearchColumns(data, fieldName);
  } catch {
    return fallbackRelationSearchColumns(fieldName);
  }
}

function relationSearchReadFields(columns: RelationSearchColumn[], dialog: Record<string, unknown> = {}) {
  const out = new Set<string>(['id', 'display_name', 'name']);
  const contractFields = Array.isArray(dialog.read_fields) ? dialog.read_fields : [];
  for (const field of contractFields) {
    const name = String(field || '').trim();
    if (name) out.add(name);
  }
  for (const column of columns) {
    if (column.name) out.add(column.name);
  }
  return Array.from(out);
}

async function fetchRelationSearchRows(name: string, keyword: string, limit = 120): Promise<RelationSearchRow[]> {
  const descriptor = contract.value?.fields?.[name];
  const relation = relationModel(name);
  if (!relation) return [];
  const entry = relationEntry(descriptor);
  if (entry && entry.canRead === false) return [];
  const domain = mergedRelationDomain(name, descriptor);
  const dialog = relationSearchDialogContract(name);
  const columns = relationSearchDialog.columns.length ? relationSearchDialog.columns : relationSearchColumnsFromContract(name);
  const limitValue = Number(dialog.limit || limit || 120);
  const order = String(dialog.order || 'id desc').trim() || 'id desc';
  const listed = await listContractFormRecords({
    model: relation,
    fields: relationSearchReadFields(columns.length ? columns : fallbackRelationSearchColumns(name), dialog),
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
  relationSearchDialog.columns = relationSearchColumnsFromContract(fieldName);
  relationSearchDialog.selectedId = null;
  relationSearchDialog.createMode = relationCreateMode(fieldName, descriptor);
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
  markFieldChanged(fieldName);
  relationKeywords[fieldName] = option.label;
  mergeRelationOptions(fieldName, [option]);
}

async function createRelationFromSearchDialog() {
  const fieldName = relationSearchDialog.fieldName;
  if (!fieldName) return;
  const descriptor = contract.value?.fields?.[fieldName];
  const label = relationSearchDialog.keyword.trim();
  const mode = relationCreateMode(fieldName, descriptor);
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
  const mode = relationCreateMode(fieldName, descriptor);
  if (mode === 'none') {
    validationErrors.value = [relationUiLabel(descriptor, 'missing_create_entry')];
    return;
  }
  const entry = relationEntry(descriptor);
  const relationActionId = entry?.actionId || null;
  const menuId = entry?.menuId || 0;
  if (!relationActionId && mode === 'quick') {
    const label = String(window.prompt(relationUiLabel(descriptor, 'quick_create_prompt')) || '').trim();
    if (label) await quickCreateRelation(fieldName, descriptor, label);
    return;
  }
  if (!relationActionId) {
    validationErrors.value = [relationUiLabel(descriptor, 'missing_page_entry')];
    return;
  }
  const defaultQuery = Object.entries(entry?.defaultVals || {}).reduce<Record<string, unknown>>((acc, [key, value]) => {
    if (!key) return acc;
    acc[`default_${key}`] = value;
    return acc;
  }, {});
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
      const label = String(window.prompt(relationUiLabel(descriptor, 'page_unavailable_prompt')) || '').trim();
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
  return Boolean(relation && currentRelationRecordId(fieldName) > 0 && entry?.canRead !== false);
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
    const inline = relationInlineCreate(fieldName, descriptor);
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
        order: 'id desc',
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

function normalizeActionLabel(raw: unknown, fallback = ''): string {
  const text = String(raw ?? '').trim();
  if (!text) return String(fallback || '').trim();
  if (!text.startsWith('{') || !text.includes('label')) return text;
  const match = text.match(/['"]label['"]\s*:\s*['"]([^'"]+)['"]/);
  if (match?.[1]) return String(match[1]).trim();
  return text;
}

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
      if (sourceWidgetId !== 'page.header') return;
      const triggerType = String(row.triggerType || row.trigger_type || '').trim();
      if (triggerType && triggerType !== 'click') return;
      const key = String(row.actionKey || row.key || row.actionId || '').trim();
      if (!key) return;
      const target = parseMaybeJsonRecord(row.target);
      const clientMode = String(target.mode || target.client_mode || '').trim();
      merged.push({
        key,
        label: String(row.label || key).trim() || key,
        kind: clientMode ? 'client' : 'open',
        intent: String(row.intent || '').trim(),
        level: 'header',
        selection: 'none',
        sourceWidgetId,
        target,
        target_model: String(target.model || '').trim(),
        payload: {
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
const nativeChatterActions = computed<NativeChatterAction[]>(() => {
  const chatter = contract.value?.views?.form?.chatter as Record<string, unknown> | undefined;
  if (!chatter || chatter.enabled !== true) return [];
  const actions = Array.isArray(chatter.actions) ? chatter.actions as Array<Record<string, unknown>> : [];
  return actions
    .map((row) => {
      const key = String(row.key || row.label || '').trim();
      const intent = String(row.intent || row.kind || key).trim().toLowerCase();
      const payload = row.payload && typeof row.payload === 'object' && !Array.isArray(row.payload)
        ? row.payload as Record<string, unknown>
        : {};
      const mode = String(payload.mode || intent || key).trim().toLowerCase();
      return {
        key,
        label: String(row.label || row.key || '').trim(),
        intent,
        mode,
        payload,
        enabled: Boolean(recordId.value) && Boolean(model.value),
        hint: intent,
      };
    })
    .filter((row) => row.key && row.label);
});

const nativeChatterTitle = computed(() => {
  const chatter = contract.value?.views?.form?.chatter as Record<string, unknown> | undefined;
  return String(chatter?.label || '').trim();
});

const nativeCollaborationTitle = computed(() => nativeChatterTitle.value || nativeAttachmentLabel('label', '附件'));

const activeChatterSubmitLabel = computed(() => {
  if (activeChatterMode.value === 'activity') return activeChatterLabel.value || '安排活动';
  if (activeChatterMode.value === 'note') return '记录备注';
  return '发送消息';
});

const activeChatterPlaceholder = computed(() => {
  if (activeChatterMode.value === 'note') return '输入备注内容';
  return '输入消息内容';
});

const activeChatterIsActivity = computed(() => activeChatterMode.value === 'activity');

const activeActivityAction = computed(() => (
  nativeChatterActions.value.find((item) => item.mode === 'activity' && item.label === activeChatterLabel.value)
  || nativeChatterActions.value.find((item) => item.mode === 'activity')
  || null
));

function activityFieldLabel(name: string, fallback: string) {
  const fields = activeActivityAction.value?.payload?.fields;
  if (!Array.isArray(fields)) return fallback;
  const row = fields.find((item) => item && typeof item === 'object' && String((item as Record<string, unknown>).name || '') === name) as Record<string, unknown> | undefined;
  return String(row?.label || fallback).trim();
}

const activitySummaryLabel = computed(() => activityFieldLabel('summary', '摘要'));
const activityDeadlineLabel = computed(() => activityFieldLabel('date_deadline', '截止日期'));
const activityNoteLabel = computed(() => activityFieldLabel('note', '备注'));

const isNativeChatterSubmitDisabled = computed(() => {
  if (chatterPosting.value) return true;
  if (activeChatterMode.value === 'activity') return !activitySummary.value.trim();
  return !chatterDraft.value.trim();
});

const nativeAttachments = computed(() => {
  const formView = contract.value?.views?.form as (Record<string, unknown> | undefined);
  const raw = formView?.attachments as Record<string, unknown> | undefined;
  if (!raw || raw.enabled !== true) return null;
  return raw;
});

const nativeAttachmentLabels = computed<Record<string, string>>(() => {
  const labels = nativeAttachments.value?.ui_labels;
  return labels && typeof labels === 'object' && !Array.isArray(labels)
    ? labels as Record<string, string>
    : {};
});

function nativeAttachmentLabel(key: string, fallback: string) {
  return String(nativeAttachmentLabels.value[key] || fallback).trim();
}

const nativeAttachmentUploadLabel = computed(() => nativeAttachmentLabel('upload', '上传附件'));
const nativeAttachmentUploadingLabel = computed(() => nativeAttachmentLabel('uploading', '上传中...'));
const nativeAttachmentDownloadLabel = computed(() => nativeAttachmentLabel('download', '下载'));
const nativeAttachmentMaxBytes = computed(() => {
  const upload = nativeAttachments.value?.upload;
  const raw = upload && typeof upload === 'object' && !Array.isArray(upload)
    ? Number((upload as Record<string, unknown>).max_bytes || 0)
    : 0;
  return Number.isFinite(raw) && raw > 0 ? raw : 5 * 1024 * 1024;
});

const hasNativeChatterNode = computed(() => nativeLayoutContainsType(nativeFormLayoutNodes.value, 'chatter'));

function nativeLayoutContainsType(nodes: NativeFormLayoutNode[], type: string): boolean {
  const target = String(type || '').trim().toLowerCase();
  for (const node of nodes || []) {
    const current = String(node?.type || '').trim().toLowerCase();
    if (current === target) return true;
    const children: NativeFormLayoutNode[] = [];
    for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
      const value = node?.[key];
      if (Array.isArray(value)) children.push(...value);
    }
    if (children.length && nativeLayoutContainsType(children, target)) return true;
  }
  return false;
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
  const needRecord = kind === 'object' || kind === 'server' || level === 'row' || level === 'smart';
  return {
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
  };
}

async function runNativeLayoutAction(row: Record<string, unknown>) {
  const action = contractActionFromNativeRow(row);
  if (!action) return;
  if ((action.kind === 'object' || action.kind === 'server') && action.methodName && recordId.value) {
    if (!action.enabled || !confirmActionSafety(action)) return;
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
        await router.push(buildEntryTargetRouteTarget(result.entry_target, {
          query: pickContractNavQuery(route.query as Record<string, unknown>),
          actionId: result.action_id,
        }) as never);
        return;
      }
      const nextActionId = toPositiveInt(result?.action_id);
      if (nextActionId) {
        await router.push({
          name: 'action',
          params: { actionId: String(nextActionId) },
          query: pickContractNavQuery(route.query as Record<string, unknown>, { action_id: nextActionId }),
        });
        return;
      }
      await reload();
      return;
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : 'action execute failed';
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
  const raw = Array.isArray(contract.value?.field_groups) ? contract.value?.field_groups : [];
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
  return `严格模式检测到后端契约缺口：${missing.join(', ')}`;
});
const strictContractDefaultsSummary = computed(() => {
  if (!strictContractMode.value) return '';
  const raw = strictContractGuard.value.defaults_applied;
  if (!Array.isArray(raw) || !raw.length) return '';
  const defaults = raw.map((item) => String(item || '').trim()).filter(Boolean);
  if (!defaults.length) return '';
  return `当前由后端兜底补齐：${defaults.join(', ')}`;
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
  const rows = Array.isArray(contract.value?.visible_fields) ? contract.value?.visible_fields : [];
  return rows.map((name) => String(name || '').trim()).filter(Boolean);
});

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

function isFieldVisible(name: string) {
  if (isProjectQuickIntakeMode.value) {
    return ['name', 'manager_id', 'owner_id'].includes(String(name || '').trim());
  }
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

const nativeFormLayoutNodes = computed<NativeFormLayoutNode[]>(() => {
  const storeContainers = resolveContractV2ContainerTree(v2ContractStore.value);
  const v2 = storeContainers.length ? null : resolveUnifiedPageContractV2(contract.value);
  const containers = storeContainers.length
    ? storeContainers
    : (Array.isArray(v2?.layoutContract?.containerTree) ? v2.layoutContract.containerTree : []);
  if (containers.length > 0) {
    return containers as unknown as NativeFormLayoutNode[];
  }
  const legacyLayout = Array.isArray(contract.value?.views?.form?.layout)
    ? contract.value?.views?.form?.layout
    : [];
  return legacyLayout as unknown as NativeFormLayoutNode[];
});

function countNativeNodesByType(nodes: NativeFormLayoutNode[], targetType: string): number {
  const target = String(targetType || '').trim().toLowerCase();
  let count = 0;
  nodes.forEach((node) => {
    const type = String(node?.type || (node as { containerType?: string })?.containerType || '').trim().toLowerCase();
    if (type === target) count += 1;
    (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
      const children = node?.[key];
      if (Array.isArray(children)) count += countNativeNodesByType(children as NativeFormLayoutNode[], target);
    });
  });
  return count;
}

const nativeNotebookPageCount = computed(() => countNativeNodesByType(nativeFormLayoutNodes.value, 'page'));
const nativeGroupCount = computed(() => countNativeNodesByType(nativeFormLayoutNodes.value, 'group'));

function resolveNativeButtonLabel(node: NativeFormLayoutNode) {
  const action = node?.action && typeof node.action === 'object' && !Array.isArray(node.action)
    ? node.action as Record<string, unknown>
    : {};
  const badge = action.badge && typeof action.badge === 'object' && !Array.isArray(action.badge)
    ? action.badge as Record<string, unknown>
    : {};
  const countField = String(badge.count_field || badge.field || '').trim();
  const sourceField = String(badge.source_field || '').trim();
  const badgeLabel = String(badge.label || node.displayLabel || node.label || node.string || node.name || '').trim();
  if (!badgeLabel) {
    return String(node.displayLabel || action.displayLabel || node.label || node.string || node.name || '操作').trim();
  }
  const countValue = countField ? formData[countField] : undefined;
  const count = Array.isArray(countValue) ? countValue.length : (typeof countValue === 'number' ? countValue : null);
  if (count !== null) {
    return `${count}${badgeLabel}`;
  }
  const sourceValue = sourceField ? formData[sourceField] : undefined;
  const sourceCount = Array.isArray(sourceValue) ? sourceValue.length : (typeof sourceValue === 'number' ? sourceValue : null);
  if (sourceCount === null) {
    return String(node.displayLabel || action.displayLabel || node.label || node.string || node.name || '操作').trim();
  }
  return `${sourceCount}${badgeLabel}`;
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

function collectNativeLayoutFieldNames(nodes: NativeFormLayoutNode[], out: Set<string>) {
  nodes.forEach((node) => {
    const type = String(node?.type || '').trim().toLowerCase();
    const name = String(node?.name || '').trim();
    if (type === 'field' && name && contract.value?.fields?.[name]) {
      out.add(name);
    }
    (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
      const children = node?.[key];
      if (Array.isArray(children)) collectNativeLayoutFieldNames(children as NativeFormLayoutNode[], out);
    });
  });
}

function collectNativeLayoutBadgeCountFieldNames(nodes: NativeFormLayoutNode[], out: Set<string>) {
  nodes.forEach((node) => {
    const type = String(node?.type || '').trim().toLowerCase();
    if (type === 'button') {
      const action = node?.action && typeof node.action === 'object' && !Array.isArray(node.action)
        ? node.action as Record<string, unknown>
        : {};
      const badge = action.badge && typeof action.badge === 'object' && !Array.isArray(action.badge)
        ? action.badge as Record<string, unknown>
        : {};
      const fieldName = String(badge.count_field || badge.field || '').trim();
      if (fieldName) out.add(fieldName);
    }
    (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
      const children = node?.[key];
      if (Array.isArray(children)) collectNativeLayoutBadgeCountFieldNames(children as NativeFormLayoutNode[], out);
    });
  });
}

function collectContractActionBadgeCountFieldNames(actions: unknown, out: Set<string>) {
  if (!Array.isArray(actions)) return;
  actions.forEach((row) => {
    if (!row || typeof row !== 'object' || Array.isArray(row)) return;
    const action = row as Record<string, unknown>;
    const badge = action.badge && typeof action.badge === 'object' && !Array.isArray(action.badge)
      ? action.badge as Record<string, unknown>
      : {};
    const fieldName = String(badge.count_field || badge.field || '').trim();
    if (fieldName) out.add(fieldName);
  });
}

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
  collectNativeLayoutFieldNames(nativeFormLayoutNodes.value, names);
  collectNativeLayoutBadgeCountFieldNames(nativeFormLayoutNodes.value, names);
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
  if (fieldMap.active) names.add('active');
  if (!names.size) {
    Object.keys(fieldMap).slice(0, 40).forEach((name) => names.add(name));
  }
  return Array.from(names);
}

const nativeFavoriteFieldNames = computed(() => {
  const names = new Set<string>();
  collectNativeFavoriteFieldNames(nativeFormLayoutNodes.value, names);
  return names;
});

const nativeStatusbar = computed(() => {
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

function nativeModifierValue(nodeRaw: NativeFormLayoutNode, key: 'invisible' | 'readonly' | 'required') {
  const node = nodeRaw as Record<string, unknown>;
  const attributes = node.attributes && typeof node.attributes === 'object'
    ? node.attributes as Record<string, unknown>
    : {};
  const action = node.action && typeof node.action === 'object' && !Array.isArray(node.action)
    ? node.action as Record<string, unknown>
    : {};
  const actionVisible = action.visible && typeof action.visible === 'object' && !Array.isArray(action.visible)
    ? action.visible as Record<string, unknown>
    : {};
  const actionVisibleAttrs = actionVisible.attrs && typeof actionVisible.attrs === 'object' && !Array.isArray(actionVisible.attrs)
    ? actionVisible.attrs as Record<string, unknown>
    : {};
  const fieldInfo = nativeNodeFieldInfo(node);
  const attributeModifiers = attributes.modifiers && typeof attributes.modifiers === 'object'
    ? attributes.modifiers as Record<string, unknown>
    : {};
  const fieldInfoModifiers = fieldInfo.modifiers && typeof fieldInfo.modifiers === 'object'
    ? fieldInfo.modifiers as Record<string, unknown>
    : {};
  const modifiers = node.modifiers && typeof node.modifiers === 'object'
    ? node.modifiers as Record<string, unknown>
    : {};
  if (key in modifiers) return modifiers[key];
  if (key in attributeModifiers) return attributeModifiers[key];
  if (key in actionVisibleAttrs) return actionVisibleAttrs[key];
  if (key in fieldInfoModifiers) return fieldInfoModifiers[key];
  if (key in fieldInfo) return fieldInfo[key];
  if (key in attributes) return attributes[key];
  if (key in node) return node[key];
  return undefined;
}

function compareNativeModifierValue(actual: unknown, operator: string, expected: unknown) {
  const left = Array.isArray(actual) && typeof actual[0] === 'number' ? actual[0] : actual;
  const key = String(operator || '').trim();
  if (key === '=' || key === '==') return String(left ?? '') === String(expected ?? '');
  if (key === '!=' || key === '<>') return String(left ?? '') !== String(expected ?? '');
  if (key === 'in') return Array.isArray(expected) && expected.map((item) => String(item)).includes(String(left ?? ''));
  if (key === 'not in') return Array.isArray(expected) && !expected.map((item) => String(item)).includes(String(left ?? ''));
  if (key === '>') return Number(left) > Number(expected);
  if (key === '>=') return Number(left) >= Number(expected);
  if (key === '<') return Number(left) < Number(expected);
  if (key === '<=') return Number(left) <= Number(expected);
  return false;
}

function evaluateNativeModifierValue(value: unknown) {
  if (typeof value === 'boolean') return value;
  if (!value || typeof value !== 'object' || Array.isArray(value)) return isStaticTruthyModifier(value);
  const row = value as Record<string, unknown>;
  const kind = String(row.kind || '').trim();
  if (kind === 'static') return Boolean(row.value);
  if (kind === 'not') return !evaluateNativeModifierValue(row.expr);
  if (kind === 'all') {
    const exprs = Array.isArray(row.exprs) ? row.exprs : [];
    return exprs.every((expr) => evaluateNativeModifierValue(expr));
  }
  if (kind === 'any') {
    const exprs = Array.isArray(row.exprs) ? row.exprs : [];
    return exprs.some((expr) => evaluateNativeModifierValue(expr));
  }
  const field = String(row.field || '').trim();
  if (!field) return false;
  if (kind === 'field_truthy') return Boolean(formData[field]);
  if (kind === 'field_compare') return compareNativeModifierValue(formData[field], String(row.operator || ''), row.value);
  return false;
}

function evaluateNativeActionVisibility(row: Record<string, unknown>) {
  const visible = row.visible && typeof row.visible === 'object' && !Array.isArray(row.visible)
    ? row.visible as Record<string, unknown>
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
  return !evaluateNativeModifierValue(invisible);
}

function isNativeLayoutNodeVisible(nodeRaw: NativeFormLayoutNode) {
  return !evaluateNativeModifierValue(nativeModifierValue(nodeRaw, 'invisible'));
}

function nativeNodeWidget(nodeRaw?: NativeFormLayoutNode) {
  const node = nodeRaw as Record<string, unknown> | undefined;
  const fieldInfo = nativeNodeFieldInfo(node);
  return String(node?.widget || fieldInfo.widget || '').trim().toLowerCase();
}

function nativeNodeWidgetSemantics(nodeRaw?: NativeFormLayoutNode) {
  const node = nodeRaw as Record<string, unknown> | undefined;
  const fieldInfo = nativeNodeFieldInfo(node);
  const semantics = fieldInfo.widget_semantics && typeof fieldInfo.widget_semantics === 'object'
    ? fieldInfo.widget_semantics as Record<string, unknown>
    : {};
  return semantics;
}

function collectNativeFavoriteFieldNames(nodes: NativeFormLayoutNode[], out: Set<string>) {
  for (const node of nodes) {
    const name = String(node?.name || '').trim();
    const label = String(node?.label || node?.string || '').trim();
    if (
      name
      && (
        nativeNodeWidget(node) === 'boolean_favorite'
        || name === 'is_favorite'
        || (nativeNodeWidget(node) === 'checkbox' && label.includes('仪表板'))
      )
    ) {
      out.add(name);
    }
    const children: NativeFormLayoutNode[] = [];
    for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
      const value = node?.[key];
      if (Array.isArray(value)) children.push(...value);
    }
    if (children.length) collectNativeFavoriteFieldNames(children, out);
  }
}

function isNativeFavoriteField(name: string) {
  return nativeFavoriteFieldNames.value.has(String(name || '').trim());
}

function nativeFieldLabel(nodeRaw: NativeFormLayoutNode, descriptor?: FieldDescriptor) {
  const node = nodeRaw as Record<string, unknown>;
  const fieldInfo = nativeNodeFieldInfo(node);
  return String(
    node.string
    || node.label
    || fieldInfo.string
    || fieldInfo.label
    || descriptor?.string
    || nodeRaw.name
    || '',
  );
}

function isStaticTruthyModifier(value: unknown) {
  if (value === true || value === 1) return true;
  if (typeof value !== 'string') return false;
  return ['1', 'true', 'True'].includes(value.trim());
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
  const descriptor = contract.value?.fields?.[normalized];
  if (!descriptor) return false;
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
  const descriptor = contract.value?.fields?.[name];
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
  if (!resolved.visible && !(renderProfile.value === 'create' && fieldSemanticMeta(name).surface_role === 'advanced')) return null;
  const state = runtimeState(name);
  const nativeReadonly = isStaticTruthyModifier(nativeModifierValue(nodeRaw, 'readonly'));
  const nativeRequired = isStaticTruthyModifier(nativeModifierValue(nodeRaw, 'required'));
  return {
    key: `native_field_${name}_${index}`,
    kind: 'field',
    name,
    label: nativeFieldLabel(nodeRaw, descriptor),
    readonly: Boolean(nativeReadonly || resolved.readonly || state.readonly || (recordId.value ? !rights.value.write : !rights.value.create)),
    required: Boolean(nativeRequired || resolved.required || state.required || descriptor?.required),
    widget: nativeNodeWidget(nodeRaw),
    widgetSemantics: nativeNodeWidgetSemantics(nodeRaw),
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

function isMissingRequiredValue(value: unknown) {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim().length === 0;
  if (typeof value === 'number') return !Number.isFinite(value) || value <= 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'boolean') return false;
  if (typeof value === 'object') return Object.keys(value as Record<string, unknown>).length === 0;
  return false;
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
      label: String(descriptor?.string || name),
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
  resolveSpanClass: (field) => resolveFieldSpanClass({
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
  resolveRelationCreateMode: (fieldName, descriptor) => relationCreateMode(fieldName, descriptor),
  resolveRelationInlineCreate: (fieldName, descriptor) => {
    const inline = relationInlineCreate(fieldName, descriptor);
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
    const mode = relationCreateMode(_fieldName, descriptor);
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
  relationCreateMode: (fieldName: string) => relationCreateMode(fieldName, contract.value?.fields?.[fieldName]),
  relationCreateLabel: (fieldName: string) => {
    const descriptor = contract.value?.fields?.[fieldName];
    const mode = relationCreateMode(fieldName, descriptor);
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
    const inline = relationInlineCreate(fieldName, descriptor);
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

function normalizeComparable(value: unknown) {
  if (Array.isArray(value) && value.every((item) => typeof item === 'number')) {
    return JSON.stringify([...value].sort((a, b) => a - b));
  }
  if (Array.isArray(value)) return JSON.stringify(value);
  if (value && typeof value === 'object') return JSON.stringify(value);
  return String(value ?? '');
}

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

function parseNumeric(text: unknown) {
  const raw = String(text ?? '').trim();
  if (!raw) return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : null;
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
  } catch (err) {
    formData[name] = previousValue;
    console.warn('[native-favorite] failed to save favorite state', err);
  }
}

function setMany2oneField(name: string, descriptor: FieldDescriptor | undefined, value: string) {
  const normalized = String(value || '').trim();
  if (!normalized) {
    formData[name] = false;
    relationKeywords[name] = '';
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
    markFieldChanged(name);
    return;
  }
  const normalizedId = Math.trunc(id);
  formData[name] = normalizedId;
  const selected = relationOptionsForField(name).find((option) => option.id === normalizedId);
  if (selected) {
    relationKeywords[name] = selected.label;
  }
  markFieldChanged(name);
}

function queryMany2oneInline(name: string, descriptor: FieldDescriptor | undefined, value: string) {
  const keyword = String(value || '').trim();
  relationKeywords[name] = keyword;
  if (!keyword) {
    formData[name] = false;
    markFieldChanged(name);
    return;
  }
  setRelationKeyword(name, keyword);
}

async function commitMany2oneInline(name: string, descriptor: FieldDescriptor | undefined, value: string) {
  const keyword = String(value || '').trim();
  if (!keyword) {
    formData[name] = false;
    relationKeywords[name] = '';
    markFieldChanged(name);
    return;
  }
  const inline = relationInlineCreate(name, descriptor);
  const localQuickFill = resolveRelationQuickFillOption(relationOptionsForField(name), keyword, inline.match);
  if (localQuickFill) {
    setMany2oneOption(name, localQuickFill);
    return;
  }
  const rows = await queryRelationOptions(name, keyword);
  const remoteQuickFill = resolveRelationQuickFillOption(rows, keyword, inline.match);
  if (remoteQuickFill) {
    setMany2oneOption(name, remoteQuickFill);
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
    const inline = relationInlineCreate(node.name, descriptor);
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
    const inline = relationInlineCreate(name, descriptor);
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
  const inline = relationInlineCreate(name, descriptor);
  if (!inline.enabled || !inline.createOnNoMatch) return;
  const existing = resolveRelationQuickFillOption(relationOptionsForField(name), label, inline.match);
  if (existing) {
    addRelationId(name, existing);
    return;
  }
  const nameField = inline.nameField || 'name';
  try {
    const created = await createContractFormRecord({ model: relation, vals: { [nameField]: label } });
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

function fieldInputType(ttype?: string) {
  const type = String(ttype || '').toLowerCase();
  if (type === 'integer' || type === 'float' || type === 'monetary') return 'number';
  if (type === 'date') return 'date';
  if (type === 'datetime') return 'datetime-local';
  return 'text';
}

function normalizeRouteDefault(value: unknown) {
  const raw = Array.isArray(value) ? value[value.length - 1] : value;
  if (typeof raw !== 'string') return raw;
  const normalized = raw.trim();
  if (!normalized) return '';
  if (normalized === 'true') return true;
  if (normalized === 'false') return false;
  if (/^-?\d+(\.\d+)?$/.test(normalized)) return Number(normalized);
  return normalized;
}

function resolveNavigationUrl(url: string) {
  const raw = String(url || '').trim();
  if (!raw) return '';
  if (/^https?:\/\//i.test(raw)) return raw;
  if (raw.startsWith('/')) return `${window.location.origin}${raw}`;
  return raw;
}

function syncContractV2ShadowStore(rawContract: unknown) {
  v2ContractStore.value = null;
  v2ContractDecodeError.value = '';
  try {
    const snapshot = decodeContractV2Snapshot(rawContract);
    v2ContractStore.value = createContractV2Store(snapshot);
  } catch (err) {
    if (err instanceof ContractV2DecodeError) {
      v2ContractDecodeError.value = err.issues.slice(0, 4).map((issue) => `${issue.path} ${issue.message}`).join(' | ');
      return;
    }
    v2ContractDecodeError.value = err instanceof Error ? err.message : 'unknown v2 contract decode error';
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
  return {
    applied: Boolean(orchestration.applied || current.applied || contracts.length),
    owner: String(orchestration.owner_layer || current.owner_layer || '-'),
    contractCount: contracts.length,
    contractNames: contracts.map((row) => String(row.name || row.id || '').trim()).filter(Boolean).join(',') || '-',
    legacyOverlay: Boolean(current.legacy_field_policy_overlay),
  };
});

const hudEntries = computed(() => [
  { label: 'model', value: model.value || '-' },
  { label: 'action_id', value: actionId.value || '-' },
  { label: 'record_id', value: recordIdDisplay.value },
  { label: 'contract_loaded', value: Boolean(contract.value) },
  { label: 'contract_ready', value: contractReadiness.value.usable },
  { label: 'contract_issues', value: contractReadiness.value.issues.length },
  { label: 'v2_shadow_store', value: v2ShadowStoreReady.value },
  { label: 'v2_shadow_widgets', value: v2ShadowWidgetCount.value },
  { label: 'v2_shadow_actions', value: v2ShadowActionCount.value },
  { label: 'v2_shadow_button_statuses', value: v2ShadowButtonStatusCount.value },
  { label: 'v2_shadow_field_codes', value: v2ShadowFieldCodeCount.value },
  { label: 'v2_shadow_field_overlap', value: v2ShadowLegacyFieldOverlapCount.value },
  { label: 'v2_shadow_field_missing', value: v2ShadowLegacyFieldMissingPreview.value },
  { label: 'v2_shadow_layout_source', value: v2ShadowLayoutSourceKind.value },
  { label: 'v2_shadow_global_source', value: v2ShadowGlobalSourceKind.value },
  { label: 'v2_shadow_source_context', value: v2ShadowSourceContextKind.value },
  { label: 'v2_shadow_status_fields', value: v2ShadowStatusFieldCount.value },
  { label: 'v2_shadow_value_fields', value: v2ShadowValueFieldCount.value },
  { label: 'v2_shadow_main_data_fields', value: v2ShadowMainDataFieldCount.value },
  { label: 'v2_shadow_readonly_values', value: v2ShadowReadonlyValueCount.value },
  { label: 'v2_shadow_value_source', value: v2ShadowValueSourceKind.value },
  { label: 'v2_shadow_error', value: v2ContractDecodeError.value || '-' },
  { label: 'contract_view_type', value: contract.value?.head?.view_type || contract.value?.view_type || '-' },
  { label: 'view_orchestration_applied', value: viewOrchestrationHudSummary.value.applied },
  { label: 'view_orchestration_owner', value: viewOrchestrationHudSummary.value.owner },
  { label: 'view_orchestration_contracts', value: viewOrchestrationHudSummary.value.contractCount },
  { label: 'view_orchestration_names', value: viewOrchestrationHudSummary.value.contractNames },
  { label: 'legacy_policy_overlay', value: viewOrchestrationHudSummary.value.legacyOverlay },
  { label: 'render_profile', value: renderProfile.value },
  { label: 'fields_count', value: Object.keys(contract.value?.fields || {}).length },
  { label: 'layout_nodes', value: layoutNodes.value.length },
  { label: 'writable_fields', value: writableFieldCount.value },
  { label: 'changed_fields', value: changedFieldCount.value },
  { label: 'actions_count', value: contractActions.value.length },
  { label: 'rights', value: `${rights.value.read ? 'R' : '-'}${rights.value.write ? 'W' : '-'}${rights.value.create ? 'C' : '-'}${rights.value.unlink ? 'D' : '-'}` },
  { label: 'onchange_warnings', value: onchangeWarnings.value.length },
  { label: 'onchange_line_patches', value: onchangeLinePatches.value.length },
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
    if (headViewType && headViewType !== 'form') issues.push(`head.view_type is ${headViewType}, expected form`);
    if (viewType && viewType !== 'form') issues.push(`view_type is ${viewType}, expected form`);
    if (v2ViewType && v2ViewType !== 'form') issues.push(`v2.pageInfo.viewType is ${v2ViewType}, expected form`);
  }

  const visible = Array.isArray(row.visible_fields)
    ? row.visible_fields.map((x) => String(x || '').trim()).filter(Boolean)
    : [];
  const visibleNameSet = new Set(visible);
  const groupNames = new Set<string>();
  const groups = Array.isArray(row.field_groups) ? row.field_groups : [];
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
    throw new Error('empty contract');
  }
  const markerCheck = validateSurfaceMarkers(
    response.data,
    (response.meta as Record<string, unknown> | null) || null,
    requestedSurface.value,
  );
  if (!markerCheck.ok) {
    throw new Error(`contract surface markers invalid: ${markerCheck.issues.slice(0, 4).join(' | ')}`);
  }
  const readiness = analyzeFormContractReadiness(response.data, { requirePureFormViewType: false });
  if (!readiness.usable) {
    throw new Error(`contract not renderable: ${readiness.issues.slice(0, 4).join(' | ')}`);
  }
  contract.value = response.data as ActionContract;
  contractMeta.value = response.meta || null;
  syncContractV2ShadowStore(response.data);
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
    const incoming = Object.prototype.hasOwnProperty.call(contractMainData, name)
      ? contractMainData[name]
      : (row as Record<string, unknown>)[name] ?? '';
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
}

async function loadNativeChatterTimeline() {
  if (!recordId.value || !model.value) return;
  chatterLoading.value = true;
  try {
    const response = await fetchChatterTimeline({
      model: model.value,
      res_id: recordId.value,
      limit: 12,
      include_audit: false,
    });
    chatterTimeline.value = Array.isArray(response.items) ? response.items : [];
  } catch (err) {
    chatterError.value = err instanceof Error ? err.message : 'chatter timeline load failed';
  } finally {
    chatterLoading.value = false;
  }
}

async function openNativeChatterAction(action: NativeChatterAction) {
  if (!action.enabled) return;
  chatterError.value = '';
  const mode = action.mode || action.intent;
  if (mode === 'message' || mode === 'note' || mode === 'activity') {
    activeChatterMode.value = mode;
    activeChatterLabel.value = action.label;
    if (!chatterTimeline.value.length && !chatterLoading.value) {
      await loadNativeChatterTimeline();
    }
    return;
  }
  activeChatterMode.value = '';
  activeChatterLabel.value = action.label;
  chatterError.value = `${action.label} 缺少可执行调度契约`;
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
    });
    chatterDraft.value = '';
    await loadNativeChatterTimeline();
  } catch (err) {
    chatterError.value = err instanceof Error ? err.message : 'chatter post failed';
  } finally {
    chatterPosting.value = false;
  }
}

async function scheduleNativeChatterActivity() {
  const summary = activitySummary.value.trim();
  if (!summary || !recordId.value || !model.value || chatterPosting.value) return;
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
    });
    activitySummary.value = '';
    activityDeadline.value = '';
    activityNote.value = '';
    await loadNativeChatterTimeline();
  } catch (err) {
    chatterError.value = err instanceof Error ? err.message : 'chatter activity schedule failed';
  } finally {
    chatterPosting.value = false;
  }
}

async function onNativeAttachmentSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file || !recordId.value || !model.value || attachmentUploading.value) return;
  attachmentError.value = '';
  if (file.size > nativeAttachmentMaxBytes.value) {
    attachmentError.value = nativeAttachmentLabel('size_exceeded', '文件过大');
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

async function downloadNativeAttachment(att: { id?: number; name?: string; mimetype?: string }) {
  if (!att?.id) return;
  attachmentError.value = '';
  try {
    const payload = await downloadFile({ id: Number(att.id) });
    const binary = atob(payload.datas || '');
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: payload.mimetype || att.mimetype || 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = payload.name || att.name || 'download';
    link.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    attachmentError.value = err instanceof Error ? err.message : nativeAttachmentLabel('download_failed', '附件下载失败');
  }
}

async function reload() {
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
    errorMessage.value = err instanceof Error ? err.message : 'load failed';
    status.value = 'error';
  }
}

async function preloadFormAuxiliaryData(reloadToken: number) {
  try {
    await loadRelationOptions();
    if (reloadToken !== activeReloadToken) return;
    await hydrateSelectedRelationOptions();
    if (reloadToken !== activeReloadToken) return;
    await hydrateVisibleOne2manyRows();
  } catch (err) {
    if (showHud.value) {
      // eslint-disable-next-line no-console
      console.info('[ContractFormPage] auxiliary form preload skipped', err);
    }
  }
}

async function discardChanges() {
  if (!hasChanges.value || busy.value) return;
  await reload();
}

onErrorCaptured((err) => {
  const message = err instanceof Error ? err.message : String(err || 'unknown render error');
  renderErrorMessage.value = `ContractFormPage render error: ${message}`;
  console.error('[ContractFormPage] render failed', err);
  return false;
});

function confirmActionSafety(action: ContractAction) {
  const safety = action.actionSafety;
  if (!safety || safety.classification !== 'danger' || !safety.requiresConfirm) return true;
  const message = safety.confirmMessage || action.hint || action.label;
  return window.confirm(message);
}

async function ensureSavedBeforeRecordAction() {
  if (!hasChanges.value) return true;
  return saveRecord({ on_success: ['scene_projection'] });
}

function applyClientMode(mode: string, toggle = true) {
  const next = String(mode || '').trim();
  if (!next) return false;
  activeContractMode.value = toggle && activeContractMode.value === next ? '' : next;
  contractModeFeedback.value = '';
  if (!activeContractMode.value) closeContractPromptAction();
  return true;
}

function promptContractActionParams(rule: Record<string, unknown>, providedValues?: Record<string, string>) {
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
    const rawValue = providedValues
      ? String(providedValues[name] || '').trim()
      : window.prompt(`${label}${suffix}`, String(field.default || ''))?.trim() || '';
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
    errorMessage.value = err instanceof Error ? err.message : 'contract action failed';
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
    contractModeFeedback.value = '字段显示设置已调整，保存后生效';
    return;
  }
  const raw = payload.action.raw;
  if (!raw) return;
  await runContractRuleAction(raw);
}

function onFieldVisibilityDraftChange(fieldKey: string, value: string) {
  fieldVisibilityDraft[fieldKey] = value === 'show';
  fieldVisibilityDirty.value = true;
  contractModeFeedback.value = '字段显示设置已调整，保存后生效';
}

function onFormSettingsFieldSelect(payload: { field: FormSectionFieldSchema; groupTitle: string }) {
  if (!isContractFieldOrderEditable.value) return;
  const fieldKey = String(payload.field.name || payload.field.key || '').trim();
  if (!fieldKey) return;
  if (!Object.prototype.hasOwnProperty.call(fieldVisibilityBase.value, fieldKey)) {
    const row = activeContractModeFieldRows.value.find((item) => item.fieldKey === fieldKey);
    const checkedAction = row?.actions.find((action) => Boolean(action.checked));
    if (checkedAction) {
      fieldVisibilityBase.value = {
        ...fieldVisibilityBase.value,
        [fieldKey]: checkedAction.value === 'show',
      };
    }
  }
  selectedFormSettingsFieldKey.value = fieldKey;
  selectedFormSettingsFieldGroupTitleDraft.value = String(payload.groupTitle || '').trim();
  formSettingsActiveTab.value = 'fields';
}

function canMoveSelectedFormSettingsField(delta: number) {
  const fieldKey = selectedFormSettingsFieldKey.value;
  if (!fieldKey) return false;
  const index = fieldOrderDraft.value.indexOf(fieldKey);
  if (index < 0) return false;
  const nextIndex = index + delta;
  return nextIndex >= 0 && nextIndex < fieldOrderDraft.value.length;
}

function moveSelectedFormSettingsField(delta: number) {
  const fieldKey = selectedFormSettingsFieldKey.value;
  if (!fieldKey || !canMoveSelectedFormSettingsField(delta)) return;
  moveFieldOrder(fieldKey, delta);
}

function addFieldAfterSelectedFormSettingsField() {
  const fieldKey = selectedFormSettingsFieldKey.value;
  if (!fieldKey) return;
  openInlineCustomFieldCreate(selectedFormSettingsFieldGroupTitle.value || '业务配置字段', fieldKey);
}

function onSelectedFormSettingsFieldVisibilityChange(value: string) {
  const fieldKey = selectedFormSettingsFieldKey.value;
  if (!fieldKey) return;
  onFieldVisibilityDraftChange(fieldKey, value);
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
  onFieldOrderDragStart(fieldKey, payload.event);
}

function onContractInlineFieldOrderDragOver(payload: { field: FormSectionFieldSchema }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  onFieldOrderDragOver(fieldKey);
}

function onContractInlineFieldOrderDragLeave(payload: { field: FormSectionFieldSchema }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  onFieldOrderDragLeave(fieldKey);
}

function onContractInlineFieldOrderDrop(payload: { field: FormSectionFieldSchema }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  onFieldOrderDrop(fieldKey);
}

function onContractInlineFieldOrderDragEnd() {
  onFieldOrderDragEnd();
}

function lowCodeApplyBaseParams() {
  const configAction = contractV2ActionRules().find((rule) => ruleKey(rule) === 'current_form_field_order_save');
  const target = parseMaybeJsonRecord(configAction?.target);
  return normalizeLowCodeApplyParams({
    model: String(model.value || ''),
    ...parseMaybeJsonRecord(target.params),
  });
}

function contractFieldSequence(fieldKey: string, fallback = 100) {
  const index = fieldOrderDraft.value.indexOf(fieldKey);
  return index >= 0 ? (index + 1) * 10 : fallback;
}

async function setInlineFieldPolicy(fieldKey: string, params: Record<string, unknown>) {
  const base = lowCodeApplyBaseParams();
  if (!fieldKey || busy.value) return;
  busyKind.value = 'action';
  try {
    await intentRequest({
      intent: 'ui.form_field_policy.set',
      params: {
        ...base,
        field_name: fieldKey,
        sequence: contractFieldSequence(fieldKey),
        ...params,
      },
      context: { view: 'form' },
    });
    contractModeFeedback.value = '字段配置已更新';
    await reload();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'field policy update failed';
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

async function onContractInlineGroupRename(payload: { oldTitle: string; newTitle: string }) {
  const oldTitle = String(payload.oldTitle || '').trim();
  const newTitle = String(payload.newTitle || '').trim();
  if (!oldTitle || !newTitle || oldTitle === newTitle || busy.value) return;
  const fields = fieldsInNativeGroup(oldTitle);
  if (!fields.length) return;
  busyKind.value = 'action';
  try {
    const base = lowCodeApplyBaseParams();
    for (const row of fields) {
      await intentRequest({
        intent: 'ui.form_field_policy.set',
        params: {
          ...base,
          field_name: row.fieldKey,
          label: row.label || row.fieldKey,
          group_title: newTitle,
          sequence: contractFieldSequence(row.fieldKey),
        },
        context: { view: 'form' },
      });
    }
    contractModeFeedback.value = '区域名称已更新';
    await reload();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'group rename failed';
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
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
      intent: 'ui.form_custom_field.create',
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
    closeInlineCustomFieldCreate();
    await reload();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'custom field create failed';
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

function onFieldOrderDragStart(fieldKey: string, event?: DragEvent) {
  if (!isContractFieldOrderEditable.value) return;
  draggingFieldKey.value = fieldKey;
  dropTargetFieldKey.value = '';
  if (event?.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', fieldKey);
  }
}

function onFieldOrderDragOver(fieldKey: string) {
  if (!isContractFieldOrderEditable.value || !draggingFieldKey.value || draggingFieldKey.value === fieldKey) return;
  dropTargetFieldKey.value = fieldKey;
}

function onFieldOrderDragLeave(fieldKey: string) {
  if (dropTargetFieldKey.value === fieldKey) dropTargetFieldKey.value = '';
}

function onFieldOrderDrop(targetFieldKey: string) {
  if (!isContractFieldOrderEditable.value || !draggingFieldKey.value || draggingFieldKey.value === targetFieldKey) return;
  moveFieldOrderTo(draggingFieldKey.value, targetFieldKey);
  dropTargetFieldKey.value = '';
}

function moveFieldOrderTo(sourceFieldKey: string, targetFieldKey: string) {
  ensureFieldOrderDraftStartsFromCurrentLayout();
  const draft = [...fieldOrderDraft.value];
  const from = draft.indexOf(sourceFieldKey);
  const to = draft.indexOf(targetFieldKey);
  if (from < 0 || to < 0) return;
  const [moved] = draft.splice(from, 1);
  draft.splice(to, 0, moved);
  fieldOrderDraft.value = draft;
  fieldOrderPreviewActive.value = true;
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
}

function onFieldOrderDragEnd() {
  draggingFieldKey.value = '';
  dropTargetFieldKey.value = '';
}

function resetContractFieldOrder() {
  fieldOrderDraft.value = contractModeBaseFieldRows.value.map((row) => row.fieldKey);
  fieldOrderPreviewActive.value = false;
  contractModeBaseFieldRows.value.forEach((row) => {
    if (Object.prototype.hasOwnProperty.call(fieldVisibilityBase.value, row.fieldKey)) {
      fieldVisibilityDraft[row.fieldKey] = fieldVisibilityBase.value[row.fieldKey];
      return;
    }
    const selected = row.actions.find((action) => Boolean(action.checked));
    if (selected) fieldVisibilityDraft[row.fieldKey] = selected.value === 'show';
  });
  fieldVisibilityDirty.value = false;
  contractModeFeedback.value = '';
}

async function saveContractFieldOrder() {
  if (!hasCurrentFormFieldDraftChanges.value) return;
  const configAction = contractV2ActionRules().find((rule) => ruleKey(rule) === 'current_form_field_order_save');
  const target = parseMaybeJsonRecord(configAction?.target);
  const baseParams = normalizeLowCodeApplyParams(parseMaybeJsonRecord(target.params));
  busyKind.value = 'action';
  try {
    await intentRequest({
      intent: 'ui.business_config.lowcode.apply',
      params: {
        ...baseParams,
        field_order: [...fieldOrderDraft.value],
        field_visibility: { ...fieldVisibilityDraft },
      },
      context: { view: 'form' },
    });
    const saveResult = await intentRequest<{
      precheck?: { warnings?: string[]; errors?: string[] }
    }>({
      intent: 'ui.business_config.contract.save',
      params: {
        ...baseParams,
        name: lowCodeScopedContractName(String(model.value || 'unknown'), baseParams),
        model: String(model.value || ''),
        view_type: 'form',
        publish: false,
        contract_json: {
          objects: buildLowCodeContractObjects(),
          layout: {
            form: lowCodeLayoutDraft.value.filter((row) => row.section === 'form').map((row) => ({ object: row.object, field: row.field })),
            list: lowCodeLayoutDraft.value.filter((row) => row.section === 'list').map((row) => ({ object: row.object, field: row.field })),
            kanban: lowCodeLayoutDraft.value.filter((row) => row.section === 'kanban').map((row) => ({ object: row.object, field: row.field })),
          },
          view_orchestration: buildLowCodeViewOrchestration(),
          rules: lowCodeRulesDraft.value.map((rule) => ({
            name: rule.name,
            trigger: rule.trigger,
            cron: rule.trigger === 'scheduled' ? (rule.cron || '') : '',
            action: { object: rule.object, field: rule.field },
          })),
        },
      },
    });
    const warnings = Array.isArray(saveResult?.precheck?.warnings) ? saveResult.precheck?.warnings || [] : [];
    lowCodePrecheckWarnings.value = warnings.map((item) => String(item || '').trim()).filter(Boolean);
    fieldVisibilityDirty.value = false;
    contractModeFeedback.value = '表单设置已保存';
    await reload();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'field order update failed';
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

async function runAction(action: ContractAction) {
  if (!action.enabled) return;
  if (!confirmActionSafety(action)) return;
  if (action.intent === 'ui.local_mode' || action.intent === 'ui.mode' || action.clientMode) {
    applyClientMode(action.clientMode, true);
    return;
  }
  const actionKey = String(action.key || '').trim().toLowerCase();
  if (actionKey === 'submit_intake' || actionKey === 'save_draft') {
    await saveRecord(action.refreshPolicy);
    return;
  }
  if (actionKey === 'cancel') {
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
    errorMessage.value = 'contract open action missing action_id';
    status.value = 'error';
    return;
  }
  if (action.mutation) {
    const params = collectActionParams(action);
    if (params === null) return;
    busyKind.value = 'action';
    try {
      const result = await executeSceneMutation({
        mutation: action.mutation,
        actionKey: action.key,
        recordId: recordId.value,
        model: action.targetModel || model.value,
        context: action.context,
        params,
      });
      if (showHud.value) {
        // eslint-disable-next-line no-console
        console.info(`[scene-mutation] intent=${result.intent} trace=${result.traceId} action=${action.key}`);
      }
      await applyProjectionRefreshPolicy(action.refreshPolicy);
      return;
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : 'scene mutation execute failed';
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
      const refresh = result?.type;
      if (refresh === 'refresh' && !action.refreshPolicy) {
        await reload();
        return;
      }
      if (result?.entry_target) {
        await router.push(buildEntryTargetRouteTarget(result.entry_target, {
          query: pickContractNavQuery(route.query as Record<string, unknown>),
          actionId: result.action_id,
        }) as never);
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
          query: pickContractNavQuery(route.query as Record<string, unknown>, { action_id: nextActionId }),
        });
        if (action.refreshPolicy) {
          await applyProjectionRefreshPolicy(action.refreshPolicy);
        }
        return;
      }
      if (action.refreshPolicy) {
        await applyProjectionRefreshPolicy(action.refreshPolicy);
      } else {
        await reload();
      }
      return;
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : 'action execute failed';
      status.value = 'error';
    } finally {
      busyKind.value = null;
    }
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

async function saveRecord(refreshPolicy?: ContractAction['refreshPolicy']): Promise<boolean> {
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
  if (!standardCreateMode) {
    const issues = validateContractFormData({
      contract: contract.value,
      fieldLabels: labels,
      values: editableMap,
    });
    const policyIssues = collectPolicyValidationErrors(contract.value, {
      ...policyContext.value,
      submittedFields: new Set(Object.keys(editableMap)),
    });
    if (policyIssues.length) {
      validationErrors.value = Array.from(new Set(policyIssues)).slice(0, 5);
      submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
      return false;
    }
    if (issues.length) {
      validationErrors.value = Array.from(new Set(issues.map((item) => item.message))).slice(0, 5);
      submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
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
      await router.replace({
        name: 'model-form',
        params: { model: model.value, id: String(created.id) },
        query: pickContractNavQuery(route.query as Record<string, unknown>),
      });
      return true;
    }
  } catch (err) {
    const fallback = recordId.value ? '保存失败，请检查填写内容' : '创建失败，请检查填写内容';
    const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, fallback);
    validationErrors.value = [message];
    submissionFeedback.value = { kind: 'error', message: fallback };
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
  () => `${String(route.params.model || '')}|${String(route.params.id || '')}|${String(route.query.action_id || '')}`,
  () => {
    void reload();
  },
  { immediate: true },
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
  void router.replace({
    path: '/s/projects.list',
    query: {
      ...resolveWorkspaceContextQuery(),
      ...(selectedProjectId > 0 ? { project_id: String(selectedProjectId) } : {}),
    },
  });
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

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener(PROJECT_CONTEXT_CHANGED_EVENT, handleProjectContextChanged);
  }
  if (typeof document !== 'undefined') {
    document.addEventListener('keydown', onRelationDialogDocumentKeydown);
  }
});

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener(PROJECT_CONTEXT_CHANGED_EVENT, handleProjectContextChanged);
  }
  if (typeof document !== 'undefined') {
    document.removeEventListener('keydown', onRelationDialogDocumentKeydown);
  }
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
  border-radius: 8px;
  padding: 18px;
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
  border-radius: 10px;
  padding: 10px;
  margin-bottom: 10px;
  background: var(--sc-app-muted-bg);
  min-width: 0;
}

.block.warn {
  border-color: var(--sc-app-warning-border);
  background: var(--sc-app-warning-bg);
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

.form-grid {
  display: grid;
  gap: 14px;
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
  gap: 10px;
  margin-bottom: 10px;
  padding-bottom: 10px;
}

.contract-form-native-shell :deep(.template-page-header-main) {
  min-width: 90px;
  max-width: 140px;
}

.contract-form-native-shell :deep(.template-page-header-main h1) {
  color: var(--sc-app-text-secondary);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.25;
  overflow-wrap: anywhere;
}

.contract-form-native-shell :deep(.template-page-header-status) {
  flex: 1 1 auto;
  min-width: 0;
  margin-left: 0;
  padding-top: 0;
}

.contract-form-native-shell :deep(.template-page-header-actions) {
  flex: 0 0 auto;
}

.native-statusbar--header .native-statusbar-step {
  min-width: 78px;
  min-height: 36px;
  padding: 0 14px;
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
  gap: 12px;
  padding: 12px 0 0;
}

.contract-form-settings-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
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

.contract-form-settings-tabs {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel-muted);
}

.contract-form-settings-tab {
  min-height: 30px;
  padding: 0 10px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  cursor: pointer;
}

.contract-form-settings-tab--active {
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  box-shadow: 0 1px 2px rgb(15 23 42 / 8%);
}

.contract-form-settings-scope {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 8px;
  margin: 0;
}

.contract-form-settings-scope > div {
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel-muted);
}

.contract-form-settings-scope dt {
  margin: 0 0 3px;
  color: var(--sc-app-text-secondary);
  font-size: 11px;
}

.contract-form-settings-scope dd {
  margin: 0;
  color: var(--sc-app-text-primary);
  font-size: 12px;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.contract-form-settings-section-head,
.contract-form-settings-placeholder {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.contract-form-settings-section-head strong,
.contract-form-settings-placeholder strong {
  color: var(--sc-app-text-primary);
  font-size: 13px;
}

.contract-form-settings-fields {
  display: grid;
  gap: 8px;
}

.contract-field-selection-panel {
  display: grid;
  gap: 8px;
}

.contract-field-selection-card,
.contract-field-selection-empty {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  min-width: 0;
  padding: 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
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
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}

.contract-field-selection-order-btn {
  width: 30px;
  height: 30px;
  padding: 0;
  display: inline-grid;
  place-items: center;
  line-height: 1;
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

.contract-field-governance-footer {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.contract-field-governance-dirty {
  margin-right: auto;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
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

.contract-lowcode-objects {
  grid-column: 1 / -1;
  margin-top: 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  padding: 10px;
}

.contract-lowcode-objects-head,
.contract-lowcode-object-head,
.contract-lowcode-field {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.contract-lowcode-contract-switch {
  min-width: 260px;
}

.contract-lowcode-flag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.contract-lowcode-object {
  padding: 8px;
  border: 1px dashed var(--sc-app-border);
  border-radius: 6px;
  margin-top: 8px;
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
