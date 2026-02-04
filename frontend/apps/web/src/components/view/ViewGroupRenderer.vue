<template>
  <div class="view-group">
    <div class="view-grid">
      <ViewFieldRenderer
        v-for="field in fieldNodes"
        :key="field.name || field.string"
        :field="field"
        :descriptor="fields?.[field.name || '']"
        :value="record?.[field.name || '']"
        :parent-id="parentId"
        :editing="editing"
        :draft-name="draftName"
        :edit-mode="editMode"
        @update:field="emit('update:field', $event)"
      />
      <ViewGroupRenderer
        v-for="(sub, index) in subGroups"
        :key="`${depth}-${index}`"
        :group="sub"
        :fields="fields"
        :record="record"
        :parent-id="parentId"
        :editing="editing"
        :draft-name="draftName"
        :edit-mode="editMode"
        :depth="depth + 1"
        @update:field="emit('update:field', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { ViewContract } from '@sc/schema';
import ViewFieldRenderer from './ViewFieldRenderer.vue';

interface ViewGroupNode {
  fields?: Array<{ name?: string; string?: string } & Record<string, unknown>>;
  sub_groups?: Array<ViewGroupNode>;
}

const props = defineProps<{
  group: ViewGroupNode;
  fields?: ViewContract['fields'];
  record?: Record<string, unknown> | null;
  parentId?: number;
  editing: boolean;
  draftName: string;
  editMode: 'none' | 'name' | 'all';
  depth: number;
}>();

const emit = defineEmits<{ (event: 'update:field', payload: { name: string; value: string }): void }>();

const fieldNodes = computed(() => (Array.isArray(props.group.fields) ? props.group.fields : []));
const subGroups = computed(() => (Array.isArray(props.group.sub_groups) ? props.group.sub_groups : []));
</script>

<style scoped>
.view-group {
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 12px;
  padding: 16px;
  background: #f8fafc;
}

.view-grid {
  display: grid;
  gap: 16px 24px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 900px) {
  .view-grid {
    grid-template-columns: 1fr;
  }
}
</style>
