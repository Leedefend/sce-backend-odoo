<template>
  <section class="release-entry">
    <header class="hero">
      <p class="eyebrow">产品切片入口</p>
      <h1>{{ product.title }}</h1>
      <p class="description">{{ product.description }}</p>
      <p class="scope">{{ product.scope }}</p>
    </header>

    <section class="actions">
      <button v-if="recentProjectId" class="primary" @click="openRecentProject">继续最近项目</button>
      <button class="ghost" @click="openProjectsIntake">新建项目</button>
      <button class="ghost" @click="openProjectList">选择已有项目</button>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

type ProductDescriptor = {
  title: string;
  description: string;
  scope: string;
};

const PRODUCT_TEXT: Record<string, ProductDescriptor> = {
  fr2: {
    title: 'FR-2 项目推进',
    description: '从项目上下文进入驾驶舱、计划和执行链路。',
    scope: '范围固定为 项目创建 -> 驾驶舱 -> 计划 -> 执行。',
  },
  fr3: {
    title: 'FR-3 成本记录',
    description: '在项目执行上下文中录入和查看成本记录与汇总。',
    scope: '范围固定为 项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本记录 -> 成本汇总。',
  },
  fr4: {
    title: 'FR-4 付款记录',
    description: '在项目执行与成本链路基础上进入付款记录和汇总。',
    scope: '范围固定为 项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本 -> 付款记录 -> 付款汇总。',
  },
  fr5: {
    title: 'FR-5 结算结果',
    description: '基于当前项目的成本与付款数据查看只读结算汇总。',
    scope: '范围固定为 项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本 -> 付款 -> 结算结果。',
  },
};

const router = useRouter();
const route = useRoute();

const productKey = computed(() => String(route.params.productKey || '').trim().toLowerCase());
const product = computed<ProductDescriptor>(() => {
  return PRODUCT_TEXT[productKey.value] ?? {
    title: '产品入口',
    description: '当前产品切片需要项目上下文后才能继续。',
    scope: '请先新建项目，或从已有项目继续。',
  };
});
const recentProjectId = computed(() => {
  if (typeof window === 'undefined') return '';
  return String(window.localStorage.getItem('sc_last_project_id') || '').trim();
});

function openProjectsIntake() {
  router.push('/s/projects.intake').catch(() => {});
}

function openProjectList() {
  router.push({
    path: '/s/projects.list',
    query: productKey.value ? { release_product: productKey.value } : {},
  }).catch(() => {});
}

function openRecentProject() {
  if (!recentProjectId.value) {
    openProjectsIntake();
    return;
  }
  router.push({
    path: '/s/project.management',
    query: {
      project_id: recentProjectId.value,
      ...(productKey.value ? { release_product: productKey.value } : {}),
    },
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
