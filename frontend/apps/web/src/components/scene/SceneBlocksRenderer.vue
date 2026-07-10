<template>
  <section class="scene-blocks">
    <article
      v-for="block in orderedBlocks"
      :key="block.key"
      class="scene-block"
      :class="[`scene-block--${block.kind}`, `scene-block--${block.semantic_role || 'content'}`]"
    >
      <header class="scene-block__header">
        <div>
          <p class="scene-block__eyebrow">{{ blockKindLabel(block.kind) }}</p>
          <h3 class="scene-block__title">{{ blockTitle(block) }}</h3>
        </div>
        <span v-if="block.visible === false" class="scene-block__badge">隐藏</span>
      </header>

      <div v-if="block.kind === 'header_bar'" class="scene-block__body scene-block__body--actions">
        <button
          v-for="action in block.actions || []"
          :key="`${block.key}-${action.key}`"
          type="button"
          class="scene-block__button"
          @click="emitAction(block, action)"
        >
          {{ actionDisplayLabel(action) }}
        </button>
      </div>

      <div v-else-if="block.kind === 'toolbar'" class="scene-block__body scene-block__body--toolbar">
        <div v-if="toolbarText(block, 'quick_filters')" class="scene-block__chips">
          <button
            v-for="item in toolbarItems(block, 'quick_filters')"
            :key="`${block.key}-${String(item.key || item.label || '')}`"
            class="scene-block__chip"
            type="button"
            @click="emitToolbarFilterAction(block, item)"
          >
            {{ recordDisplayLabel(item) }}
          </button>
        </div>
        <div v-if="toolbarItems(block, 'view_modes').length" class="scene-block__chips">
          <button
            v-for="item in toolbarItems(block, 'view_modes')"
            :key="`${block.key}-view-${String(item.key || item.label || '')}`"
            class="scene-block__chip scene-block__chip--secondary"
            type="button"
            @click="emitToolbarViewModeAction(block, item)"
          >
            {{ recordDisplayLabel(item) }}
          </button>
        </div>
      </div>

      <div v-else-if="block.kind === 'statusbar'" class="scene-block__body scene-block__body--meta">
        <div v-if="statusbarStates(block).length" class="scene-block__chips">
          <button
            v-for="item in statusbarStates(block)"
            :key="`${block.key}-state-${item.value}`"
            type="button"
            class="scene-block__chip scene-block__chip--status"
            @click="emitStatusbarAction(block, item)"
          >
            {{ item.label }}
          </button>
        </div>
      </div>

      <div v-else-if="block.kind === 'primary_actions' || block.kind === 'smart_actions'" class="scene-block__body scene-block__body--actions">
        <button
          v-for="action in block.actions || []"
          :key="`${block.key}-${action.key}`"
          type="button"
          class="scene-block__button"
          @click="emitAction(block, action)"
        >
          {{ actionDisplayLabel(action) }}
        </button>
      </div>

      <div v-else-if="block.kind === 'body' || block.kind === 'list_view' || block.kind === 'kanban_board'" class="scene-block__body">
        <div class="scene-block__kv-grid">
          <p class="scene-block__kv-item">
            <span class="scene-block__kv-key">字段数</span>
            <strong class="scene-block__kv-val">{{ blockFieldCount(block) }}</strong>
          </p>
          <p class="scene-block__kv-item">
            <span class="scene-block__kv-key">搜索字段</span>
            <strong class="scene-block__kv-val">{{ blockSearchFieldCount(block) }}</strong>
          </p>
        </div>
        <div v-if="blockFieldLabels(block).length" class="scene-block__chips">
          <span
            v-for="field in blockFieldLabels(block)"
            :key="`${block.key}-field-${field.key}`"
            class="scene-block__chip scene-block__chip--plain"
          >
            {{ field.label }}
          </span>
        </div>
      </div>

      <div v-else-if="block.kind === 'relation_block'" class="scene-block__body">
        <div v-if="relationFieldRows(block).length" class="scene-block__chips">
          <span
            v-for="item in relationFieldRows(block)"
            :key="`${block.key}-relation-${item.field}`"
            class="scene-block__chip scene-block__chip--plain"
          >
            {{ item.label }}
          </span>
        </div>
      </div>

      <div v-else-if="block.kind === 'overview_strip'" class="scene-block__body">
        <div v-if="overviewItems(block).length" class="scene-block__kv-grid">
          <p
            v-for="item in overviewItems(block)"
            :key="`${block.key}-overview-${item.key}`"
            class="scene-block__kv-item"
          >
            <span class="scene-block__kv-key">{{ item.label }}</span>
            <strong class="scene-block__kv-val">{{ item.value }}</strong>
          </p>
        </div>
      </div>

      <div v-else class="scene-block__body">
        <div class="scene-block__kv-grid" />
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type SceneBlockAction = {
  key?: string;
  label?: string;
  intent?: string;
  target?: Record<string, unknown>;
};

