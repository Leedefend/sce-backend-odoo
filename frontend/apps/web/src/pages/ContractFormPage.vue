<template>
  <main class="page">
    <header class="header">
      <div>
        <h1>{{ pageTitle }}</h1>
        <p class="meta">model={{ model }} · id={{ recordIdDisplay }} · action={{ actionId || '-' }}</p>
        <p v-if="contractMetaLine" class="meta">{{ contractMetaLine }}</p>
      </div>
      <div class="actions">
        <button
          v-for="action in headerActions"
          :key="`hdr-${action.key}`"
          class="ghost"
          :disabled="busy || !action.enabled"
          :title="action.hint"
          @click="runAction(action)"
        >
          {{ action.label }}
        </button>
        <button class="primary" :disabled="busy || !canSave" @click="saveRecord">
          {{ busy && busyKind === 'save' ? 'Saving...' : 'Save' }}
        </button>
        <button class="ghost" :disabled="busy" @click="reload">Reload</button>
      </div>
    </header>

    <StatusPanel v-if="status === 'loading'" title="Loading contract form..." variant="info" />
    <StatusPanel v-else-if="status === 'error'" title="Contract form failed" :message="errorMessage" variant="error" :on-retry="reload" />

    <section v-else class="card">
      <section v-if="warnings.length" class="block warn">
        <h3>Warnings</h3>
        <ul>
          <li v-for="item in warnings" :key="item">{{ item }}</li>
        </ul>
      </section>

      <section v-if="workflowTransitions.length" class="block">
        <h3>Workflow</h3>
        <div class="chips">
          <span v-for="item in workflowTransitions" :key="item.key" class="chip" :title="item.notes || ''">{{ item.label }}</span>
        </div>
      </section>

      <section v-if="searchFilters.length" class="block">
        <h3>Search Filters</h3>
        <div class="chips">
          <button
            v-for="item in searchFilters"
            :key="`flt-${item.key}`"
            class="chip-btn"
            :disabled="busy || !item.key"
            @click="openFilter(item.key)"
          >
            {{ item.label }}
          </button>
        </div>
      </section>

      <section class="form-grid">
        <template v-for="node in layoutNodes" :key="node.key">
          <div v-if="node.kind === 'header'" class="layout-divider">Header</div>
          <div v-else-if="node.kind === 'sheet'" class="layout-divider">Sheet</div>
          <div v-else-if="node.kind === 'field'" class="field">
            <label class="label">{{ node.label }}</label>
            <template v-if="node.readonly">
              <FieldValue :value="formData[node.name]" :field="node.descriptor" />
            </template>
            <template v-else>
              <select
                v-if="node.descriptor?.ttype === 'selection'"
                v-model="formData[node.name]"
                class="input"
              >
                <option v-for="option in node.descriptor?.selection || []" :key="option[0]" :value="option[0]">
                  {{ option[1] }}
                </option>
              </select>
              <input
                v-else
                v-model="formData[node.name]"
                class="input"
                :type="fieldInputType(node.descriptor?.ttype)"
              />
            </template>
          </div>
        </template>
      </section>

      <section v-if="bodyActions.length" class="block">
        <h3>Actions</h3>
        <div class="chips">
          <button
            v-for="action in bodyActions"
            :key="`body-${action.key}`"
            class="chip-btn"
            :disabled="busy || !action.enabled"
            :title="action.hint"
            @click="runAction(action)"
          >
            {{ action.label }} · {{ action.kind }}
          </button>
        </div>
      </section>
    </section>

    <DevContextPanel
      :visible="showHud"
      title="Contract Form HUD"
      :entries="hudEntries"
    />
  </main>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import FieldValue from '../components/FieldValue.vue';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import { isHudEnabled } from '../config/debug';
import { loadActionContractRaw } from '../api/contract';
import { createRecord, readRecord, writeRecord } from '../api/data';
import { executeButton } from '../api/executeButton';
import type { ActionContract, FieldDescriptor } from '@sc/schema';
import { useSessionStore } from '../stores/session';

type UiStatus = 'loading' | 'ok' | 'error';
type BusyKind = 'save' | 'action' | null;

type ContractAction = {
  key: string;
  label: string;
  kind: string;
  level: string;
  actionId: number | null;
  methodName: string;
  enabled: boolean;
  hint: string;
};

type LayoutNode = {
  key: string;
  kind: 'header' | 'sheet' | 'field';
  name: string;
  label: string;
  readonly: boolean;
  descriptor?: FieldDescriptor;
};

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const status = ref<UiStatus>('loading');
const errorMessage = ref('');
const busyKind = ref<BusyKind>(null);
const contract = ref<ActionContract | null>(null);
const contractMeta = ref<Record<string, unknown> | null>(null);
const formData = reactive<Record<string, unknown>>({});

