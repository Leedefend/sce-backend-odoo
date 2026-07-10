<template>
  <ul class="tree" :class="[`depth-${level}`, { 'tree--root': level === 0 }]">
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
        <span v-else class="toggle-spacer" aria-hidden="true"></span>
        <button
          class="label"
          :disabled="isBlocked(node)"
          :title="blockedTitle(node)"
          @click="onSelect(node)"
        >
          <span class="label-text">{{ nodeLabel(node) }}</span>
          <span v-if="isHandlingGroup(node)" class="label-badge">办理</span>
          <span v-if="node.children?.length" class="label-count">{{ node.children.length }}</span>
        </button>
      </div>
      <transition name="expand">
        <MenuTree
          v-if="node.children?.length"
          v-show="searchActive || expanded.has(nodeKey(node))"
          :nodes="node.children"
          :active-menu-id="activeMenuId"
          :capabilities="capabilities"
          :level="level + 1"
          :search-active="searchActive"
          @select="emit('select', $event)"
        />
      </transition>
    </li>
  </ul>
</template>

<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue';
import type { NavNode } from '@sc/schema';
import { capabilityTooltip, evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { useSessionStore } from '../stores/session';

const props = withDefaults(defineProps<{ nodes: NavNode[]; activeMenuId?: number; capabilities?: string[]; level?: number; searchActive?: boolean }>(), {
  activeMenuId: undefined,
  capabilities: () => [],
  level: 0,
  searchActive: false,
});
const emit = defineEmits<{ (e: 'select', node: NavNode): void }>();

const session = useSessionStore();
const expanded = computed(() => new Set(session.menuExpandedKeys));
const activeParents = ref<Set<string>>(new Set());

const sorted = computed(() => {
  const nodes = hideDuplicateLeafBesideGroup(props.nodes);
  return [...nodes];
});

function hideDuplicateLeafBesideGroup(nodes: NavNode[]) {
  const groupLabels = new Set(
    nodes
      .filter((node) => Boolean(node.children?.length))
      .map((node) => normalizedNodeLabel(node))
      .filter(Boolean),
  );
  if (!groupLabels.size) return [...nodes];
  return nodes.filter((node) => {
    if (node.children?.length) return true;
    return !groupLabels.has(normalizedNodeLabel(node));
  });
}

const level = computed(() => Number(props.level || 0));

function toggle(key: string) {
  session.toggleMenuExpanded(key);
}

function nodeKey(node: NavNode) {
  return (node as NavNode & { xmlid?: string }).xmlid || node.key || `menu_${node.menu_id || node.id}`;
}

function nodeLabel(node: NavNode) {
  const raw = String(node.title || node.name || node.label || 'Unnamed');
  return raw
    .replace(/\s*\(\d+\)\s*$/g, '')
    .replace(/^project\s*manager$/i, '负责人')
    .replace(/^purchase\s*manager$/i, '采购经理')
    .replace(/^finance$/i, '财务主管')
    .replace(/^executive$/i, '管理层')
    .replace(/^ops$/i, '运维专员')
    .replace(/^admin$/i, '系统管理员')
    .replace(/^workbench$/i, '诊断页')
    .replace(/^dashboard$/i, '看板');
}

function normalizedNodeLabel(node: NavNode) {
  return nodeLabel(node).trim();
}

function isHandlingGroup(node: NavNode) {
  return Boolean(node.children?.length) && (
    /办理$/.test(normalizedNodeLabel(node))
    || String(node.meta?.intent_group || '').trim() === 'handling'
  );
}

function onSelect(node: NavNode) {
  if (isBlocked(node)) {
    return;
  }
  if (node.children?.length && !hasNavigationTarget(node)) {
    toggle(nodeKey(node));
    return;
  }
  emit('select', node);
}

function hasNavigationTarget(node: NavNode) {
  const raw = node as NavNode & {
    action?: unknown;
    action_id?: unknown;
    actionId?: unknown;
    model?: unknown;
    route?: unknown;
    scene_key?: unknown;
    sceneKey?: unknown;
  };
  const meta = (node.meta && typeof node.meta === 'object') ? node.meta : {};
  return Boolean(
    raw.action
      || raw.action_id
      || raw.actionId
      || raw.model
      || raw.route
      || raw.scene_key
      || raw.sceneKey
      || meta.action_id
      || meta.actionId
      || meta.model
      || meta.route
      || meta.scene_key
      || meta.sceneKey,
  );
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

function ensureExpandedForDefaultGroups(nodes: NavNode[]): Set<string> {
  const next = new Set<string>();
  const walk = (items: NavNode[], insideJointAcceptance = false) => {
    for (const node of items) {
      const key = nodeKey(node);
      const label = normalizedNodeLabel(node);
      const isJointAcceptanceRoot = label === '联营项目数据核对';
      const shouldExpand = isJointAcceptanceRoot || isHandlingGroup(node) || (insideJointAcceptance && Boolean(node.children?.length));
      if (shouldExpand) {
        next.add(key);
      }
      if (node.children?.length) {
        walk(node.children, insideJointAcceptance || isJointAcceptanceRoot);
      }
    }
  };
  walk(nodes);
  return next;
}

watchEffect(() => {
  const parents = ensureExpandedForActive(props.nodes, props.activeMenuId);
  const defaults = ensureExpandedForDefaultGroups(props.nodes);
  if (defaults.size) {
    session.ensureMenuExpanded([...defaults]);
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

</script>

<style scoped>
.tree {
  list-style: none;
  padding-left: 0;
  margin: 0;
  display: grid;
  gap: 3px;
}

.tree:not(.tree--root) {
  margin-top: 3px;
  margin-bottom: 6px;
  padding-left: 0;
}

.tree.depth-1 {
  padding: 3px 0 5px 22px;
}

.tree.depth-2,
.tree.depth-3,
.tree.depth-4,
.tree.depth-5 {
  padding: 2px 0 4px 14px;
}

.node {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr);
  align-items: center;
  gap: 2px;
  min-height: 30px;
}

.label {
  background: transparent;
  border: none;
  text-align: left;
  cursor: pointer;
  color: var(--sc-app-text-primary);
  display: inline-flex;
  align-items: center;
  gap: 7px;
  max-width: 100%;
  min-width: 0;
}

.node.active .label {
  font-weight: 600;
  color: var(--sc-app-text-primary);
  background: var(--sc-app-info-bg);
  box-shadow: inset 3px 0 0 var(--sc-semantic-surface-interactive);
}

.node.ancestor .label {
  color: var(--sc-app-text-primary);
  background: var(--sc-app-subtle-bg);
}

.node.disabled .label {
  cursor: not-allowed;
  color: var(--sc-semantic-text-muted);
}

.node.disabled .label:hover {
  background-color: transparent;
}

.toggle {
  width: 22px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  color: var(--sc-semantic-text-muted);
  font-size: 12px;
  line-height: 1;
}

.toggle:hover {
  background: var(--sc-app-hover-bg);
  color: var(--sc-app-text-primary);
}

.toggle-spacer {
  width: 22px;
  display: inline-block;
  flex: 0 0 22px;
}

.label {
  width: 100%;
  min-height: 30px;
  padding: 6px 8px;
  border-radius: 7px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;
  transition: background-color 0.16s, box-shadow 0.16s, color 0.16s;
}

.tree--root > li > .node .label {
  min-height: 34px;
  padding: 7px 9px;
  font-weight: 700;
  letter-spacing: 0;
}

.depth-1 > li > .node .label {
  font-weight: 600;
}

.depth-2 > li > .node .label,
.depth-3 > li > .node .label,
.depth-4 > li > .node .label,
.depth-5 > li > .node .label {
  color: var(--sc-app-text-secondary);
}

.label-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.label-badge,
.label-count {
  flex: 0 0 auto;
  border: 1px solid var(--sc-app-border);
  color: var(--sc-app-text-secondary);
  background: var(--sc-app-subtle-bg);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  padding: 2px 4px;
}

.label-count {
  min-width: 18px;
  text-align: center;
  color: var(--sc-semantic-text-muted);
  background: var(--sc-app-panel);
}

.label:hover {
  background-color: var(--sc-app-hover-bg);
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