type SceneBlock = {
  key?: string;
  kind?: string;
  title?: string;
  order?: number;
  visible?: boolean;
  semantic_role?: string;
  layout?: Record<string, unknown>;
  data_deps?: Record<string, unknown>;
  actions?: SceneBlockAction[];
  payload?: Record<string, unknown>;
};

const props = defineProps<{
  blocks: SceneBlock[];
}>();

const emit = defineEmits<{
  (event: 'action', payload: { block: SceneBlock; action: SceneBlockAction }): void;
}>();

const orderedBlocks = computed(() => {
  const blocks = Array.isArray(props.blocks) ? [...props.blocks] : [];
  return blocks
    .filter((item) => item && typeof item === 'object')
    .sort((a, b) => Number(a.order || 0) - Number(b.order || 0));
});

function toolbarItems(block: SceneBlock, key: string) {
  const payload = block.payload && typeof block.payload === 'object' ? block.payload : {};
  const raw = (payload as Record<string, unknown>)[key];
  return Array.isArray(raw) ? raw as Array<Record<string, unknown>> : [];
}

function labelFromDictLikeText(value: unknown): string {
  const source = String(value || '').trim();
  if (!source.startsWith('{') || !source.includes('label')) return source;
  const match = source.match(/['"]label['"]\s*:\s*['"]([^'"]+)['"]/);
  return String(match?.[1] || source).trim();
}

function recordDisplayLabel(item: Record<string, unknown>): string {
  return labelFromDictLikeText(item.label || item.key || '');
}

function actionDisplayLabel(action: SceneBlockAction): string {
  return labelFromDictLikeText(action.label || action.key || '');
}

function blockKindLabel(kind: unknown): string {
  const raw = String(kind || '').trim();
  const mapping: Record<string, string> = {
    header_bar: '页面头部',
    toolbar: '筛选工具栏',
    statusbar: '状态流转',
    primary_actions: '主要操作',
    smart_actions: '快捷操作',
    body: '主体内容',
    list_view: '列表内容',
    kanban_board: '看板内容',
    relation_block: '关联明细',
    overview_strip: '摘要信息',
  };
  if (!raw) return '页面区块';
  return mapping[raw] || raw.replace(/_/g, ' ');
}

function blockTitle(block: SceneBlock): string {
  const title = labelFromDictLikeText(block.title || '');
  if (title) return title;
  return blockKindLabel(block.kind);
}

function asArray(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value)
    ? value.filter((item) => item && typeof item === 'object') as Array<Record<string, unknown>>
    : [];
}

function fieldDisplayLabel(item: Record<string, unknown>) {
  return labelFromDictLikeText(item.label || item.string || item.title || item.field || item.name || item.key || '');
}

function blockFieldLabels(block: SceneBlock) {
  const deps = block.data_deps && typeof block.data_deps === 'object' ? block.data_deps : {};
  const columns = asArray((deps as Record<string, unknown>).columns)
    .map((item) => ({
      key: String(item.field || item.name || item.key || item.label || '').trim(),
      label: fieldDisplayLabel(item),
    }))
    .filter((item) => item.key && item.label);
  const fields = asArray((deps as Record<string, unknown>).fields)
    .map((item) => ({
      key: String(item.field || item.name || item.key || item.label || '').trim(),
      label: fieldDisplayLabel(item),
    }))
    .filter((item) => item.key && item.label);
  const merged = [...columns, ...fields];
  return Array.from(new Map(merged.map((item) => [item.key, item])).values()).slice(0, 12);
}

function blockFieldCount(block: SceneBlock) {
  return blockFieldLabels(block).length;
}

function blockSearchFieldCount(block: SceneBlock) {
  const deps = block.data_deps && typeof block.data_deps === 'object' ? block.data_deps : {};
  return asArray((deps as Record<string, unknown>).search_fields).length;
}

function relationFieldRows(block: SceneBlock) {
  const payload = block.payload && typeof block.payload === 'object' ? block.payload : {};
  return asArray((payload as Record<string, unknown>).relation_fields)
    .map((item) => ({
      field: String(item.field || item.name || '').trim(),
      label: String(item.label || item.field || item.name || '').trim(),
    }))
    .filter((item) => item.field);
}

function overviewItems(block: SceneBlock) {
  const payload = block.payload && typeof block.payload === 'object' ? block.payload : {};
  return asArray((payload as Record<string, unknown>).overview_items)
    .map((item) => ({
      key: String(item.key || item.label || '').trim(),
      label: String(item.label || item.key || '').trim(),
      value: String(item.value ?? item.count ?? '--').trim(),
    }))
    .filter((item) => item.key);
}

function toolbarText(block: SceneBlock, key: string) {
  const payload = block.payload && typeof block.payload === 'object' ? block.payload : {};
  const raw = (payload as Record<string, unknown>)[key];
  if (!raw) return '';
  if (Array.isArray(raw)) return '';
  if (typeof raw === 'string') return raw.trim();
  return '';
}

function statusbarStates(block: SceneBlock) {
  const payload = block.payload && typeof block.payload === 'object' ? block.payload : {};
  const workflow = (payload as Record<string, unknown>).workflow_surface;
  const workflowRow = workflow && typeof workflow === 'object' ? workflow as Record<string, unknown> : {};
  const states = Array.isArray(workflowRow.states) ? workflowRow.states : [];
  return states
    .map((item) => (item && typeof item === 'object' ? item as Record<string, unknown> : {}))
    .map((item) => ({
      value: String(item.value || item.key || '').trim(),
      label: String(item.label || item.value || item.key || '').trim(),
    }))
    .filter((item) => item.value && item.label);
}

function emitToolbarFilterAction(block: SceneBlock, item: Record<string, unknown>) {
  const key = String(item.key || '').trim();
  if (!key) return;
  emitAction(block, {
    key: `filter:${key}`,
    label: String(item.label || key),
    intent: 'scene.block.filter',
    target: {
      kind: 'quick_filter',
      filter_key: key,
    },
  });
}

function emitToolbarViewModeAction(block: SceneBlock, item: Record<string, unknown>) {
  const raw = String(item.key || item.mode || '').trim().toLowerCase();
  if (!raw) return;
  const mode = raw === 'tree' ? 'list' : raw;
  emitAction(block, {
    key: `view_mode:${mode}`,
    label: String(item.label || mode),
    intent: 'scene.block.view_mode',
    target: {
      kind: 'view_mode',
      view_mode: mode,
    },
  });
}

function emitStatusbarAction(block: SceneBlock, item: { value: string; label: string }) {
  emitAction(block, {
    key: `status:${item.value}`,
    label: item.label,
    intent: 'scene.block.statusbar',
    target: {
      kind: 'statusbar_value',
      value: item.value,
    },
  });
}

function emitAction(block: SceneBlock, action: SceneBlockAction) {
  const key = String(action.key || '').trim();
  if (!key) return;
  emit('action', { block, action });
}
</script>

<style scoped>
.scene-blocks {
  display: grid;
  gap: 12px;
  min-width: 0;
}
.scene-block {
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  padding: 12px 14px;
}
.scene-block__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}
.scene-block__eyebrow {
  margin: 0;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}
.scene-block__title {
  margin: 2px 0 0;
  font-size: 16px;
  line-height: 1.2;
  overflow-wrap: anywhere;
}
.scene-block__badge {
  font-size: 12px;
  color: var(--sc-app-warning-text);
}
.scene-block__body {
  margin-top: 10px;
  min-width: 0;
}
.scene-block__body--actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.scene-block__body--toolbar {
  display: grid;
  gap: 6px;
}
.scene-block__hint {
  margin: 0;
  font-size: 13px;
  color: var(--sc-app-text-secondary);
}
.scene-block__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.scene-block__chip {
  padding: 4px 10px;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 999px;
  font-size: 12px;
  color: var(--sc-app-text-primary);
  background: var(--sc-app-muted-bg);
  cursor: pointer;
}
.scene-block__chip--secondary {
  border-style: dashed;
}
.scene-block__chip--status {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
}
.scene-block__button {
  padding: 6px 12px;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 999px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  font-size: 13px;
  cursor: pointer;
}
.scene-block__chip--plain {
  cursor: default;
  border-color: var(--sc-app-border);
}
.scene-block__kv-grid {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}
.scene-block__kv-item {
  margin: 0;
  padding: 8px 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-muted-bg);
}
.scene-block__kv-key {
  display: block;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}
.scene-block__kv-val {
  display: block;
  margin-top: 2px;
  font-size: 14px;
  color: var(--sc-app-text-primary);
}
</style>
