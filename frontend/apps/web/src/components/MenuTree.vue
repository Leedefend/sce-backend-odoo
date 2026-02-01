<template>
  <ul class="tree">
    <li v-for="node in sorted" :key="node.key">
      <div class="node" :class="{ active: activeKey === node.key }">
        <button v-if="node.children?.length" class="toggle" @click="toggle(node.key)">
          {{ expanded.has(node.key) ? '▾' : '▸' }}
        </button>
        <button class="label" @click="onSelect(node)">
          {{ node.label }}
        </button>
      </div>
      <MenuTree
        v-if="node.children?.length && expanded.has(node.key)"
        :nodes="node.children"
        :active-key="activeKey"
        @select="emit('select', $event)"
      />
    </li>
  </ul>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { NavNode } from '@sc/schema';

const props = defineProps<{ nodes: NavNode[]; activeKey?: string }>();
const emit = defineEmits<{ (e: 'select', node: NavNode): void }>();

const expanded = ref<Set<string>>(new Set());

const sorted = computed(() => {
  return [...props.nodes].sort((a, b) => {
    const seqA = a.meta?.sequence ?? 0;
    const seqB = b.meta?.sequence ?? 0;
    return seqA - seqB;
  });
});

function toggle(key: string) {
  if (expanded.value.has(key)) {
    expanded.value.delete(key);
  } else {
    expanded.value.add(key);
  }
}

function onSelect(node: NavNode) {
  emit('select', node);
}
</script>

<style scoped>
.tree {
  list-style: none;
  padding-left: 12px;
  margin: 0;
  display: grid;
  gap: 6px;
}

.node {
  display: flex;
  align-items: center;
  gap: 6px;
}

.label {
  background: transparent;
  border: none;
  text-align: left;
  cursor: pointer;
  color: #0f172a;
}

.node.active .label {
  font-weight: 600;
  color: #2563eb;
}

.toggle {
  width: 20px;
  border: none;
  background: transparent;
  cursor: pointer;
}
</style>
