<template>
  <section class="release-entry">
    <header class="hero">
      <p class="eyebrow">产品切片入口</p>
      <h1>{{ productView.title }}</h1>
      <p class="description">{{ productView.description }}</p>
      <p class="scope">{{ productView.scope }}</p>
    </header>

    <section class="actions">
      <button class="primary" @click="openRecentProject">进入项目驾驶舱</button>
      <button class="ghost" @click="openProjectsIntake">新建项目</button>
      <button class="ghost" @click="openProjectList">选择已有项目</button>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { PROJECT_INTAKE_SCENE_PATH } from '../app/projectCreationBaseline';

type ProductDescriptor = {
  title: string;
  description: string;
  scope: string;
};

const router = useRouter();
const route = useRoute();
const session = useSessionStore();

const productKey = computed(() => String(route.params.productKey || '').trim().toLowerCase());
const releasedScene = computed<Record<string, unknown>>(() => {
  const rows = session.deliveryEngineV1?.scenes;
  if (!Array.isArray(rows)) return {};
  return (
    rows.find((item) => {
      if (!item || typeof item !== 'object') return false;
      return String((item as Record<string, unknown>).product_key || '').trim().toLowerCase() === productKey.value;
    }) as Record<string, unknown> | undefined
  ) ?? {};
});
const releasedSceneContract = computed<Record<string, unknown>>(() => {
  const raw = releasedScene.value.scene_contract_standard_v1;
  return raw && typeof raw === 'object' ? raw as Record<string, unknown> : {};
});
const releasedIdentity = computed<Record<string, unknown>>(() => {
  const raw = releasedSceneContract.value.identity;
  return raw && typeof raw === 'object' ? raw as Record<string, unknown> : {};
});
const releasedState = computed<Record<string, unknown>>(() => {
  const raw = releasedSceneContract.value.state;
  return raw && typeof raw === 'object' ? raw as Record<string, unknown> : {};
});
const productView = computed<ProductDescriptor>(() => ({
  title:
    String(releasedIdentity.value.title || '').trim()
    || String(releasedScene.value.title || '').trim()
    || (productKey.value ? productKey.value.toUpperCase() : '产品入口'),
  description:
    String(releasedIdentity.value.description || '').trim()
    || String(releasedScene.value.description || '').trim()
    || String(releasedState.value.message || '').trim()
    || '查看当前产品入口说明',
  scope:
    String(releasedIdentity.value.scope || '').trim()
    || String(releasedScene.value.scope || '').trim()
    || '查看当前产品入口范围',
}));
function openProjectsIntake() {
  router.push(PROJECT_INTAKE_SCENE_PATH).catch(() => {});
}

function openProjectList() {
  router.push({
    path: '/s/projects.list',
    query: productKey.value ? { release_product: productKey.value } : {},
  }).catch(() => {});
}

function openRecentProject() {
  router.push({
    path: '/s/project.management',
  }).catch(() => {});
}
</script>

<style scoped>
.release-entry {
  display: grid;
  gap: 20px;
  padding: 28px;
  min-height: calc(100vh - 140px);
  align-content: start;
}

.hero {
  display: grid;
  gap: 10px;
  padding: 24px;
  border-radius: 20px;
  background: linear-gradient(145deg, #fffaf5 0%, #f3f7fb 100%);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.08);
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #8b5e3c;
}

.hero h1 {
  margin: 0;
  font-size: 30px;
  line-height: 1.1;
  color: #0f172a;
}

.description,
.scope {
  margin: 0;
  max-width: 720px;
  color: #475569;
  line-height: 1.6;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.primary,
.ghost {
  min-width: 160px;
  padding: 12px 18px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.primary {
  border: 0;
  color: #fff;
  background: linear-gradient(135deg, #2f3a5f, #1d4e89);
  box-shadow: 0 10px 24px rgba(47, 58, 95, 0.24);
}

.ghost {
  border: 1px solid rgba(15, 23, 42, 0.1);
  color: #0f172a;
  background: rgba(255, 255, 255, 0.9);
}
</style>
