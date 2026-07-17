<template>
  <main class="page sc-page sc-page-frame sc-page-frame--standard sc-product-workspace-stack" data-product-page-mode="workspace" data-page-width-mode="standard">
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
      <h1>{{ pageText('title', 'Dynamic View Placeholder') }}</h1>
      <p>{{ pageText('route_label', 'Route') }}: {{ route.path }}</p>
      <p>{{ pageText('params_label', 'Params') }}: {{ route.params }}</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';

const route = useRoute();
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

.card {
  width: min(520px, 92vw);
  background: var(--sc-app-panel);
  padding: 32px;
  border-radius: 16px;
  box-shadow: var(--sc-semantic-shadow-modal);
}
</style>