const model = computed(() => String(route.params.model || contract.value?.head?.model || contract.value?.model || ''));
const actionId = computed(() => {
  const raw = route.query.action_id;
  const current = Array.isArray(raw) ? raw[0] : raw;
  const parsed = Number(current || 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
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

const pageTitle = computed(() => {
  const title = String(contract.value?.head?.title || '').trim();
  if (title) return title;
  return `Contract Form · ${model.value || '-'}`;
});

const contractMetaLine = computed(() => {
  if (!contract.value) return '';
  const mode = String(contractMeta.value?.contract_mode || '-');
  const viewType = String(contract.value.head?.view_type || contract.value.view_type || '-');
  const filters = Array.isArray(contract.value.search?.filters) ? contract.value.search.filters.length : 0;
  const transitions = Array.isArray(contract.value.workflow?.transitions) ? contract.value.workflow.transitions.length : 0;
  return `mode=${mode} · view_type=${viewType} · filters=${filters} · transitions=${transitions} · rights=${rights.value.read ? 'R' : '-'}${rights.value.write ? 'W' : '-'}${rights.value.create ? 'C' : '-'}${rights.value.unlink ? 'D' : '-'}`;
});

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
  return rows.map((row, idx) => ({
    key: `wf_${idx}`,
    label: String(row.trigger?.label || row.trigger?.name || `transition_${idx + 1}`),
    notes: String(row.notes || ''),
  }));
});

const searchFilters = computed(() => {
  const rows = contract.value?.search?.filters;
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => ({ key: String(row.key || '').trim(), label: String(row.label || row.key || '').trim() }))
    .filter((row) => row.key && row.label);
});

function hasGroupAccess(groupsXmlids?: string[]) {
  if (!Array.isArray(groupsXmlids) || !groupsXmlids.length) return true;
  const userGroups = session.user?.groups_xmlids || [];
  return groupsXmlids.some((group) => userGroups.includes(group));
}

function toActionId(raw: unknown) {
  const parsed = Number(raw || 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function detectMethodName(key: string, payloadMethod: string) {
  if (payloadMethod) return payloadMethod;
  const m = key.match(/^obj_([^_]+(?:_[^_]+)*)_/);
  return m?.[1] || '';
}

const contractActions = computed<ContractAction[]>(() => {
  const merged: Array<Record<string, unknown>> = [];
  if (Array.isArray(contract.value?.buttons)) merged.push(...(contract.value?.buttons as Array<Record<string, unknown>>));
  if (Array.isArray(contract.value?.toolbar?.header)) merged.push(...(contract.value?.toolbar?.header as Array<Record<string, unknown>>));

  const dedup = new Set<string>();
  const out: ContractAction[] = [];
  for (const row of merged) {
    const key = String(row.key || '').trim();
    if (!key || dedup.has(key)) continue;
    dedup.add(key);
    const payload = row.payload && typeof row.payload === 'object' ? (row.payload as Record<string, unknown>) : {};
    const kind = String(row.kind || '').trim().toLowerCase();
    const level = String(row.level || 'body').trim().toLowerCase();
    const actionId = toActionId(payload.action_id) ?? toActionId(payload.ref);
    const methodName = detectMethodName(key, String(payload.method || '').trim());
    const groups = Array.isArray(row.groups_xmlids) ? (row.groups_xmlids as string[]) : [];
    const byGroup = hasGroupAccess(groups);
    const needRecord = kind === 'object' || kind === 'server' || level === 'row' || level === 'smart';
    const enabled = byGroup && (!needRecord || Boolean(recordId.value));
    out.push({
      key,
      label: String(row.label || key),
      kind,
      level,
      actionId,
      methodName,
      enabled,
      hint: byGroup ? (needRecord && !recordId.value ? 'requires record id' : '') : 'permission denied',
    });
  }
  return out;
});

const headerActions = computed(() => contractActions.value.filter((item) => item.level === 'header' || item.level === 'toolbar'));
const bodyActions = computed(() => contractActions.value.filter((item) => item.level !== 'header' && item.level !== 'toolbar'));

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
      nodes.push({ key: `${kind}_${i}`, kind: kind as 'header' | 'sheet', name: '', label: '', readonly: true });
      continue;
    }
    if (kind !== 'field') continue;
    const name = String(item?.name || '').trim();
    if (!name || used.has(name)) continue;
    const groups = fieldGroups[name]?.groups_xmlids;
    if (!hasGroupAccess(Array.isArray(groups) ? groups : [])) continue;
    used.add(name);
    const descriptor = fieldMap[name];
    nodes.push({
      key: `field_${name}`,
      kind: 'field',
      name,
      label: String(descriptor?.string || name),
      readonly: Boolean(descriptor?.readonly || (recordId.value ? !rights.value.write : !rights.value.create)),
      descriptor,
    });
  }

  Object.entries(fieldMap).forEach(([name, descriptor]) => {
    if (used.has(name)) return;
    const groups = fieldGroups[name]?.groups_xmlids;
    if (!hasGroupAccess(Array.isArray(groups) ? groups : [])) return;
    nodes.push({
      key: `field_${name}`,
      kind: 'field',
      name,
      label: String(descriptor?.string || name),
      readonly: Boolean(descriptor?.readonly || (recordId.value ? !rights.value.write : !rights.value.create)),
      descriptor,
    });
  });

  return nodes;
});

