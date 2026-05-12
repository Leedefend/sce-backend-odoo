<template>
  <div class="view-notebook">
    <div class="tabs">
      <button
        v-for="(page, index) in pages"
        :key="page.title || index"
        class="tab"
        :class="{ active: index === activeIndex }"
        @click="activeIndex = index"
      >
        {{ page.title || `Page ${index + 1}` }}
      </button>
    </div>
    <div class="tab-panel">
      <ViewGroupRenderer
        v-for="(group, index) in activeGroups"
        :key="`page-${activeIndex}-group-${index}`"
        :group="group"
        :fields="fields"
        :record="record"
        :editing="editing"
        :draft-name="draftName"
        :edit-mode="editMode"
        :depth="0"
        @update:field="emit('update:field', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { ViewContract } from '@sc/schema';
import ViewGroupRenderer from './ViewGroupRenderer.vue';

interface ViewPageNode {
  title?: string;
  groups?: Array<Record<string, unknown>>;
}

interface ViewNotebookNode {
  pages?: ViewPageNode[];
}

const props = defineProps<{
  notebook: ViewNotebookNode;
  fields?: ViewContract['fields'];
  record?: Record<string, unknown> | null;
  editing: boolean;
  draftName: string;
  editMode: 'none' | 'name' | 'all';
}>();

const emit = defineEmits<{ (event: 'update:field', payload: { name: string; value: string }): void }>();

const pages = computed(() => (Array.isArray(props.notebook.pages) ? props.notebook.pages : []));
const activeIndex = ref(0);
const activeGroups = computed(() => {
  const page = pages.value[activeIndex.value];
  if (!page || !Array.isArray(page.groups)) {
    return [];
  }
  return page.groups;
});
</script>

<style scoped>
.view-notebook {
  display: grid;
  gap: 16px;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tab {
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-subtle-bg);
  color: var(--sc-app-text-primary);
  cursor: pointer;
}

.tab.active {
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
  border-color: var(--sc-semantic-surface-interactive);
}

.tab-panel {
  display: grid;
  gap: 16px;
}
</style>
