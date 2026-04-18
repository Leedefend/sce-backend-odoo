<template>
  <ul class="tree" :class="`depth-${level}`" :style="treeStyle">
    <li v-for="node in sorted" :key="nodeKey(node)">
      <div
        class="node"
        :class="{
          active: activeMenuId === node.menu_id,
          ancestor: activeParents.has(nodeKey(node)),
          disabled: isNodeDisabled(node),
          directory: hasChildren(node),
          leaf: !hasChildren(node),
          expanded: hasChildren(node) && expanded.has(nodeKey(node)),
          'level-root': level === 0,
          'level-child': level > 0,
        }"
      >
        <button v-if="node.children?.length" class="toggle" @click="toggle(nodeKey(node))">
          {{ expanded.has(nodeKey(node)) ? '▾' : '▸' }}
        </button>
        <span v-else class="toggle-spacer" aria-hidden="true"></span>
        <button
          class="label"
          :disabled="isNodeDisabled(node)"
          :title="nodeDisabledTitle(node)"
          @click="onSelect(node)"
        >
          <span class="label-copy">
            <span class="label-title">{{ nodeLabel(node) }}</span>
            <span v-if="nodeMeta(node)" class="label-meta">{{ nodeMeta(node) }}</span>
          </span>
          <span class="label-tags">
            <span v-if="nodeBadge(node)" class="badge" :class="badgeClass(node)">{{ nodeBadge(node) }}</span>
          </span>
        </button>
      </div>
      <transition name="expand">
        <MenuTree
          v-if="node.children?.length"
          v-show="expanded.has(nodeKey(node))"
          :nodes="node.children"
          :active-menu-id="activeMenuId"
          :level="level + 1"
          @select="emit('select', $event)"
        />
      </transition>
    </li>
  </ul>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watchEffect } from 'vue';
import type { ExplainedMenuNode } from '../types/navigation';
import { useSessionStore } from '../stores/session';

const props = withDefaults(defineProps<{
  nodes: ExplainedMenuNode[];
  activeMenuId?: number;
  level?: number;
}>(), {
  activeMenuId: undefined,
  level: 0,
});
const emit = defineEmits<{ (e: 'select', node: ExplainedMenuNode): void }>();

const session = useSessionStore();
const expanded = computed(() => new Set(session.menuExpandedKeys));
const activeParents = ref<Set<string>>(new Set());

const sorted = computed(() => props.nodes || []);

const level = computed(() => Number(props.level || 0));
const treeStyle = computed<Record<string, string>>(() => {
  if (level.value <= 0) return {};
  return {
    marginLeft: '12px',
    paddingLeft: '12px',
    borderLeft: '1px dashed #dbe3ee',
  };
});

function toggle(key: string) {
  session.toggleMenuExpanded(key);
}

function nodeKey(node: ExplainedMenuNode) {
  return String(node.key || `menu_${node.menu_id || 0}`);
}

function nodeLabel(node: ExplainedMenuNode) {
  const raw = String(node.name || 'Unnamed');
  return raw
    .replace(/\s*\(\d+\)\s*$/g, '')
    .replace(/^project\s*manager$/i, '项目经理')
    .replace(/^purchase\s*manager$/i, '采购经理')
    .replace(/^finance$/i, '财务主管')
    .replace(/^executive$/i, '管理层')
    .replace(/^ops$/i, '运维专员')
    .replace(/^admin$/i, '系统管理员')
    .replace(/^workbench$/i, '工作台')
    .replace(/^dashboard$/i, '看板');
}

function nodeBadge(node: ExplainedMenuNode) {
  if (node.target_type === 'native') return '原生';
  if (node.target_type === 'unavailable') return '不可用';
  if (node.target_type === 'directory') return '目录';
  return '';
}

function nodeMeta(node: ExplainedMenuNode) {
  if (node.target_type === 'directory' && node.children?.length) {
    return `${node.children.length} 项`;
  }
  return '';
}

function badgeClass(node: ExplainedMenuNode) {
  return node.target_type === 'unavailable' ? 'badge--preview' : 'badge--stable';
}

function hasChildren(node: ExplainedMenuNode) {
  return Array.isArray(node.children) && node.children.length > 0;
}

function onSelect(node: ExplainedMenuNode) {
  if (isNodeDisabled(node)) {
    return;
  }
  if (node.target_type === 'directory' && node.children?.length) {
    toggle(nodeKey(node));
    return;
  }
  emit('select', node);
}

