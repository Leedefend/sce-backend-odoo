<template>
  <main class="page">
    <header class="header">
      <div>
        <h1>{{ pageTitle }}</h1>
        <p v-if="showHud" class="meta">model={{ model }} · id={{ recordIdDisplay }} · action={{ actionId || '-' }}</p>
        <p v-if="showHud && contractMetaLine" class="meta">{{ contractMetaLine }}</p>
      </div>
      <div class="actions">
        <button
          v-for="action in headerActions"
          :key="`hdr-${action.key}`"
          :class="action.semantic === 'primary_action' ? 'primary' : 'ghost'"
          :disabled="busy || !action.enabled"
          :title="action.hint"
          @click="runAction(action)"
        >
          {{ action.label }}
        </button>
        <button
          v-if="!hasPrimaryHeaderAction"
          class="primary"
          :disabled="busy || !canSave || (Boolean(recordId) && !hasChanges)"
          @click="saveRecord"
        >
          {{ busy && busyKind === 'save' ? '保存中...' : '保存' }}
        </button>
        <button v-if="showDebugActions" class="ghost" :disabled="busy || !contract" @click="copyContractJson">复制契约</button>
        <button v-if="showDebugActions" class="ghost" :disabled="busy || !contract" @click="exportContractJson">导出契约</button>
        <button v-if="showDebugActions" class="ghost" :disabled="busy" @click="reload">重新加载</button>
      </div>
    </header>

    <StatusPanel v-if="status === 'loading'" title="正在加载页面..." variant="info" />
    <StatusPanel v-else-if="status === 'error'" title="页面加载失败" :message="errorMessage" variant="error" :on-retry="reload" />

    <section v-else class="card">
      <section v-if="warnings.length" class="block warn">
        <h3>提示信息</h3>
        <ul>
          <li v-for="item in warnings" :key="item">{{ item }}</li>
        </ul>
      </section>

      <section v-if="workflowTransitions.length" class="block">
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

      <section v-if="showSearchFilters && searchFilters.length" class="block">
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
        <p v-if="validationErrors.length" class="validation-error">
          {{ validationErrors.join('；') }}
        </p>
        <p v-if="onchangeWarnings.length" class="validation-warn">
          {{ onchangeWarnings.map((item) => item.message || item.title || '').filter(Boolean).join('；') }}
        </p>
        <div v-if="coreFieldsLabel" class="layout-divider">{{ coreFieldsLabel }}</div>
        <template v-for="node in layoutNodes" :key="node.key">
          <div v-if="showHud && node.kind === 'header'" class="layout-divider">头部</div>
          <div v-else-if="showHud && node.kind === 'sheet'" class="layout-divider">主体</div>
          <div v-else-if="node.kind === 'field' && isFieldVisible(node.name)" class="field">
            <label class="label">{{ node.label }}<span v-if="shouldShowRequiredMark(node)" class="required">*</span></label>
            <template v-if="node.readonly">
              <FieldValue :value="formData[node.name]" :field="node.descriptor" />
            </template>
            <template v-else>
              <input
                v-if="fieldType(node.descriptor) === 'boolean'"
                :checked="Boolean(formData[node.name])"
                class="input-checkbox"
                type="checkbox"
                @change="setBooleanField(node.name, ($event.target as HTMLInputElement).checked)"
              />
              <select
                v-else-if="fieldType(node.descriptor) === 'selection'"
                :value="String(formData[node.name] ?? '')"
                class="input"
                @change="setSelectionField(node.name, ($event.target as HTMLSelectElement).value)"
              >
                <option v-if="!node.required" value="">请选择</option>
                <option v-for="option in node.descriptor?.selection || []" :key="option[0]" :value="option[0]">
                  {{ option[1] }}
                </option>
              </select>
              <div v-else-if="fieldType(node.descriptor) === 'many2one'" class="relation-editor">
                <select
                  class="input"
                  :value="many2oneValue(node.name)"
                  @change="setMany2oneField(node.name, node.descriptor, ($event.target as HTMLSelectElement).value)"
                >
                  <option value="">请选择</option>
                  <option
                    v-for="option in relationOptionsForField(node.name, node.descriptor)"
                    :key="`${node.name}-${option.id}`"
                    :value="String(option.id)"
                  >
                    {{ option.label }}
                  </option>
                  <option v-if="relationCreateMode(node.name, node.descriptor) !== 'none'" :value="MANY2ONE_CREATE_OPTION">
                    {{ relationCreateMode(node.name, node.descriptor) === 'page' ? '+ 新建并维护...' : '+ 快速新建...' }}
                  </option>
                </select>
              </div>
              <div v-else-if="fieldType(node.descriptor) === 'many2many'" class="relation-editor">
                <input
                  class="input relation-search"
                  type="text"
                  :value="relationKeyword(node.name)"
                  placeholder="搜索并多选..."
                  @input="setRelationKeyword(node.name, ($event.target as HTMLInputElement).value)"
                />
                <select
                  class="input"
                  multiple
                  size="6"
                  :value="relationIds(node.name).map((id) => String(id))"
                  @change="setRelationMultiField(node.name, $event.target as HTMLSelectElement)"
                >
                  <option
                    v-for="option in filteredRelationOptions(node.name, node.descriptor)"
                    :key="`${node.name}-${option.id}`"
                    :value="String(option.id)"
                  >
                    {{ option.label }}
                  </option>
                </select>
              </div>
              <div v-else-if="fieldType(node.descriptor) === 'one2many'" class="relation-editor">
                <div class="o2m-toolbar">
                  <button class="chip-btn" type="button" :disabled="busy" @click="addOne2manyRow(node.name)">+ 新增行</button>
                  <span v-if="one2manySummary(node.name)" class="o2m-summary">{{ one2manySummary(node.name) }}</span>
                </div>
                <div class="o2m-list">
                  <div v-for="row in visibleOne2manyRows(node.name)" :key="row.key" class="o2m-row">
                    <p class="o2m-row-state">{{ one2manyRowStateLabel(row) }}</p>
                    <div class="o2m-fields">
                      <label
                        v-for="column in one2manyColumns(node.name)"
                        :key="`${row.key}-${column.name}`"
                        class="o2m-field"
                      >
                        <span class="meta">{{ column.label }}<span v-if="column.required" class="required">*</span></span>
                        <input
                          v-if="column.ttype === 'boolean'"
                          class="input-checkbox"
                          type="checkbox"
                          :checked="Boolean(row.values[column.name])"
                          @change="setOne2manyRowField(node.name, row.key, column, ($event.target as HTMLInputElement).checked)"
                        />
                        <select
                          v-else-if="column.ttype === 'selection'"
                          class="input"
                          :value="String(row.values[column.name] ?? '')"
                          @change="setOne2manyRowField(node.name, row.key, column, ($event.target as HTMLSelectElement).value)"
                        >
                          <option value="">请选择</option>
                          <option v-for="option in column.selection || []" :key="String(option[0])" :value="String(option[0])">
                            {{ String(option[1]) }}
                          </option>
                        </select>
                        <input
                          v-else
                          class="input"
                          :type="one2manyColumnInputType(column)"
                          :value="one2manyColumnDisplayValue(column, row.values[column.name])"
                          :placeholder="column.label"
                          @input="setOne2manyRowField(node.name, row.key, column, ($event.target as HTMLInputElement).value)"
                        />
                      </label>
                    </div>
                    <button class="ghost" type="button" :disabled="busy" @click="removeOne2manyRow(node.name, row.key)">移除</button>
                    <p v-if="showOne2manyErrors && one2manyRowErrors(node.name, row.key).length" class="o2m-row-error">
                      {{ one2manyRowErrors(node.name, row.key).join('；') }}
                    </p>
                  </div>
                </div>
                <div v-if="removedOne2manyRows(node.name).length" class="o2m-removed">
                  <p class="meta">已移除 {{ removedOne2manyRows(node.name).length }} 行</p>
                  <div class="chips">
                    <button
                      v-for="row in removedOne2manyRows(node.name)"
                      :key="`rm-${row.key}`"
                      class="chip-btn"
                      type="button"
                      :disabled="busy"
                      @click="restoreOne2manyRow(node.name, row.key)"
                    >
                      撤销移除 · {{ one2manyRowLabel(node.name, row) }} · 待删除
                    </button>
                  </div>
                </div>
              </div>
              <input
                v-else
                :value="String(formData[node.name] ?? '')"
                class="input"
                :type="fieldInputType(fieldType(node.descriptor))"
                @input="setTextField(node.name, ($event.target as HTMLInputElement).value)"
              />
            </template>
          </div>
        </template>
        <div v-if="hasAdvancedFields" class="layout-divider advanced-toggle">
          <button class="chip-btn" :disabled="busy" @click="advancedExpanded = !advancedExpanded">
            {{ advancedExpanded ? '收起高级信息' : '展开高级信息' }}
          </button>
        </div>
      </section>

      <section v-if="bodyActions.length" class="block">
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
    </section>

    <DevContextPanel
      :visible="showHud"
      title="表单上下文"
      :entries="hudEntries"
    />
  </main>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import FieldValue from '../components/FieldValue.vue';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import { isHudEnabled } from '../config/debug';
