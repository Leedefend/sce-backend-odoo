<template>
  <div class="view-layout">
    <ViewGroupRenderer
      v-for="(group, index) in groups"
      :key="`root-group-${index}`"
      :group="group"
      :fields="fields"
      :record="record"
      :parent-id="parentId"
      :editing="editing"
      :draft-name="draftName"
      :edit-mode="editMode"
      :depth="0"
      @update:field="emit('update:field', $event)"
    />
    <ViewNotebookRenderer
      v-for="(notebook, index) in notebooks"
      :key="`notebook-${index}`"
      :notebook="notebook"
      :fields="fields"
      :record="record"
      :parent-id="parentId"
      :editing="editing"
      :draft-name="draftName"
      :edit-mode="editMode"
      @update:field="emit('update:field', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { ViewContract } from '@sc/schema';
import ViewGroupRenderer from './ViewGroupRenderer.vue';
import ViewNotebookRenderer from './ViewNotebookRenderer.vue';

interface ViewLayoutNode {
  groups?: Array<Record<string, unknown>>;
  notebooks?: Array<Record<string, unknown>>;
}

const props = defineProps<{
  layout: ViewLayoutNode;
  fields?: ViewContract['fields'];
  record?: Record<string, unknown> | null;
  parentId?: number;
  editing: boolean;
  draftName: string;
  editMode: 'none' | 'name' | 'all';
}>();

const emit = defineEmits<{ (event: 'update:field', payload: { name: string; value: string }): void }>();

const groups = computed(() => (Array.isArray(props.layout.groups) ? props.layout.groups : []));
const notebooks = computed(() => (Array.isArray(props.layout.notebooks) ? props.layout.notebooks : []));
</script>

<style scoped>
.view-layout {
  display: grid;
  gap: 16px;
}
</style>
