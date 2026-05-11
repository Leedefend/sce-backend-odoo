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
          <p class="scene-block__eyebrow">{{ block.kind }}</p>
          <h3 class="scene-block__title">{{ block.title || block.key }}</h3>
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
          {{ action.label || action.key }}
        </button>
      </div>

      <div v-else-if="block.kind === 'toolbar'" class="scene-block__body scene-block__body--toolbar">
        <div v-if="toolbarText(block, 'search_surface')" class="scene-block__hint">{{ toolbarText(block, 'search_surface') }}</div>
        <div v-if="toolbarText(block, 'list_surface')" class="scene-block__hint">{{ toolbarText(block, 'list_surface') }}</div>
        <div v-if="toolbarText(block, 'advanced_filters')" class="scene-block__hint">{{ toolbarText(block, 'advanced_filters') }}</div>
        <div v-if="toolbarText(block, 'quick_filters')" class="scene-block__chips">
          <button
            v-for="item in toolbarItems(block, 'quick_filters')"
            :key="`${block.key}-${String(item.key || item.label || '')}`"
            class="scene-block__chip"
            type="button"
            @click="emitToolbarFilterAction(block, item)"
          >
            {{ String(item.label || item.key || '') }}
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
            {{ String(item.label || item.key || '') }}
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
        <pre v-else class="scene-block__json">{{ stringifyCompact(block.payload) }}</pre>
      </div>

      <div v-else-if="block.kind === 'primary_actions' || block.kind === 'smart_actions'" class="scene-block__body scene-block__body--actions">
        <button
          v-for="action in block.actions || []"
          :key="`${block.key}-${action.key}`"
          type="button"
          class="scene-block__button"
          @click="emitAction(block, action)"
        >
          {{ action.label || action.key }}
        </button>
      </div>

      <div v-else-if="block.kind === 'body' || block.kind === 'list_view' || block.kind === 'kanban_board'" class="scene-block__body">
        <p class="scene-block__hint">
          {{ bodyHint(block) }}
        </p>
        <pre class="scene-block__json">{{ stringifyCompact(block.data_deps || block.payload) }}</pre>
      </div>

      <div v-else-if="block.kind === 'relation_block' || block.kind === 'chatter' || block.kind === 'overview_strip'" class="scene-block__body">
        <pre class="scene-block__json">{{ stringifyCompact(block.payload) }}</pre>
      </div>

      <div v-else class="scene-block__body">
        <pre class="scene-block__json">{{ stringifyCompact(block.payload || block.data_deps || {}) }}</pre>
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

function stringifyCompact(value: unknown) {
  if (!value || typeof value !== 'object') return '';
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return '';
  }
}

function toolbarItems(block: SceneBlock, key: string) {
  const payload = block.payload && typeof block.payload === 'object' ? block.payload : {};
  const raw = (payload as Record<string, unknown>)[key];
  return Array.isArray(raw) ? raw as Array<Record<string, unknown>> : [];
}

function toolbarText(block: SceneBlock, key: string) {
  const payload = block.payload && typeof block.payload === 'object' ? block.payload : {};
  const raw = (payload as Record<string, unknown>)[key];
  if (!raw) return '';
  if (Array.isArray(raw)) return '';
  if (typeof raw === 'string') return raw.trim();
  if (typeof raw === 'object') {
    try {
      return JSON.stringify(raw);
    } catch {
      return '';
    }
  }
  return String(raw);
}

function bodyHint(block: SceneBlock) {
  if (block.kind === 'list_view') return '列表场景块';
  if (block.kind === 'kanban_board') return '看板场景块';
  if (block.kind === 'body') return '表单主体场景块';
  return '场景内容块';
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
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  background: #fff;
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
  color: #64748b;
}
.scene-block__title {
  margin: 2px 0 0;
  font-size: 16px;
  line-height: 1.2;
  overflow-wrap: anywhere;
}
.scene-block__badge {
  font-size: 12px;
  color: #b45309;
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
  color: #475569;
}
.scene-block__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.scene-block__chip {
  padding: 4px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  font-size: 12px;
  color: #0f172a;
  background: #f8fafc;
  cursor: pointer;
}
.scene-block__chip--secondary {
  border-style: dashed;
}
.scene-block__chip--status {
  border-color: #94a3b8;
  background: #eef2ff;
}
.scene-block__button {
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #0f172a;
  font-size: 13px;
  cursor: pointer;
}
.scene-block__json {
  margin: 0;
  padding: 10px;
  border-radius: 8px;
  background: #f8fafc;
  color: #334155;
  font-size: 12px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