import { loadActionContractRaw, loadModelContractRaw } from '../api/contract';
import { createRecord, listRecords, readRecord, writeRecord } from '../api/data';
import { executeButton } from '../api/executeButton';
import { triggerOnchange } from '../api/onchange';
import type { ActionContract, FieldDescriptor } from '@sc/schema';
import { useSessionStore } from '../stores/session';
import {
  detectObjectMethodFromActionKey,
  normalizeActionKind,
  parseMaybeJsonRecord,
  toPositiveInt,
} from '../app/contractRuntime';
import { validateContractFormData } from '../app/contractValidation';
import { resolveActionIdFromContext } from '../app/actionContext';
import { pickContractNavQuery } from '../app/navigationContext';
import { collectPolicyValidationErrors, evaluateActionPolicy, evaluateFieldPolicy } from '../app/contractPolicies';
import { buildRuntimeFieldStates } from '../app/modifierEngine';
import { buildOne2ManyInlineCommands, buildX2ManyCommands, extractX2ManyIds } from '../app/x2manyCommands';

type UiStatus = 'loading' | 'ok' | 'error';
type BusyKind = 'save' | 'action' | null;
const MANY2ONE_CREATE_OPTION = '__create__';

type ContractAction = {
  key: string;
  label: string;
  kind: string;
  level: string;
  actionId: number | null;
  methodName: string;
  targetModel: string;
  context: Record<string, unknown>;
  domainRaw: string;
  target: string;
  url: string;
  enabled: boolean;
  hint: string;
  semantic: string;
  visibleProfiles: Array<'create' | 'edit' | 'readonly'>;
};

type LayoutNode = {
  key: string;
  kind: 'header' | 'sheet' | 'field';
  name: string;
  label: string;
  readonly: boolean;
  required: boolean;
  descriptor?: FieldDescriptor;
};

type RelationOption = {
  id: number;
  label: string;
};

type One2ManyInlineRow = {
  key: string;
  id: number | null;
  isNew: boolean;
  removed: boolean;
  dirty: boolean;
  values: Record<string, unknown>;
};