function ensureExpandedForActive(nodes: ExplainedMenuNode[], menuId?: number): Set<string> {
  if (!menuId) {
    return new Set();
  }
  const next = new Set<string>();
  const walk = (items: ExplainedMenuNode[], parents: string[] = []) => {
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

function isNodeDisabled(node: ExplainedMenuNode) {
  if (node.is_visible === false) {
    return true;
  }
  if (node.is_clickable === false) {
    return true;
  }
  return node.target_type === 'unavailable';
}

function nodeDisabledTitle(node: ExplainedMenuNode) {
  if (node.target_type === 'unavailable') {
    return node.reason_code ? `不可用：${node.reason_code}` : '不可用菜单';
  }
  if (node.is_clickable === false) {
    return '当前节点不可点击';
  }
  return undefined;
}

// 调试：打印接收到的节点
onMounted(() => {
  if (import.meta.env.DEV) {
    console.info('[MenuTree] Received nodes:', props.nodes.length);
    if (props.nodes.length > 0) {
      console.info('[MenuTree] First node:', {
        key: props.nodes[0].key,
        name: props.nodes[0].name,
        menu_id: props.nodes[0].menu_id,
        children: props.nodes[0].children?.length || 0,
        target_type: props.nodes[0].target_type,
        route: props.nodes[0].route,
      });
    }
  }
});
</script>

<style scoped>
.tree {
  list-style: none;
  padding-left: 0;
  margin: 0;
  display: grid;
  gap: 6px;
}

.node {
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
}

.node::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 7px;
  bottom: 7px;
  width: 2px;
  border-radius: 999px;
  background: transparent;
}

.label {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.16);
  text-align: left;
  cursor: pointer;
  color: #0f172a;
  width: 100%;
  justify-content: space-between;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.node.active .label {
  font-weight: 600;
  color: #173b78;
  background: linear-gradient(135deg, rgba(224, 242, 254, 0.96), rgba(255, 255, 255, 0.98));
  border-color: rgba(56, 189, 248, 0.34);
  box-shadow: 0 16px 28px rgba(14, 116, 144, 0.14);
}

.node.active::before {
  background: linear-gradient(180deg, #0284c7, #38bdf8);
}

.node.ancestor .label {
  color: #334155;
  border-color: rgba(96, 165, 250, 0.24);
  background: rgba(241, 245, 249, 0.9);
}

.node.ancestor::before {
  background: rgba(125, 211, 252, 0.7);
}

.node.disabled .label {
  cursor: not-allowed;
  color: #94a3b8;
  background: rgba(248, 250, 252, 0.92);
  box-shadow: none;
}

.node.disabled .label:hover {
  background-color: transparent;
}

.node.directory .label {
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.96), rgba(255, 255, 255, 0.98));
}

.node.directory.level-root .label {
  border-radius: 14px;
  padding-top: 10px;
  padding-bottom: 10px;
}

.node.leaf .label {
  background: rgba(255, 255, 255, 0.86);
}

.node.expanded .label {
  border-color: rgba(59, 130, 246, 0.24);
}

.toggle {
  width: 20px;
  border: none;
  background: rgba(255, 255, 255, 0.76);
  cursor: pointer;
  color: #64748b;
  font-size: 12px;
  border-radius: 999px;
  height: 20px;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.18);
}

.toggle-spacer {
  width: 20px;
  display: inline-block;
  flex: 0 0 20px;
}

.label {
  padding: 8px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;
  transition: background-color 0.2s, border-color 0.2s, box-shadow 0.2s, transform 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.label:hover {
  background-color: #f8fafc;
  border-color: rgba(59, 130, 246, 0.2);
  transform: translateX(1px);
}

.label-copy {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.label-title {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.label-meta {
  font-size: 11px;
  color: #64748b;
}

.label-tags {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.badge--stable {
  background: #e0f2fe;
  color: #0369a1;
}

.badge--preview {
  background: #fef3c7;
  color: #b45309;
}

.depth-0 {
  gap: 8px;
}

.depth-0 > li + li {
  margin-top: 2px;
}

.depth-1,
.depth-2,
.depth-3,
.depth-4 {
  gap: 4px;
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.label--leaf-preview {
  color: #7c4a03;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.badge--stable {
  background: #e8f1ff;
  color: #2454a6;
}

.badge--preview {
  background: #fff2d8;
  color: #9a5a00;
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
