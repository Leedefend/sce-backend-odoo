<template>
  <section class="intake-handoff">
    <header class="intake-handoff__hero">
      <p class="intake-handoff__eyebrow">项目立项</p>
      <h1>正在进入立项表单</h1>
      <p>
        当前场景会直接交给项目表单承接面，确保字段结构与提交动作贴近业务事实层。
      </p>
    </header>

    <section class="intake-handoff__card">
      <h2>如果没有自动跳转</h2>
      <p>点击下面的按钮进入项目立项表单。</p>
      <button type="button" class="intake-handoff__button" @click="openIntakeForm">
        进入项目立项表单
      </button>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getSceneByKey } from '../app/resolvers/sceneRegistry';
import { readWorkspaceContext } from '../app/workspaceContext';
import { PROJECT_INITIATION_MENU_XMLID, PROJECT_INTAKE_SCENE_KEY } from '../app/projectCreationBaseline';

const router = useRouter();
const route = useRoute();

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
}

function resolveTargetSceneKey() {
  const scene = getSceneByKey(PROJECT_INTAKE_SCENE_KEY);
  return scene ? PROJECT_INTAKE_SCENE_KEY : PROJECT_INTAKE_SCENE_KEY;
}

function buildTargetQuery() {
  void resolveTargetSceneKey();
  return {
    scene_key: PROJECT_INTAKE_SCENE_KEY,
    menu_xmlid: PROJECT_INITIATION_MENU_XMLID,
    scene_label: '项目立项',
    intake_mode: undefined,
    context_raw: undefined,
    ...resolveWorkspaceContextQuery(),
  };
}

function openIntakeForm() {
  void router.replace({
    path: `/s/${resolveTargetSceneKey()}`,
    query: buildTargetQuery(),
  });
}

onMounted(() => {
  openIntakeForm();
});
</script>

<style scoped>
.intake-handoff {
  display: grid;
  gap: 14px;
}

.intake-handoff__hero,
.intake-handoff__card {
  border: 1px solid #dbe4f0;
  border-radius: 12px;
  background: #ffffff;
  padding: 16px;
}

.intake-handoff__eyebrow {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #2563eb;
}

.intake-handoff__hero h1,
.intake-handoff__card h2 {
  margin: 0;
  color: #111827;
}

.intake-handoff__hero p,
.intake-handoff__card p {
  margin: 8px 0 0;
  color: #4b5563;
  font-size: 14px;
}

.intake-handoff__button {
  margin-top: 12px;
  border: 1px solid #1d4ed8;
  border-radius: 8px;
  background: #1d4ed8;
  color: #ffffff;
  padding: 9px 14px;
  font-size: 14px;
  cursor: pointer;
}
</style>