type One2ManyColumn = {
  name: string;
  label: string;
  ttype: string;
  required: boolean;
  selection?: Array<[string, string]>;
};

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const status = ref<UiStatus>('loading');
const errorMessage = ref('');
const validationErrors = ref<string[]>([]);
const showOne2manyErrors = ref(false);
const busyKind = ref<BusyKind>(null);
const contract = ref<ActionContract | null>(null);
const contractMeta = ref<Record<string, unknown> | null>(null);
const activeFilterKey = ref('');
const originalValues = ref<Record<string, unknown>>({});
const formData = reactive<Record<string, unknown>>({});
const advancedExpanded = ref(false);
const relationOptions = ref<Record<string, RelationOption[]>>({});
const relationFieldDescriptors = ref<Record<string, Record<string, FieldDescriptor>>>({});
const relationKeywords = reactive<Record<string, string>>({});
const one2manyRows = reactive<Record<string, One2ManyInlineRow[]>>({});
const relationQueryTimers: Record<string, ReturnType<typeof setTimeout>> = {};
const onchangeModifiersPatch = ref<Record<string, Record<string, unknown>>>({});
const onchangeWarnings = ref<Array<{ title?: string; message?: string }>>([]);
const changedFieldSet = new Set<string>();
let onchangeTimer: ReturnType<typeof setTimeout> | null = null;
const applyingOnchangePatch = ref(false);

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
const busy = computed(() => busyKind.value !== null);

const renderProfile = computed<'create' | 'edit' | 'readonly'>(() => {
  const profile = String(contract.value?.render_profile || '').trim().toLowerCase();
  if (profile === 'readonly') return 'readonly';
  if (profile === 'edit') return 'edit';
  if (profile === 'create') return 'create';
  if (!canSave.value) return 'readonly';
  return recordId.value ? 'edit' : 'create';
});

const rights = computed(() => {
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
    write: resolve('write'),
    create: resolve('create'),
    unlink: resolve('unlink'),
  };
});

const canSave = computed(() => (recordId.value ? rights.value.write : rights.value.create));
const hasChanges = computed(() => {
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
  Object.keys(formData).filter((key) => isFieldWritable(key) && comparableFieldValue(key, formData[key]) !== comparableFieldValue(key, originalValues.value[key])).length,
);

const one2manyValidation = computed(() => collectOne2manyDraftValidation());

const pageTitle = computed(() => {
  const title = String(contract.value?.head?.title || '').trim();
  if (title) return title;
  return model.value ? `业务表单 · ${model.value}` : '业务表单';
});

const contractMetaLine = computed(() => {
  if (!contract.value) return '';
  const mode = String(contractMeta.value?.contract_mode || '-');
  const viewType = String(contract.value.head?.view_type || contract.value.view_type || '-');
  const filters = Array.isArray(contract.value.search?.filters) ? contract.value.search.filters.length : 0;
  const transitions = Array.isArray(contract.value.workflow?.transitions) ? contract.value.workflow.transitions.length : 0;
  return `mode=${mode} · view_type=${viewType} · profile=${renderProfile.value} · filters=${filters} · transitions=${transitions} · rights=${rights.value.read ? 'R' : '-'}${rights.value.write ? 'W' : '-'}${rights.value.create ? 'C' : '-'}${rights.value.unlink ? 'D' : '-'}`;
});

const showDebugActions = computed(() => showHud.value && renderProfile.value !== 'create');
const runtimeUserGroups = computed(() => {
  const out = new Set<string>();
  (session.user?.groups_xmlids || []).forEach((group) => {
    const normalized = String(group || '').trim();
    if (normalized) out.add(normalized);
  });
  return out;
});
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
    .filter(Boolean);
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
  if (!contract.value) return true;
  if (renderProfile.value !== 'create') return true;
  return !Boolean(contract.value.hide_filters_on_create);
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

function many2oneValue(name: string) {
  const ids = relationIds(name);
  return ids.length ? String(ids[0]) : '';
}

function relationOptionsForField(name: string, descriptor?: FieldDescriptor) {
  const rows = relationOptions.value[name];
  if (Array.isArray(rows) && rows.length) return rows;
  const ids = relationIds(name);
  if (!ids.length) return [];
  return ids.map((id) => ({ id, label: `#${id}` }));
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

function one2manyColumns(name: string): One2ManyColumn[] {
  const subviews = (contract.value?.views?.form as Record<string, unknown> | undefined)?.subviews;
  const fieldSubview = subviews && typeof subviews === 'object'
    ? (subviews as Record<string, unknown>)[name]
    : undefined;
  const tree = fieldSubview && typeof fieldSubview === 'object'
    ? (fieldSubview as Record<string, unknown>).tree
    : undefined;
  const columnsRaw = tree && typeof tree === 'object'
    ? (tree as Record<string, unknown>).columns
    : undefined;
  const out: One2ManyColumn[] = [];
  if (Array.isArray(columnsRaw)) {
    columnsRaw.forEach((item) => {
      if (typeof item === 'string') {
        const normalized = item.trim();
        if (!normalized || normalized === 'id') return;
        const descriptor = one2manyRelationFieldDescriptor(name, normalized);
        out.push({
          name: normalized,
          label: String(descriptor?.string || normalized),
          ttype: fieldType(descriptor) || 'char',
          required: Boolean(descriptor?.required),
          selection: Array.isArray(descriptor?.selection) ? descriptor?.selection : undefined,
        });
        return;
      }
      if (!item || typeof item !== 'object') return;
      const row = item as Record<string, unknown>;
      const colName = String(row.name || '').trim();
      if (!colName || colName === 'id') return;
      const descriptor = one2manyRelationFieldDescriptor(name, colName);
      out.push({
        name: colName,
        label: String(row.label || row.string || descriptor?.string || colName).trim() || colName,
        ttype: fieldType(descriptor) || 'char',
        required: Boolean(descriptor?.required),
        selection: Array.isArray(descriptor?.selection) ? descriptor?.selection : undefined,
      });
    });
  }
  if (!out.length) {
    const descriptor = one2manyRelationFieldDescriptor(name, 'name');
    return [{
      name: 'name',
      label: String(descriptor?.string || '名称'),
      ttype: fieldType(descriptor) || 'char',
      required: Boolean(descriptor?.required),
      selection: Array.isArray(descriptor?.selection) ? descriptor?.selection : undefined,
    }];
  }
  return out.slice(0, 4);
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
  const rows = ensureOne2manyRows(fieldName);
  const row = rows.find((item) => item.key === rowKey);
  if (!row) return;
  const normalized = normalizeOne2manyColumnValue(column, value);
  row.values = {
    ...(row.values || {}),
    [column.name]: normalized,
  };
  row.dirty = true;
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
    values: {
      [primary]: optionMap.get(id) || `#${id}`,
      name: optionMap.get(id) || `#${id}`,
    },
  }));
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
      values: row.values || {},
    })),
    mode,
  });
}

