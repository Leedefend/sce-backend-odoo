<template>
  <main class="page sc-page sc-product-workspace-stack" data-product-page-mode="workspace">
    <section v-if="headerActions.length" class="page-actions">
      <button
        v-for="action in headerActions"
        :key="`placeholder-header-${action.key}`"
        class="ghost"
        @click="executeHeaderAction(action.key)"
      >
        {{ action.label || action.key }}
      </button>
    </section>
    <section
      v-if="pageSectionEnabled('card', true) && pageSectionTagIs('card', 'section')"
      class="card"
      :style="pageSectionStyle('card')"
    >
      <h1>{{ pageText('title', '当前入口正在配置') }}</h1>
      <p>{{ pageText('description', '请返回工作台重新选择业务入口，或联系系统管理员确认该入口的发布状态。') }}</p>
      <button class="primary" type="button" @click="goHome">{{ pageText('action_back_home', '返回工作台') }}</button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';

const router = useRouter();
const pageContract = usePageContract('placeholder');
const pageText = pageContract.text;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const headerActions = computed(() => pageGlobalActions.value);

async function executeHeaderAction(actionKey: string) {
  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: {},
    onRefresh: async () => {},
    onFallback: async (key) => {
      if (key === 'open_landing' || key === 'open_workbench') {
        await router.push('/');
        return true;
      }
      return false;
    },
  });
  if (!handled) {
    await router.push('/').catch(() => {});
  }
}

async function goHome() {
  await router.push('/').catch(() => {});
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  display: grid;
  gap: var(--sc-product-workspace-stack-gap);
  place-items: center;
  background: var(--sc-app-muted-bg);
  font-family: "IBM Plex Sans", system-ui, sans-serif;
}

.page-actions {
  width: min(520px, 92vw);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ghost {
  padding: 8px 10px;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 8px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  cursor: pointer;
}

.primary {
  justify-self: start;
  padding: 10px 14px;
  border: none;
  border-radius: 8px;
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
  cursor: pointer;
}

.card {
  width: min(520px, 92vw);
  background: var(--sc-app-panel);
  padding: 32px;
  border-radius: 8px;
  box-shadow: var(--sc-semantic-shadow-modal);
  display: grid;
  gap: 12px;
}
</style>
