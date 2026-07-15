<template>
  <section class="panel sc-state-panel" :class="[variant, `state-${productState.kind}`]" :role="variant === 'error' ? 'alert' : 'status'" :aria-live="variant === 'error' ? 'assertive' : 'polite'" :aria-busy="busy || undefined">
    <h2 v-if="!hideTitle">{{ displayTitle }}</h2>
    <p v-if="displayMessage">{{ displayMessage }}</p>
    <div v-if="busy" class="state-skeleton" aria-hidden="true"><span /><span /><span /></div>
    <div v-if="variant === 'error' && showHudMeta" class="error-meta">
      <p class="trace">Error code: {{ errorCode ?? 'N/A' }}</p>
      <p class="trace">Trace: {{ traceId || 'N/A' }}</p>
      <p v-if="reasonCode" class="trace">Reason: {{ reasonCode }}</p>
      <p v-if="errorCategory" class="trace">Category: {{ errorCategory }}</p>
      <p v-if="errorModel" class="trace">Model: {{ errorModel }}</p>
      <p v-if="errorOp" class="trace">Operation: {{ errorOp }}</p>
      <p v-if="retryable !== undefined" class="trace">Retryable: {{ retryable ? 'yes' : 'no' }}</p>
      <p v-if="hint" class="trace">Hint: {{ hint }}</p>
      <button v-if="traceId" class="trace-copy sc-btn sc-btn-ghost sc-btn-sm" @click="copyTrace">复制诊断编号</button>
      <button v-if="canRunSuggestedAction && suggestedActionLabel" class="trace-copy" @click="runSuggestedAction">
        {{ suggestedActionLabel }}
      </button>
      <p v-if="actionRunFeedback" class="trace action-feedback">{{ actionRunFeedback }}</p>
    </div>
    <button
      v-else-if="variant === 'error' && canRunSuggestedAction && suggestedActionLabel"
      class="trace-copy sc-btn sc-btn-ghost"
      @click="runSuggestedAction"
    >
      {{ suggestedActionLabel }}
    </button>
    <button v-if="onRetry" class="sc-btn sc-btn-primary" type="button" :disabled="retrying" @click="retry">
      {{ retrying ? '正在重试…' : (retryLabel || productState.actionLabel) }}
    </button>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useSuggestedAction } from '../composables/useSuggestedAction';
import { isHudEnabled } from '../config/debug';
import { resolveProductErrorState } from '../app/productErrorState';

const props = defineProps<{
  title: string;
  message?: string;
  traceId?: string;
  errorCode?: number | string | null;
  reasonCode?: string;
  errorCategory?: string;
  errorDetails?: Record<string, unknown>;
  retryable?: boolean;
  hint?: string;
  suggestedAction?: string;
  variant?: 'error' | 'info' | 'forbidden_capability';
  onRetry?: () => void;
  onSuggestedAction?: (action: string) => boolean | void;
  hideTitle?: boolean;
  retryLabel?: string;
  busy?: boolean;
}>();
const emit = defineEmits<{
  (event: 'action-executed', payload: { action: string; success: boolean }): void;
}>();
const actionRunFeedback = ref('');
const retrying = ref(false);
const route = useRoute();

watch(
  () => [props.suggestedAction, props.message, props.reasonCode, props.traceId],
  () => {
    actionRunFeedback.value = '';
  },
);

const suggestedActionRuntime = useSuggestedAction(
  () => props.suggestedAction,
  computed(() => ({
    hasRetryHandler: typeof props.onRetry === 'function',
    hasActionHandler: typeof props.onSuggestedAction === 'function',
    traceId: props.traceId,
    reasonCode: props.reasonCode,
    message: props.message,
  })),
);

const canRunSuggestedAction = computed(() => suggestedActionRuntime.canRun.value);
const suggestedActionLabel = computed(() => suggestedActionRuntime.label.value);
const showHudMeta = computed(() => isHudEnabled(route));
const errorModel = computed(() => String(props.errorDetails?.model || '').trim());
const errorOp = computed(() => String(props.errorDetails?.op || '').trim().toLowerCase());
const productState = computed(() => resolveProductErrorState({ status: props.errorCode, message: props.message, reasonCode: props.reasonCode }));
const displayTitle = computed(() => (props.variant === 'error' ? productState.value.title : props.title));
const displayMessage = computed(() => (props.variant === 'error' ? productState.value.message : props.message));

function runSuggestedAction() {
  const ran = suggestedActionRuntime.run({
    onRetry: props.onRetry,
    onSuggestedAction: props.onSuggestedAction,
    traceId: props.traceId,
    reasonCode: props.reasonCode,
    message: props.message,
    onExecuted: (result) => {
      actionRunFeedback.value = result.success ? '恢复操作已执行。' : '当前无法执行恢复操作。';
      emit('action-executed', { action: result.raw || result.kind, success: result.success });
    },
  });
  if (!ran && !actionRunFeedback.value) {
    actionRunFeedback.value = '当前状态无法执行此恢复操作。';
  }
}

async function retry() {
  if (!props.onRetry || retrying.value) return;
  retrying.value = true;
  try { await props.onRetry(); } finally { retrying.value = false; }
}

function copyTrace() {
  if (!props.traceId) {
    return;
  }
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(props.traceId).catch(() => {});
  }
}
</script>

<style scoped>
.panel {
  padding: 24px;
  border-radius: var(--sc-product-radius-panel);
  background: var(--sc-app-muted-bg);
  border: 1px solid var(--sc-app-border);
  color: var(--sc-app-text-primary);
  display: grid;
  gap: 8px;
}

.panel.error {
  border-color: var(--sc-app-danger-border);
  background: var(--sc-app-danger-bg);
}

.panel.forbidden_capability {
  border-color: var(--sc-app-warning-border);
  background: var(--sc-app-warning-bg);
}

.error-meta {
  display: grid;
  gap: 4px;
}

.trace {
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.panel > button { justify-self: start; }

.trace-copy {
  justify-self: start;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid var(--sc-app-border);
  background: transparent;
  color: var(--sc-app-text-primary);
  font-size: 12px;
}

.action-feedback {
  color: var(--sc-app-text-primary);
}

.state-skeleton { display: grid; gap: var(--sc-product-space-1); width: min(520px, 100%); }
.state-skeleton span { display: block; height: 12px; border-radius: var(--sc-product-radius-control); background: var(--sc-app-border); animation: state-pulse 1.2s ease-in-out infinite alternate; }
.state-skeleton span:nth-child(2) { width: 82%; }
.state-skeleton span:nth-child(3) { width: 64%; }
@keyframes state-pulse { to { opacity: .45; } }
@media (prefers-reduced-motion: reduce) { .state-skeleton span { animation: none; } }
</style>