function collectOne2manyDraftValidation() {
  const issues: string[] = [];
  const rowErrors: Record<string, string[]> = {};
  Object.entries(one2manyRows).forEach(([fieldName, rows]) => {
    if (!Array.isArray(rows) || !rows.length) return;
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

function setRelationKeyword(name: string, keyword: string) {
  relationKeywords[name] = keyword;
  if (relationQueryTimers[name]) {
    clearTimeout(relationQueryTimers[name]);
  }
  relationQueryTimers[name] = setTimeout(() => {
    void queryRelationOptions(name, relationKeywords[name] || '');
  }, 260);
}

function filteredRelationOptions(name: string, descriptor?: FieldDescriptor) {
  const rows = relationOptionsForField(name, descriptor);
  const kw = relationKeyword(name).trim().toLowerCase();
  if (!kw) return rows;
  return rows.filter((row) => row.label.toLowerCase().includes(kw) || String(row.id).includes(kw));
}

function relationModel(name: string) {
  const descriptor = contract.value?.fields?.[name] as Record<string, unknown> | undefined;
  return String(descriptor?.relation || '').trim();
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
  return {
    model: String(row.model || '').trim(),
    actionId,
    menuId,
    canCreate: Boolean(row.can_create),
    createMode,
    defaultVals,
    reasonCode: String(row.reason_code || '').trim(),
  };
}

function canOpenRelationCreatePage(fieldName: string, descriptor?: FieldDescriptor) {
  const entry = relationEntry(descriptor);
  return Boolean(entry?.actionId && entry?.createMode === 'page');
}

function relationCreateMode(fieldName: string, descriptor?: FieldDescriptor): 'page' | 'quick' | 'none' {
  const entry = relationEntry(descriptor);
  if (!entry) return 'none';
  if (entry.createMode === 'page' && entry.actionId) return 'page';
  if (entry.createMode === 'quick' && entry.canCreate) return 'quick';
  return 'none';
}

function relationDomain(descriptor?: FieldDescriptor) {
  const entry = relationEntry(descriptor);
  const out: unknown[] = [];
  const type = String(entry?.defaultVals?.type || '').trim();
  if (type) out.push(['type', '=', type]);
  return out.length ? out : undefined;
}

function runtimeRelationDomain(name: string) {
  const raw = (onchangeModifiersPatch.value?.[name] || {}) as Record<string, unknown>;
  const domain = raw.domain;
  if (!Array.isArray(domain)) return [];
  return domain;
}

function mergedRelationDomain(name: string, descriptor?: FieldDescriptor) {
  const base = relationDomain(descriptor);
  const runtime = runtimeRelationDomain(name);
  const out: unknown[] = [];
  if (Array.isArray(base)) out.push(...base);
  if (Array.isArray(runtime)) out.push(...runtime);
  return out.length ? out : undefined;
}

async function queryRelationOptions(name: string, keyword: string) {
  const descriptor = contract.value?.fields?.[name];
  const relation = relationModel(name);
  if (!relation) return;
  const search = String(keyword || '').trim();
  const domain = mergedRelationDomain(name, descriptor);
  try {
    const listed = await listRecords({
      model: relation,
      fields: ['id', 'name', 'display_name'],
      limit: search ? 40 : 80,
      order: 'id desc',
      domain,
      search_term: search || undefined,
    });
    const records = Array.isArray(listed?.records) ? listed.records : [];
    const mapped = records
      .map((row) => {
        const id = Number((row as Record<string, unknown>).id);
        if (!Number.isFinite(id) || id <= 0) return null;
        const label = String(
          (row as Record<string, unknown>).display_name
          || (row as Record<string, unknown>).name
          || `#${id}`,
        ).trim();
        return { id: Math.trunc(id), label };
      })
      .filter((item): item is RelationOption => Boolean(item));
    relationOptions.value = {
      ...relationOptions.value,
      [name]: mapped,
    };
  } catch {
    // keep existing options if remote query fails
  }
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
    validationErrors.value = [`未找到 ${relation} 的新建入口，请联系管理员配置菜单动作`];
    return;
  }
  const entry = relationEntry(descriptor);
  const relationActionId = entry?.actionId || null;
  const menuId = entry?.menuId || 0;
  const quickCreate = async () => {
    const label = String(window.prompt('当前未配置维护页面，请输入新选项名称（快速新建）') || '').trim();
    if (!label) return;
    try {
      const vals: Record<string, unknown> = { ...(entry?.defaultVals || {}), name: label };
      if (relation === 'sc.dictionary' && typeof vals.type === 'string' && String(vals.type || '').trim()) {
        vals.code = label.toUpperCase().replace(/\\s+/g, '_').slice(0, 60);
      }
      const created = await createRecord({ model: relation, vals });
      const id = Number(created?.id || 0);
      if (Number.isFinite(id) && id > 0) {
        formData[fieldName] = Math.trunc(id);
        markFieldChanged(fieldName);
        relationKeywords[fieldName] = label;
        await queryRelationOptions(fieldName, label);
      }
      return;
    } catch (err) {
      const message = err instanceof Error ? err.message : '快速新建失败';
      validationErrors.value = [message];
      return;
    }
  };
  if (!relationActionId && mode === 'quick') {
    await quickCreate();
    return;
  }
  if (!relationActionId) {
    validationErrors.value = [`未找到 ${relation} 的维护页面入口，请联系管理员配置 action/menu`];
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
      await quickCreate();
      return;
    }
    validationErrors.value = [err instanceof Error ? err.message : '跳转新建页面失败'];
  }
}

async function loadRelationOptions() {
  const fields = contract.value?.fields || {};
  const one2manyNames = Object.entries(fields)
    .filter(([, descriptor]) => fieldType(descriptor) === 'one2many')
    .map(([name]) => name);
  await Promise.all(one2manyNames.map((name) => ensureRelationFieldDescriptors(name)));
  const visibleRelationFields = new Set(
    layoutNodes.value
      .filter((node) => node.kind === 'field' && isFieldVisible(node.name))
      .map((node) => node.name),
  );
  const entries = Object.entries(fields).filter(([name]) => {
    if (!visibleRelationFields.size) return true;
    if (visibleRelationFields.has(name)) return true;
    return relationIds(name).length > 0;
  });
  const next: Record<string, RelationOption[]> = {};
  await Promise.all(entries.map(async ([name, descriptor]) => {
    if (!descriptor || typeof descriptor !== 'object') return;
    const type = fieldType(descriptor);
    if (!['many2one', 'many2many', 'one2many'].includes(type)) return;
    const relation = String((descriptor as Record<string, unknown>).relation || '').trim();
    if (!relation) return;
    const domain = mergedRelationDomain(name, descriptor as FieldDescriptor);
    try {
      const listed = await listRecords({
        model: relation,
        fields: ['id', 'name', 'display_name'],
        limit: 80,
        order: 'id desc',
        domain,
      });
      const records = Array.isArray(listed?.records) ? listed.records : [];
      next[name] = records
        .map((row) => {
          const id = Number((row as Record<string, unknown>).id);
          if (!Number.isFinite(id) || id <= 0) return null;
          const label = String(
            (row as Record<string, unknown>).display_name
            || (row as Record<string, unknown>).name
            || `#${id}`,
          ).trim();
          return { id: Math.trunc(id), label };
        })
        .filter((item): item is RelationOption => Boolean(item));
    } catch {
      next[name] = [];
    }
  }));
  relationOptions.value = next;
}

function hasGroupAccess(groupsXmlids?: string[]) {
  if (!Array.isArray(groupsXmlids) || !groupsXmlids.length) return true;
  const userGroups = session.user?.groups_xmlids || [];
  return groupsXmlids.some((group) => userGroups.includes(group));
}

function toActionId(raw: unknown) {
  return toPositiveInt(raw);
}

function detectMethodName(key: string, payloadMethod: string) {
  return detectObjectMethodFromActionKey(key, payloadMethod);
}

const contractActions = computed<ContractAction[]>(() => {
  const merged: Array<Record<string, unknown>> = [];
  if (Array.isArray(contract.value?.buttons)) merged.push(...(contract.value?.buttons as Array<Record<string, unknown>>));
  if (Array.isArray(contract.value?.toolbar?.header)) merged.push(...(contract.value?.toolbar?.header as Array<Record<string, unknown>>));
  if (Array.isArray(contract.value?.toolbar?.sidebar)) merged.push(...(contract.value?.toolbar?.sidebar as Array<Record<string, unknown>>));
  if (Array.isArray(contract.value?.toolbar?.footer)) merged.push(...(contract.value?.toolbar?.footer as Array<Record<string, unknown>>));

  const dedup = new Set<string>();
  const out: ContractAction[] = [];
  for (const row of merged) {
    const key = String(row.key || '').trim();
    if (!key || dedup.has(key)) continue;
    dedup.add(key);
    const payload = parseMaybeJsonRecord(row.payload);
    const kind = normalizeActionKind(row.kind);
    const level = String(row.level || 'body').trim().toLowerCase();
    const actionId = toActionId(payload.action_id) ?? toActionId(payload.ref);
    const methodName = detectMethodName(key, String(payload.method || '').trim());
    const targetModel = String(row.target_model || row.model || model.value || '').trim();
    const context = parseMaybeJsonRecord(payload.context_raw);
    const domainRaw = String(payload.domain_raw || '').trim();
    const target = String(payload.target || '').trim();
    const groups = Array.isArray(row.groups_xmlids) ? (row.groups_xmlids as string[]) : [];
    const visibleProfiles = (
      Array.isArray(row.visible_profiles) ? row.visible_profiles : ['create', 'edit']
    )
      .map((item) => String(item || '').trim().toLowerCase())
      .filter((item): item is 'create' | 'edit' | 'readonly' => item === 'create' || item === 'edit' || item === 'readonly');
    const policy = evaluateActionPolicy(contract.value, key, policyContext.value);
    if (!policy.visible) continue;
    const byGroup = hasGroupAccess(groups);
    const needRecord = kind === 'object' || kind === 'server' || level === 'row' || level === 'smart';
    const enabled = policy.enabled && byGroup && (!needRecord || Boolean(recordId.value));
    out.push({
      key,
      label: String(row.label || key),
      kind,
      level,
      actionId,
      methodName,
      targetModel,
      context,
      domainRaw,
      target,
      url: String(payload.url || '').trim(),
      enabled,
      hint: byGroup
        ? (needRecord && !recordId.value ? 'requires record id' : policy.reason)
        : 'permission denied',
      semantic: policy.semantic,
      visibleProfiles,
    });
  }
  return out.sort((a, b) => {
    const levelDelta = a.level.localeCompare(b.level);
    if (levelDelta !== 0) return levelDelta;
    return a.label.localeCompare(b.label, 'zh-CN');
  });
});

const headerActions = computed(() => contractActions.value.filter((item) => item.level === 'header' || item.level === 'toolbar'));
const bodyActions = computed(() => contractActions.value.filter((item) => item.level !== 'header' && item.level !== 'toolbar'));
const hasPrimaryHeaderAction = computed(() => headerActions.value.some((item) => item.semantic === 'primary_action'));

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
  return out;
});

