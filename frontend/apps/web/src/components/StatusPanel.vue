<template>
  <section class="panel" :class="variant">
    <h2>{{ title }}</h2>
    <p v-if="message">{{ message }}</p>
    <p v-if="variant === 'error' && userHint" class="error-help">{{ userHint }}</p>
    <p v-if="variant === 'error' && !showHudMeta && compactContext" class="error-context">
      Context: {{ compactContext }}
    </p>
    <p v-if="variant === 'error' && !showHudMeta && compactTraceLine" class="error-context">
      {{ compactTraceLine }}
    </p>
    <div v-if="variant === 'error' && showHudMeta" class="error-meta">
      <p class="trace">Error code: {{ errorCode ?? 'N/A' }}</p>
      <p class="trace">Trace: {{ traceId || 'N/A' }}</p>
      <p v-if="reasonCode" class="trace">Reason: {{ reasonCode }}</p>
      <p v-if="errorCategory" class="trace">Category: {{ errorCategory }}</p>
      <p v-if="errorModel" class="trace">Model: {{ errorModel }}</p>
      <p v-if="errorOp" class="trace">Operation: {{ errorOp }}</p>
      <p v-if="retryable !== undefined" class="trace">Retryable: {{ retryable ? 'yes' : 'no' }}</p>
      <p v-if="hint" class="trace">Hint: {{ hint }}</p>
      <button v-if="traceId" class="trace-copy" @click="copyTrace">Copy trace</button>
      <button v-if="canRunSuggestedAction && suggestedActionLabel" class="trace-copy" @click="runSuggestedAction">
        {{ suggestedActionLabel }}
      </button>
      <p v-if="actionRunFeedback" class="trace action-feedback">{{ actionRunFeedback }}</p>
    </div>
    <button
      v-else-if="variant === 'error' && canRunSuggestedAction && suggestedActionLabel"
      class="trace-copy"
      @click="runSuggestedAction"
    >
      {{ suggestedActionLabel }}
    </button>
    <button v-if="onRetry" @click="onRetry">{{ retryButtonText }}</button>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useSuggestedAction } from '../composables/useSuggestedAction';
import { isHudEnabled } from '../config/debug';

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
  retryLabel?: string;
  variant?: 'error' | 'info' | 'forbidden_capability';
  onRetry?: () => void;
  onSuggestedAction?: (action: string) => boolean | void;
}>();
const emit = defineEmits<{
  (event: 'action-executed', payload: { action: string; success: boolean }): void;
}>();
const actionRunFeedback = ref('');
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
const compactContext = computed(() => {
  const scope = [errorModel.value, errorOp.value].filter(Boolean).join('/');
  const reason = String(props.reasonCode || '').trim().toUpperCase();
  if (scope && reason) return `${scope} [${reason}]`;
  if (scope) return scope;
  if (reason) return `[${reason}]`;
  return '';
});
const compactTraceLine = computed(() => {
  const code = props.errorCode !== null && props.errorCode !== undefined ? String(props.errorCode) : '';
  const trace = String(props.traceId || '').trim();
  if (code && trace) return `错误码：${code} · TraceID：${trace}`;
  if (code) return `错误码：${code}`;
  if (trace) return `TraceID：${trace}`;
  return '';
});
const retryButtonText = computed(() => String(props.retryLabel || '').trim() || '重试');
const userHint = computed(() => {
  if (showHudMeta.value) return '';
  return props.hint || '';
});

function runSuggestedAction() {
  const ran = suggestedActionRuntime.run({
    onRetry: props.onRetry,
    onSuggestedAction: props.onSuggestedAction,
    traceId: props.traceId,
    reasonCode: props.reasonCode,
    message: props.message,
    onExecuted: (result) => {
      actionRunFeedback.value = result.success ? '建议操作已执行。' : '建议操作执行失败。';
      emit('action-executed', { action: result.raw || result.kind, success: result.success });
    },
  });
  if (!ran && !actionRunFeedback.value) {
    actionRunFeedback.value = '当前上下文不支持执行建议操作。';
  }
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
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #0f172a;
  display: grid;
  gap: 8px;
}

.panel.error {
  border-color: #fecaca;
  background: #fff1f2;
}

.panel.forbidden_capability {
  border-color: #fde68a;
  background: #fffbeb;
}

.error-meta {
  display: grid;
  gap: 4px;
}

.error-context {
  margin: 0;
  font-size: 12px;
  color: #475569;
}

.trace {
  font-size: 12px;
  color: #64748b;
}

button {
  justify-self: start;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: #111827;
  color: white;
  cursor: pointer;
}

.trace-copy {
  justify-self: start;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: transparent;
  color: #111827;
  font-size: 12px;
}

.action-feedback {
  color: #334155;
}
</style>
