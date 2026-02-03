<template>
  <ul class="tree">
    <li v-for="node in sorted" :key="node.key || node.menu_id">
      <div class="node" :class="{ active: activeMenuId === (node.menu_id ?? node.id) }">
        <button v-if="node.children?.length" class="toggle" @click="toggle(nodeKey(node))">
          {{ expanded.has(nodeKey(node)) ? '▾' : '▸' }}
        </button>
        <button class="label" @click="onSelect(node)">
          {{ node.title || node.name || node.label || 'Unnamed' }}
          <span v-if="node.children?.length" class="child-count">({{ node.children.length }})</span>
        </button>
      </div>
      <MenuTree
        v-if="node.children?.length && expanded.has(nodeKey(node))"
        :nodes="node.children"
        :active-menu-id="activeMenuId"
        @select="emit('select', $event)"
      />
    </li>
  </ul>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watchEffect } from 'vue';
import type { NavNode } from '@sc/schema';

const props = defineProps<{ nodes: NavNode[]; activeMenuId?: number }>();
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

function nodeKey(node: NavNode) {
  return node.key || `menu_${node.menu_id || node.id}`;
}

function onSelect(node: NavNode) {
  emit('select', node);
}

function ensureExpandedForActive(nodes: NavNode[], menuId?: number): Set<string> {
  if (!menuId) {
    return expanded.value;
  }
  const next = new Set(expanded.value);
  const walk = (items: NavNode[], parents: string[] = []) => {
    for (const node of items) {
      const key = nodeKey(node);
      if (node.menu_id === menuId) {
        parents.forEach((p) => next.add(p));
      }
      if (node.children?.length) {
        walk(node.children, [...parents, key]);
      }
    }
  };
  walk(nodes);
  return next;
}

watchEffect(() => {
  expanded.value = ensureExpandedForActive(props.nodes, props.activeMenuId);
});

// 调试：打印接收到的节点
onMounted(() => {
  if (import.meta.env.DEV) {
    console.info('[MenuTree] Received nodes:', props.nodes.length);
    if (props.nodes.length > 0) {
      console.info('[MenuTree] First node:', {
        key: props.nodes[0].key,
        name: props.nodes[0].name,
        label: props.nodes[0].label,
        menu_id: props.nodes[0].menu_id,
        children: props.nodes[0].children?.length || 0,
        meta: props.nodes[0].meta
      });
    }
  }
});
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
  color: #64748b;
}

.child-count {
  font-size: 12px;
  color: #64748b;
  margin-left: 4px;
}

.label {
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.label:hover {
  background-color: #f1f5f9;
}
</style>
