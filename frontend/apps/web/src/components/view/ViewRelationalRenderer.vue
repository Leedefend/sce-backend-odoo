<template>
  <div class="relational">
    <div class="relational-header">
      <span class="relational-title">{{ headerLabel }}</span>
      <div class="relational-actions">
        <span class="relational-count">{{ countLabel }}</span>
        <button v-if="canEdit" class="relational-add" type="button" @click="startCreate">新增明细</button>
      </div>
    </div>
    <div v-if="loading" class="relational-meta">正在加载关联记录...</div>
    <div v-else-if="error" class="relational-meta">{{ error }}</div>
    <div v-else-if="!rows.length" class="relational-meta">暂无关联记录。</div>
    <ul v-else class="relational-list">
      <li v-for="row in rows" :key="String(row.id)" class="relational-item">
        <button class="relational-link" type="button" @click="openRecord(row.id)">
          {{ row.name || `#${row.id}` }}
        </button>
        <div v-if="canEdit" class="relational-row-actions">
          <button class="relational-edit" type="button" @click="startEdit(row)">编辑</button>
          <button class="relational-delete" type="button" @click="removeRow(row)">删除</button>
        </div>
      </li>
    </ul>
    <div v-if="truncated" class="relational-meta">当前仅显示前 {{ rows.length }} 条记录。</div>
    <ProductConfirmDialog
      :open="deleteConfirm.state.open"
      :title="deleteConfirm.state.title"
      :message="deleteConfirm.state.message"
      :confirm-label="deleteConfirm.state.confirmLabel"
      :cancel-label="deleteConfirm.state.cancelLabel"
      :tone="deleteConfirm.state.tone"
      @confirm="deleteConfirm.confirm"
      @cancel="deleteConfirm.cancel"
    />

    <div v-if="editorVisible" class="relational-editor">
      <div class="editor-card">
        <div class="editor-title">{{ editorTitle }}</div>
        <div v-if="editTxState === 'saved'" class="editor-banner">已保存。</div>
        <div v-else-if="editTxState === 'saving'" class="editor-banner">正在保存...</div>
        <label class="editor-label">名称</label>
        <input v-model="draftName" class="editor-input" type="text" />
        <div class="editor-actions">
          <button class="relational-save" type="button" :disabled="saving || !draftName.trim()" @click="saveRow">
            {{ saving ? '正在保存...' : '保存' }}
          </button>
          <button class="relational-cancel" type="button" @click="cancelEdit">取消</button>
        </div>
        <div v-if="editorError" class="relational-meta">{{ editorError }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ProductConfirmDialog from '../ProductConfirmDialog.vue';
import { useEditTx } from '../../composables/useEditTx';
import { useProductConfirmDialog } from '../../composables/useProductConfirmDialog';
import { pickContractNavQuery } from '../../app/navigationContext';
import {
  createRelationRendererRecord,
  listRelationRendererRecords,
  unlinkRelationRendererRecord,
  writeRelationRendererRecord,
} from '../../app/runtime/relationRendererDataRuntime';

const props = defineProps<{
  ids: number[];
  model?: string;
  relationField?: string;
  parentId?: number;
  editable?: boolean;
}>();

const router = useRouter();
const route = useRoute();
const loading = ref(false);
const error = ref('');
const rows = ref<Array<{ id: number; name?: string }>>([]);
const truncated = ref(false);
const editorVisible = ref(false);
const editorMode = ref<'create' | 'edit'>('create');
const editorTargetId = ref<number | null>(null);
const draftName = ref('');
const saving = ref(false);
const editorError = ref('');
const editTx = useEditTx();
const editTxState = computed(() => editTx.state.value);
const deleteConfirm = useProductConfirmDialog();

const headerLabel = computed(() => (props.model ? props.model : '关联记录'));
const countLabel = computed(() => `共 ${props.ids.length} 条`);
const canEdit = computed(() => Boolean(props.editable && props.parentId && props.relationField && props.model));
const editorTitle = computed(() => (editorMode.value === 'create' ? '新增关联记录' : '编辑关联记录'));
type RelationRecordRaw = { id?: number | string; name?: unknown };

async function load() {
  rows.value = [];
  error.value = '';
  truncated.value = false;
  if (!props.model) {
    error.value = '缺少关联模型配置';
    return;
  }
  if (!Array.isArray(props.ids) || props.ids.length === 0) {
    return;
  }
  loading.value = true;
  try {
    const ids = props.ids.slice(0, 50);
    truncated.value = props.ids.length > ids.length;
    const response = await listRelationRendererRecords({
      model: props.model,
      fields: ['id', 'name'],
      domain: [['id', 'in', ids]],
      limit: ids.length,
      order: 'id asc',
      silentErrors: true,
    });
    rows.value = (response.records || []).map((record) => {
      const raw = record as RelationRecordRaw;
      return {
      id: Number(raw.id),
      name: raw.name ? String(raw.name) : undefined,
      };
    });
  } catch (err) {
    error.value = err instanceof Error ? err.message : '关联记录加载失败';
  } finally {
    loading.value = false;
  }
}

function openRecord(id: number) {
  if (!props.model) return;
  const carry = pickContractNavQuery(route.query as Record<string, unknown>);
  router.push({ name: 'record', params: { model: props.model, id }, query: carry });
}

function startCreate() {
  editorError.value = '';
  editorVisible.value = true;
  editorMode.value = 'create';
  editorTargetId.value = null;
  draftName.value = '';
  editTx.beginEdit();
}

function startEdit(row: { id: number; name?: string }) {
  editorError.value = '';
  editorVisible.value = true;
  editorMode.value = 'edit';
  editorTargetId.value = row.id;
  draftName.value = row.name || '';
  editTx.beginEdit();
}

function cancelEdit() {
  editorVisible.value = false;
  editorTargetId.value = null;
  draftName.value = '';
  editTx.cancelEdit();
}

async function saveRow() {
  if (!props.model || !props.relationField || !props.parentId) {
    editorError.value = '缺少关联配置';
    return;
  }
  if (!draftName.value.trim()) return;
  saving.value = true;
  editorError.value = '';
  try {
    await editTx.save(async () => {
      if (editorMode.value === 'create') {
        return createRelationRendererRecord({
          model: props.model,
          vals: {
            name: draftName.value.trim(),
            [props.relationField]: props.parentId,
          },
        });
      }
      if (editorTargetId.value) {
        return writeRelationRendererRecord({
          model: props.model,
          ids: [editorTargetId.value],
          vals: { name: draftName.value.trim() },
        });
      }
      return null;
    });
    editTx.markSaved();
    editorVisible.value = false;
    editorTargetId.value = null;
    draftName.value = '';
    await load();
  } catch (err) {
    editorError.value = err instanceof Error ? err.message : '关联记录保存失败';
    editTx.markError();
  } finally {
    saving.value = false;
  }
}

async function removeRow(row: { id: number }) {
  if (!props.model) return;
  const confirmed = await deleteConfirm.open({
    title: '确认删除关联记录',
    message: '删除后该关联记录将从当前业务中移除，请确认是否继续。',
    confirmLabel: '删除',
    cancelLabel: '取消',
    tone: 'danger',
  });
  if (!confirmed) return;
  try {
    await editTx.save(async () => {
      return unlinkRelationRendererRecord({ model: props.model, ids: [row.id] });
    });
    editTx.markSaved();
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '关联记录删除失败';
    editTx.markError();
  }
}

watch(
  () => [props.model, props.ids.join(',')],
  () => {
    load();
  },
  { immediate: true },
);

onMounted(load);
</script>

<style scoped>
.relational {
  display: grid;
  gap: 8px;
  padding: 10px;
  border-radius: 10px;
  border: 1px dashed var(--sc-app-border-strong);
  background: var(--sc-app-muted-bg);
}

.relational-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.relational-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.relational-title {
  font-weight: 600;
  color: var(--sc-app-text-primary);
}

.relational-count {
  color: var(--sc-app-text-secondary);
}

.relational-meta {
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.relational-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 6px;
}

.relational-item {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.relational-link {
  width: 100%;
  text-align: left;
  background: var(--sc-app-input-bg);
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 8px;
  padding: 6px 10px;
  color: var(--sc-app-text-primary);
  cursor: pointer;
}

.relational-row-actions {
  display: flex;
  gap: 6px;
}

.relational-add,
.relational-edit,
.relational-delete,
.relational-save,
.relational-cancel {
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  border-radius: 8px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}

.relational-delete {
  border-color: var(--sc-app-danger-border);
  color: var(--sc-app-danger-text);
}

.relational-save {
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
  border-color: var(--sc-semantic-surface-interactive);
}

.relational-editor {
  margin-top: 12px;
}

.editor-card {
  border: 1px dashed var(--sc-app-border-strong);
  border-radius: 10px;
  padding: 12px;
  background: var(--sc-app-panel);
  display: grid;
  gap: 8px;
}

.editor-title {
  font-weight: 600;
}

.editor-label {
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.editor-input {
  border-radius: 8px;
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 8px;
  font-size: 13px;
}

.editor-banner {
  font-size: 12px;
  color: var(--sc-app-info-text);
  background: var(--sc-app-info-bg);
  border: 1px solid var(--sc-app-info-border);
  padding: 4px 8px;
  border-radius: 8px;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.relational-link:hover {
  border-color: var(--sc-app-border-strong);
}
</style>