const coreFieldNames = computed<string[]>(() => semanticFieldGroups.value.core?.fields || []);
const advancedFieldNames = computed<string[]>(() => semanticFieldGroups.value.advanced?.fields || []);
const coreFieldsLabel = computed(() => semanticFieldGroups.value.core?.label || '');
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
  return out;
});
const contractVisibleFields = computed<string[]>(() => {
  const rows = Array.isArray(contract.value?.visible_fields) ? contract.value?.visible_fields : [];
  return rows.map((name) => String(name || '').trim()).filter(Boolean);
});
const fieldModifierMap = computed<Record<string, Record<string, unknown>>>(() => {
  const formView = (contract.value?.views?.form || {}) as { field_modifiers?: Record<string, Record<string, unknown>> };
  return formView.field_modifiers || {};
});
const runtimeFieldStates = computed(() => {
  const names = Object.keys(contract.value?.fields || {});
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
  const state = runtimeState(name);
  if (state.invisible) return false;
  const visible = contractVisibleFields.value;
  if (visible.length && !visible.includes(name)) return false;
  const core = coreFieldNames.value;
  const advanced = advancedFieldNames.value;
  if (!core.length && !advanced.length) return true;
  if (core.includes(name)) return true;
  if (advanced.includes(name)) return advancedExpanded.value;
  return renderProfile.value !== 'create';
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

const layoutNodes = computed<LayoutNode[]>(() => {
  const fieldMap = contract.value?.fields || {};
  const order = contract.value?.views?.form?.layout || [];
  const fieldGroups = contract.value?.permissions?.field_groups || {};
  const used = new Set<string>();
  const nodes: LayoutNode[] = [];

  for (let i = 0; i < order.length; i += 1) {
    const item = order[i];
    const kind = String(item?.type || '').trim().toLowerCase();
    if (kind === 'header' || kind === 'sheet') {
      nodes.push({ key: `${kind}_${i}`, kind: kind as 'header' | 'sheet', name: '', label: '', readonly: true, required: false });
      continue;
    }
    if (kind !== 'field') continue;
    const name = String(item?.name || '').trim();
    if (!name || used.has(name)) continue;
    const groups = fieldGroups[name]?.groups_xmlids;
    if (!hasGroupAccess(Array.isArray(groups) ? groups : [])) continue;
    used.add(name);
    const descriptor = fieldMap[name];
    if (!descriptor) continue;
    const resolved = evaluateFieldPolicy(
      contract.value,
      name,
      {
        required: Boolean(descriptor?.required),
        readonly: Boolean(descriptor?.readonly),
      },
      policyContext.value,
    );
    if (!resolved.visible) continue;
    const state = runtimeState(name);
    nodes.push({
      key: `field_${name}`,
      kind: 'field',
      name,
      label: String(descriptor?.string || name),
      readonly: Boolean(resolved.readonly || state.readonly || (recordId.value ? !rights.value.write : !rights.value.create)),
      required: Boolean(resolved.required || state.required),
      descriptor,
    });
  }

  Object.entries(fieldMap).forEach(([name, descriptor]) => {
    if (used.has(name)) return;
    const groups = fieldGroups[name]?.groups_xmlids;
    if (!hasGroupAccess(Array.isArray(groups) ? groups : [])) return;
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
    const state = runtimeState(name);
    nodes.push({
      key: `field_${name}`,
      kind: 'field',
      name,
      label: String(descriptor?.string || name),
      readonly: Boolean(resolved.readonly || state.readonly || (recordId.value ? !rights.value.write : !rights.value.create)),
      required: Boolean(resolved.required || state.required),
      descriptor,
    });
  });

  return nodes;
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
      values: row.values || {},
    }));
    return JSON.stringify(rows);
  }
  return normalizeComparable(value);
}

