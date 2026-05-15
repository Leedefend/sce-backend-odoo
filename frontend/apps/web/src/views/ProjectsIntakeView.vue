<template>
  <section class="intake-page">
    <header class="intake-hero">
      <h1>项目立项</h1>
      <p>先创建项目管理对象，再在项目驾驶舱持续补充合同、成本、资金与风险信息。</p>
    </header>

    <section class="intake-grid">
      <article class="intake-card intake-card-primary">
        <h2>快速创建（推荐）</h2>
        <p>仅需项目名称与项目经理，30 秒完成项目创建。</p>
        <ul>
          <li>项目名称（必填）</li>
          <li>项目经理（必填）</li>
          <li>业主单位（可选）</li>
        </ul>
        <button type="button" class="intake-btn intake-btn-primary" @click="openQuickCreate">
          快速创建项目
        </button>
      </article>

      <article class="intake-card">
        <h2>标准立项</h2>
        <p>用于一次性补充项目标识、地点与计划日期等可选信息。</p>
        <ul>
          <li>项目编号（自动生成）</li>
          <li>项目类型 / 类别</li>
          <li>项目地点 / 计划日期</li>
        </ul>
        <button type="button" class="intake-btn" @click="openFullForm">
          进入标准立项表单
        </button>
      </article>
    </section>
  </section>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import type { NavNode } from '@sc/schema';
import { useSessionStore } from '../stores/session';
import { readWorkspaceContext } from '../app/workspaceContext';
import { getSceneByKey } from '../app/resolvers/sceneRegistry';

const FULL_CREATE_MENU_XMLID = 'smart_construction_core.menu_sc_project_initiation';

const session = useSessionStore();
const router = useRouter();
const route = useRoute();

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
}

function findNodeByMenuXmlid(nodes: NavNode[], menuXmlid: string): NavNode | null {
  for (const node of nodes || []) {
    const nodeXmlid = String(node.meta?.menu_xmlid || '').trim();
    if (nodeXmlid === menuXmlid) return node;
    if (node.children?.length) {
      const found = findNodeByMenuXmlid(node.children, menuXmlid);
      if (found) return found;
    }
  }
  return null;
}

function findNodeBySceneKey(nodes: NavNode[], sceneKey: string): NavNode | null {
  for (const node of nodes || []) {
    const nodeSceneKey = String(node.meta?.scene_key || '').trim();
    if (nodeSceneKey === sceneKey && node.meta?.action_id) return node;
    if (node.children?.length) {
      const found = findNodeBySceneKey(node.children, sceneKey);
      if (found) return found;
    }
  }
  return null;
}

function resolveIntakeActionTarget() {
  const scene = getSceneByKey('projects.intake');
  const sceneActionId = Number((scene?.target?.action_id as number) || 0);
  if (sceneActionId > 0) {
    return { actionId: sceneActionId, menuId: Number((scene?.target?.menu_id as number) || 0) || undefined };
  }
  const sceneNode = findNodeBySceneKey(session.menuTree, 'projects.intake');
  if (sceneNode?.meta?.action_id) {
    return {
      actionId: Number(sceneNode.meta.action_id),
      menuId: Number(sceneNode.menu_id || sceneNode.id || 0) || undefined,
    };
  }
  return null;
}

function openQuickCreate() {
  const workspaceContext = resolveWorkspaceContextQuery();
  const target = resolveIntakeActionTarget();
  void router.replace({
    path: '/f/project.project/new',
    query: {
      action_id: target?.actionId || undefined,
      menu_id: target?.menuId || undefined,
      scene_label: '项目立项',
      intake_mode: 'quick',
      ...workspaceContext,
    },
  });
}

function openFullForm() {
  const fullNode = findNodeByMenuXmlid(session.menuTree, FULL_CREATE_MENU_XMLID);
  const fallback = resolveIntakeActionTarget();
  if (fullNode?.meta?.action_id) {
    void router.replace({
      path: '/f/project.project/new',
      query: {
        menu_id: Number(fullNode.menu_id || fullNode.id || 0) || undefined,
        action_id: Number(fullNode.meta.action_id),
        scene_label: '项目立项',
        intake_mode: 'standard',
        context_raw: undefined,
        ...resolveWorkspaceContextQuery(),
      },
    });
    return;
  }
  if (!fallback?.actionId) return;
  void router.replace({
    path: '/f/project.project/new',
    query: {
      action_id: fallback.actionId,
      menu_id: fallback.menuId,
      scene_label: '项目立项',
      intake_mode: 'standard',
      context_raw: undefined,
      ...resolveWorkspaceContextQuery(),
    },
  });
}
</script>

<style scoped>
.intake-page {
  display: grid;
  gap: 14px;
}
.intake-hero {
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-panel);
  padding: 16px;
}
.intake-hero h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--sc-app-text-primary);
}
.intake-hero p {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--sc-app-text-secondary);
}
.intake-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.intake-card {
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-panel);
  padding: 14px;
}
.intake-card-primary {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
}
.intake-card h2 {
  margin: 0;
  font-size: 18px;
  color: var(--sc-app-text-primary);
}
.intake-card p {
  margin: 8px 0;
  font-size: 13px;
  color: var(--sc-semantic-text-muted);
}
.intake-card ul {
  margin: 0 0 12px;
  padding-left: 16px;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}
.intake-btn {
  border: 1px solid var(--sc-app-border-strong);
  border-radius: var(--sc-component-button-radius);
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  padding: 8px 14px;
  font-size: 13px;
  cursor: pointer;
}
.intake-btn-primary {
  background: var(--sc-semantic-surface-interactive);
  border-color: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
}
@media (max-width: 1080px) {
  .intake-grid {
    grid-template-columns: 1fr;
  }
}
</style>
