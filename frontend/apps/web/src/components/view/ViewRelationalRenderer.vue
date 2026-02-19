<template>
  <div class="relational">
    <div class="relational-header">
      <span class="relational-title">{{ headerLabel }}</span>
      <div class="relational-actions">
        <span class="relational-count">{{ countLabel }}</span>
        <button v-if="canEdit" class="relational-add" type="button" @click="startCreate">Add line</button>
      </div>
    </div>
    <div v-if="loading" class="relational-meta">Loading related records…</div>
    <div v-else-if="error" class="relational-meta">{{ error }}</div>
    <div v-else-if="!rows.length" class="relational-meta">No related records.</div>
    <ul v-else class="relational-list">
      <li v-for="row in rows" :key="String(row.id)" class="relational-item">
        <button class="relational-link" type="button" @click="openRecord(row.id)">
          {{ row.name || `#${row.id}` }}
        </button>
        <div v-if="canEdit" class="relational-row-actions">
          <button class="relational-edit" type="button" @click="startEdit(row)">Edit</button>
          <button class="relational-delete" type="button" @click="removeRow(row)">Delete</button>
        </div>
      </li>
    </ul>
    <div v-if="truncated" class="relational-meta">Showing first {{ rows.length }} records.</div>

    <div v-if="editorVisible" class="relational-editor">
      <div class="editor-card">
        <div class="editor-title">{{ editorTitle }}</div>
        <div v-if="editTx.state === 'saved'" class="editor-banner">Saved.</div>
        <div v-else-if="editTx.state === 'saving'" class="editor-banner">Saving…</div>
        <label class="editor-label">Name</label>
        <input v-model="draftName" class="editor-input" type="text" />
        <div class="editor-actions">
          <button class="relational-save" type="button" :disabled="saving || !draftName.trim()" @click="saveRow">
            {{ saving ? 'Saving…' : 'Save' }}
          </button>
          <button class="relational-cancel" type="button" @click="cancelEdit">Cancel</button>
        </div>
        <div v-if="editorError" class="relational-meta">{{ editorError }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createRecord, listRecords, unlinkRecord, writeRecord } from '../../api/data';
import { useEditTx } from '../../composables/useEditTx';

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

const headerLabel = computed(() => (props.model ? props.model : 'Related'));
const countLabel = computed(() => `${props.ids.length} items`);
const canEdit = computed(() => Boolean(props.editable && props.parentId && props.relationField && props.model));
const editorTitle = computed(() => (editorMode.value === 'create' ? 'Add related record' : 'Edit related record'));
type RelationRecordRaw = { id?: number | string; name?: unknown };

async function load() {
  rows.value = [];
  error.value = '';
  truncated.value = false;
  if (!props.model) {
    error.value = 'Missing relation model';
    return;
  }
  if (!Array.isArray(props.ids) || props.ids.length === 0) {
    return;
  }
  loading.value = true;
  try {
    const ids = props.ids.slice(0, 50);
    truncated.value = props.ids.length > ids.length;
    const response = await listRecords({
      model: props.model,
      fields: ['id', 'name'],
      domain: [['id', 'in', ids]],
      limit: ids.length,
      order: 'id asc',
    });
    rows.value = (response.records || []).map((record) => {
      const raw = record as RelationRecordRaw;
      return {
      id: Number(raw.id),
      name: raw.name ? String(raw.name) : undefined,
      };
    });
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load relation records';
  } finally {
    loading.value = false;
  }
}

function openRecord(id: number) {
  if (!props.model) return;
  const source = route.query as Record<string, unknown>;
  const carry: Record<string, unknown> = {};
  const keys = ['menu_id', 'action_id', 'hud', 'scene', 'scene_key', 'context_raw', 'preset', 'preset_filter', 'search', 'ctx_source'];
  keys.forEach((key) => {
    if (source[key] !== undefined) {
      carry[key] = source[key];
    }
  });
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
    editorError.value = 'Missing relation configuration';
    return;
  }
  if (!draftName.value.trim()) return;
  saving.value = true;
  editorError.value = '';
  try {
    await editTx.save(async () => {
      if (editorMode.value === 'create') {
        return createRecord({
          model: props.model,
          vals: {
            name: draftName.value.trim(),
            [props.relationField]: props.parentId,
          },
        });
      }
      if (editorTargetId.value) {
        return writeRecord({
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
    editorError.value = err instanceof Error ? err.message : 'Failed to save related record';
    editTx.markError();
  } finally {
    saving.value = false;
  }
}

async function removeRow(row: { id: number }) {
  if (!props.model) return;
  if (!confirm('Delete this related record?')) return;
  try {
    await editTx.save(async () => {
      return unlinkRecord({ model: props.model, ids: [row.id] });
    });
    editTx.markSaved();
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to delete related record';
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
  border: 1px dashed rgba(148, 163, 184, 0.5);
  background: #f8fafc;
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
  color: #0f172a;
}

.relational-count {
  color: #64748b;
}

.relational-meta {
  font-size: 12px;
  color: #64748b;
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
  background: white;
  border: 1px solid rgba(148, 163, 184, 0.4);
  border-radius: 8px;
  padding: 6px 10px;
  color: #0f172a;
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
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: white;
  color: #0f172a;
  border-radius: 8px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}

.relational-delete {
  border-color: rgba(248, 113, 113, 0.4);
  color: #b91c1c;
}

.relational-save {
  background: #0f172a;
  color: white;
  border-color: #0f172a;
}

.relational-editor {
  margin-top: 12px;
}

.editor-card {
  border: 1px dashed rgba(148, 163, 184, 0.4);
  border-radius: 10px;
  padding: 12px;
  background: #fff;
  display: grid;
  gap: 8px;
}

.editor-title {
  font-weight: 600;
}

.editor-label {
  font-size: 12px;
  color: #64748b;
}

.editor-input {
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  padding: 8px;
  font-size: 13px;
}

.editor-banner {
  font-size: 12px;
  color: #0f172a;
  background: #ecfeff;
  border: 1px solid #a5f3fc;
  padding: 4px 8px;
  border-radius: 8px;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.relational-link:hover {
  border-color: #94a3b8;
}
</style>
