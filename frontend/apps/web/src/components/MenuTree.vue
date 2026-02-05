<template>
  <ul class="tree">
    <li v-for="node in sorted" :key="nodeKey(node)">
      <div
        class="node"
        :class="{
          active: activeMenuId === (node.menu_id ?? node.id),
          ancestor: activeParents.has(nodeKey(node)),
          disabled: isBlocked(node),
        }"
      >
        <button v-if="node.children?.length" class="toggle" @click="toggle(nodeKey(node))">
          {{ expanded.has(nodeKey(node)) ? '▾' : '▸' }}
        </button>
        <button
          class="label"
          :disabled="isBlocked(node)"
          :title="blockedTitle(node)"
          @click="onSelect(node)"
        >
          {{ node.title || node.name || node.label || 'Unnamed' }}
          <span v-if="node.children?.length" class="child-count">({{ node.children.length }})</span>
        </button>
      </div>
      <transition name="expand">
        <MenuTree
          v-if="node.children?.length"
          v-show="expanded.has(nodeKey(node))"
          :nodes="node.children"
          :active-menu-id="activeMenuId"
          @select="emit('select', $event)"
        />
      </transition>
    </li>
  </ul>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watchEffect } from 'vue';
import type { NavNode } from '@sc/schema';
import { capabilityTooltip, evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { useSessionStore } from '../stores/session';

const props = defineProps<{ nodes: NavNode[]; activeMenuId?: number; capabilities?: string[] }>();
const emit = defineEmits<{ (e: 'select', node: NavNode): void }>();

const session = useSessionStore();
const expanded = computed(() => new Set(session.menuExpandedKeys));
const activeParents = ref<Set<string>>(new Set());

const sorted = computed(() => {
  return [...props.nodes].sort((a, b) => {
    const seqA = a.meta?.sequence ?? 0;
    const seqB = b.meta?.sequence ?? 0;
    return seqA - seqB;
  });
});

function toggle(key: string) {
  session.toggleMenuExpanded(key);
}

function nodeKey(node: NavNode) {
  return (node as NavNode & { xmlid?: string }).xmlid || node.key || `menu_${node.menu_id || node.id}`;
}

function onSelect(node: NavNode) {
  if (isBlocked(node)) {
    return;
  }
  emit('select', node);
}

function ensureExpandedForActive(nodes: NavNode[], menuId?: number): Set<string> {
  if (!menuId) {
    return new Set();
  }
  const next = new Set<string>();
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
  const parents = ensureExpandedForActive(props.nodes, props.activeMenuId);
  if (parents.size) {
    session.ensureMenuExpanded([...parents]);
  }
  activeParents.value = parents;
});

function isBlocked(node: NavNode) {
  return evaluateCapabilityPolicy({ source: node.meta, available: props.capabilities }).state !== 'enabled';
}

function blockedTitle(node: NavNode) {
  const policy = evaluateCapabilityPolicy({ source: node.meta, available: props.capabilities });
  const tip = capabilityTooltip(policy);
  return tip || undefined;
}

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

.node.ancestor .label {
  color: #64748b;
}

.node.disabled .label {
  cursor: not-allowed;
  color: #94a3b8;
}

.node.disabled .label:hover {
  background-color: transparent;
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

.expand-enter-active,
.expand-leave-active {
  transition: all 0.18s ease;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