function isFieldWritable(name: string) {
  const node = layoutNodes.value.find((item) => item.kind === 'field' && item.name === name);
  return Boolean(node && !node.readonly);
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

function setBooleanField(name: string, checked: boolean) {
  formData[name] = checked;
  markFieldChanged(name);
}

function setMany2oneField(name: string, descriptor: FieldDescriptor | undefined, value: string) {
  const normalized = String(value || '').trim();
  if (!normalized) {
    formData[name] = false;
    markFieldChanged(name);
    return;
  }
  if (normalized === MANY2ONE_CREATE_OPTION) {
    void openRelationCreateForm(name, descriptor);
    return;
  }
  const id = Number(normalized);
  if (!Number.isFinite(id) || id <= 0) {
    formData[name] = false;
    markFieldChanged(name);
    return;
  }
  formData[name] = Math.trunc(id);
  markFieldChanged(name);
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

function setTextField(name: string, value: string) {
  formData[name] = value;
  markFieldChanged(name);
}

function markFieldChanged(name: string) {
  const key = String(name || '').trim();
  if (!key || applyingOnchangePatch.value) return;
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
    const warnings = Array.isArray(response?.warnings) ? response.warnings : [];
    onchangeWarnings.value = warnings;
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
          const ids = normalizeRelationIds(value);
          formData[name] = ids.length ? ids[0] : false;
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
  } catch {
    // Onchange is best-effort; keep current values when roundtrip fails.
  }
}

function collectWritableValues() {
  return layoutNodes.value
    .filter((node) => node.kind === 'field' && !node.readonly)
    .reduce<Record<string, unknown>>((acc, node) => {
      const value = normalizeFieldValue(node.name, formData[node.name]);
      const ttype = fieldType(node.descriptor);
      if ((ttype === 'many2many' || ttype === 'one2many') && Array.isArray(value) && !value.length) {
        return acc;
      }
      acc[node.name] = value;
      return acc;
    }, {});
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

const hudEntries = computed(() => [
  { label: 'model', value: model.value || '-' },
  { label: 'action_id', value: actionId.value || '-' },
  { label: 'record_id', value: recordIdDisplay.value },
  { label: 'contract_loaded', value: Boolean(contract.value) },
  { label: 'contract_view_type', value: contract.value?.head?.view_type || contract.value?.view_type || '-' },
  { label: 'render_profile', value: renderProfile.value },
  { label: 'fields_count', value: Object.keys(contract.value?.fields || {}).length },
  { label: 'layout_nodes', value: layoutNodes.value.length },
  { label: 'writable_fields', value: writableFieldCount.value },
  { label: 'changed_fields', value: changedFieldCount.value },
  { label: 'actions_count', value: contractActions.value.length },
  { label: 'rights', value: `${rights.value.read ? 'R' : '-'}${rights.value.write ? 'W' : '-'}${rights.value.create ? 'C' : '-'}${rights.value.unlink ? 'D' : '-'}` },
  { label: 'onchange_warnings', value: onchangeWarnings.value.length },
]);

async function loadContract() {
  const profile = recordId.value ? 'edit' : 'create';
  const currentModel = String(model.value || '').trim();
  let response: Awaited<ReturnType<typeof loadActionContractRaw>> | null = null;
  if (actionId.value) {
    try {
      response = await loadActionContractRaw(actionId.value, {
        recordId: recordId.value,
        renderProfile: profile,
      });
    } catch {
      response = null;
    }
  }
  if (!response && currentModel) {
    response = await loadModelContractRaw(currentModel, {
      viewType: 'form',
      recordId: recordId.value,
      renderProfile: profile,
    });
  }
  if (!response?.data || typeof response.data !== 'object') {
    throw new Error('empty contract');
  }
  contract.value = response.data as ActionContract;
  contractMeta.value = response.meta || null;
  advancedExpanded.value = renderProfile.value !== 'create';
}

async function loadRecord() {
  const fieldNames = Object.keys(contract.value?.fields || {});
  Object.keys(formData).forEach((key) => {
    delete formData[key];
  });
  Object.keys(relationKeywords).forEach((key) => {
    delete relationKeywords[key];
  });
  Object.keys(one2manyRows).forEach((key) => {
    delete one2manyRows[key];
  });
  onchangeModifiersPatch.value = {};
  onchangeWarnings.value = [];
  changedFieldSet.clear();
  if (onchangeTimer) {
    clearTimeout(onchangeTimer);
    onchangeTimer = null;
  }
  if (!recordId.value) {
    const context = contract.value?.head?.context;
    const defaults: Record<string, unknown> = {};
    Object.entries(route.query as Record<string, unknown>).forEach(([key, value]) => {
      if (key.startsWith('default_')) {
        defaults[key.replace(/^default_/, '')] = normalizeRouteDefault(value);
      }
    });
    if (context && typeof context === 'object' && !Array.isArray(context)) {
      Object.entries(context).forEach(([key, value]) => {
        if (key.startsWith('default_') && !(key.replace(/^default_/, '') in defaults)) {
          defaults[key.replace(/^default_/, '')] = value;
        }
      });
    }
    const validator = contract.value?.validator as Record<string, unknown> | undefined;
    const defaultsSample = validator?.defaults_sample;
    if (defaultsSample && typeof defaultsSample === 'object' && !Array.isArray(defaultsSample)) {
      Object.entries(defaultsSample as Record<string, unknown>).forEach(([key, value]) => {
        if (!(key in defaults)) {
          defaults[key] = value === 'dynamic' ? '' : value;
        }
      });
    }
    fieldNames.forEach((name) => {
      const descriptor = contract.value?.fields?.[name];
      const ttype = fieldType(descriptor);
      const incoming = name in defaults ? defaults[name] : '';
      if (ttype === 'many2many' || ttype === 'one2many') {
        formData[name] = Array.isArray(incoming) ? incoming : [];
        if (ttype === 'one2many') initOne2manyRows(name, formData[name]);
      } else if (ttype === 'many2one') {
        const ids = normalizeRelationIds(incoming);
        formData[name] = ids.length ? ids[0] : false;
        const matched = ids.length
          ? (relationOptions.value[name] || []).find((item) => item.id === ids[0])
          : null;
        relationKeywords[name] = matched?.label || '';
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
    return;
  }
  const read = await readRecord({
    model: model.value,
    ids: [recordId.value],
    fields: fieldNames.length ? fieldNames : '*',
  });
  const row = read.records?.[0] || {};
  fieldNames.forEach((name) => {
    const descriptor = contract.value?.fields?.[name];
    const ttype = fieldType(descriptor);
    const incoming = (row as Record<string, unknown>)[name] ?? '';
    if (ttype === 'many2many' || ttype === 'one2many') {
      formData[name] = Array.isArray(incoming) ? incoming : [];
      if (ttype === 'one2many') initOne2manyRows(name, formData[name]);
    } else if (ttype === 'many2one') {
      const ids = normalizeRelationIds(incoming);
      formData[name] = ids.length ? ids[0] : false;
      const matched = ids.length
        ? (relationOptions.value[name] || []).find((item) => item.id === ids[0])
        : null;
      relationKeywords[name] = matched?.label || '';
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

async function reload() {
  status.value = 'loading';
  errorMessage.value = '';
  validationErrors.value = [];
  showOne2manyErrors.value = false;
  try {
    await loadContract();
    await loadRelationOptions();
    await loadRecord();
    status.value = 'ok';
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'load failed';
    status.value = 'error';
  }
}

async function runAction(action: ContractAction) {
  if (!action.enabled) return;
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
  if ((action.kind === 'object' || action.kind === 'server') && action.methodName && recordId.value) {
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
      if (refresh === 'refresh') {
        await reload();
        return;
      }
      const nextActionId = toPositiveInt(result?.action_id);
      if (nextActionId) {
        await router.push({
          name: 'action',
          params: { actionId: String(nextActionId) },
          query: pickContractNavQuery(route.query as Record<string, unknown>, { action_id: nextActionId }),
        });
      }
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : 'action execute failed';
      status.value = 'error';
    } finally {
      busyKind.value = null;
    }
  }
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

async function saveRecord() {
  if (!canSave.value || !model.value) return;
  validationErrors.value = [];
  const one2manyIssues = one2manyValidation.value.issues;
  if (one2manyIssues.length) {
    showOne2manyErrors.value = true;
    validationErrors.value = one2manyIssues.slice(0, 5);
    return;
  }
  showOne2manyErrors.value = false;
  const editableMap = collectWritableValues();
  const labels = layoutNodes.value.reduce<Record<string, string>>((acc, node) => {
    if (node.kind === 'field') acc[node.name] = node.label || node.name;
    return acc;
  }, {});
  const issues = validateContractFormData({
    contract: contract.value,
    fieldLabels: labels,
    values: editableMap,
  });
  const policyIssues = collectPolicyValidationErrors(contract.value, policyContext.value);
  if (policyIssues.length) {
    validationErrors.value = Array.from(new Set(policyIssues)).slice(0, 5);
    return;
  }
  if (issues.length) {
    validationErrors.value = Array.from(new Set(issues.map((item) => item.message))).slice(0, 5);
    return;
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
      if (comparableFieldValue(key, formData[key]) !== comparableFieldValue(key, originalValues.value[key])) {
        acc[key] = value;
      }
      return acc;
    }, {});
    if (recordId.value && !Object.keys(values).length) {
      busyKind.value = null;
      return;
    }
    if (recordId.value) {
      await writeRecord({ model: model.value, ids: [recordId.value], vals: values });
      await reload();
      return;
    }
    const created = await createRecord({ model: model.value, vals: values });
    if (created?.id) {
      await router.replace({
        name: 'model-form',
        params: { model: model.value, id: String(created.id) },
        query: pickContractNavQuery(route.query as Record<string, unknown>),
      });
      return;
    }
  } finally {
    busyKind.value = null;
  }
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
</script>

<style scoped>
.page {
  display: grid;
  gap: 12px;
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.meta {
  margin: 2px 0;
  color: #64748b;
  font-size: 12px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
  background: #fff;
}

.block {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px;
  margin-bottom: 10px;
  background: #f8fafc;
}

.block.warn {
  border-color: #fdba74;
  background: #fff7ed;
}

.block h3 {
  margin: 0 0 8px;
  font-size: 13px;
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
  border: 1px solid #cbd5e1;
  background: #fff;
}

.chip-btn {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  cursor: pointer;
}

.chip-btn.active {
  border-color: #0f766e;
  box-shadow: inset 0 0 0 1px #0f766e;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 10px;
}

.validation-error {
  grid-column: 1 / -1;
  margin: 0;
  color: #b91c1c;
  font-size: 12px;
}

.validation-warn {
  grid-column: 1 / -1;
  margin: 0;
  color: #92400e;
  font-size: 12px;
}

.layout-divider {
  grid-column: 1 / -1;
  font-size: 12px;
  color: #475569;
  border-bottom: 1px dashed #cbd5e1;
  padding-bottom: 4px;
}

.layout-divider.advanced-toggle {
  display: flex;
  justify-content: flex-start;
  border-bottom: 0;
  padding-bottom: 0;
  margin-top: 2px;
}

.field {
  display: grid;
  gap: 6px;
}

.relation-editor {
  display: grid;
  gap: 6px;
}

.o2m-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.o2m-summary {
  font-size: 12px;
  color: #475569;
}

.o2m-list {
  display: grid;
  gap: 6px;
}

.o2m-row {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) auto;
  gap: 6px;
  align-items: center;
}

.o2m-row-state {
  grid-column: 1 / -1;
  margin: 0;
  font-size: 12px;
  color: #475569;
}

.o2m-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 6px;
}

.o2m-field {
  display: grid;
  gap: 4px;
}

.o2m-removed {
  display: grid;
  gap: 4px;
}

.o2m-row-error {
  grid-column: 1 / -1;
  margin: 0;
  color: #b91c1c;
  font-size: 12px;
}

.relation-search {
  font-size: 12px;
}

.label {
  font-size: 12px;
  color: #334155;
  font-weight: 600;
}

.required {
  color: #b91c1c;
  margin-left: 2px;
}

.input {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 10px;
}

select.input[multiple] {
  min-height: 120px;
}

.input-checkbox {
  width: 18px;
  height: 18px;
}

.ghost,
.primary {
  border-radius: 8px;
  padding: 8px 10px;
  border: 1px solid #cbd5e1;
  background: #fff;
}

.primary {
  background: #111827;
  color: #fff;
  border-color: #111827;
}
</style>