function fieldInputType(ttype?: string) {
  if (ttype === 'integer' || ttype === 'float' || ttype === 'monetary') return 'number';
  if (ttype === 'date') return 'date';
  if (ttype === 'datetime') return 'datetime-local';
  return 'text';
}

const hudEntries = computed(() => [
  { label: 'model', value: model.value || '-' },
  { label: 'action_id', value: actionId.value || '-' },
  { label: 'record_id', value: recordIdDisplay.value },
  { label: 'contract_loaded', value: Boolean(contract.value) },
  { label: 'contract_view_type', value: contract.value?.head?.view_type || contract.value?.view_type || '-' },
  { label: 'fields_count', value: Object.keys(contract.value?.fields || {}).length },
  { label: 'layout_nodes', value: layoutNodes.value.length },
  { label: 'actions_count', value: contractActions.value.length },
  { label: 'rights', value: `${rights.value.read ? 'R' : '-'}${rights.value.write ? 'W' : '-'}${rights.value.create ? 'C' : '-'}${rights.value.unlink ? 'D' : '-'}` },
]);

async function loadContract() {
  if (!actionId.value) {
    throw new Error('missing action_id');
  }
  const response = await loadActionContractRaw(actionId.value);
  if (!response?.data || typeof response.data !== 'object') {
    throw new Error('empty contract');
  }
  contract.value = response.data as ActionContract;
  contractMeta.value = response.meta || null;
}

async function loadRecord() {
  const fieldNames = Object.keys(contract.value?.fields || {});
  if (!recordId.value) {
    fieldNames.forEach((name) => {
      formData[name] = '';
    });
    return;
  }
  const read = await readRecord({
    model: model.value,
    ids: [recordId.value],
    fields: fieldNames.length ? fieldNames : '*',
  });
  const row = read.records?.[0] || {};
  fieldNames.forEach((name) => {
    formData[name] = row[name] ?? '';
  });
}

async function reload() {
  status.value = 'loading';
  errorMessage.value = '';
  try {
    await loadContract();
    await loadRecord();
    status.value = 'ok';
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'load failed';
    status.value = 'error';
  }
}

async function runAction(action: ContractAction) {
  if (!action.enabled) return;
  if (action.kind === 'open' && action.actionId) {
    await router.push({
      name: 'action',
      params: { actionId: String(action.actionId) },
      query: {
        menu_id: route.query.menu_id,
        action_id: action.actionId,
      },
    });
    return;
  }
  if ((action.kind === 'object' || action.kind === 'server') && action.methodName && recordId.value) {
    busyKind.value = 'action';
    try {
      const response = await executeButton({
        model: model.value,
        res_id: recordId.value,
        button: { name: action.methodName, type: 'object' },
        context: {},
        meta: {
          menu_id: Number(route.query.menu_id || 0) || undefined,
          action_id: actionId.value || undefined,
        },
      });
      const refresh = response?.result && typeof response.result === 'object' ? (response.result as Record<string, unknown>).type : '';
      if (refresh === 'refresh') {
        await reload();
      }
    } finally {
      busyKind.value = null;
    }
  }
}

async function openFilter(filterKey: string) {
  if (!actionId.value) return;
  await router.push({
    name: 'action',
    params: { actionId: String(actionId.value) },
    query: {
      menu_id: route.query.menu_id,
      action_id: actionId.value,
      preset_filter: filterKey,
    },
  });
}

async function saveRecord() {
  if (!canSave.value || !model.value) return;
  busyKind.value = 'save';
  try {
    const values: Record<string, unknown> = {};
    layoutNodes.value
      .filter((node) => node.kind === 'field' && !node.readonly)
      .forEach((node) => {
        values[node.name] = formData[node.name];
      });
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
        query: { ...route.query },
      });
      return;
    }
  } finally {
    busyKind.value = null;
  }
}

reload();
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

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 10px;
}

.layout-divider {
  grid-column: 1 / -1;
  font-size: 12px;
  color: #475569;
  border-bottom: 1px dashed #cbd5e1;
  padding-bottom: 4px;
}

.field {
  display: grid;
  gap: 6px;
}

.label {
  font-size: 12px;
  color: #334155;
  font-weight: 600;
}

.input {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 10px;
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
