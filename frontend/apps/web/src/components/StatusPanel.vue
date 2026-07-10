<template>
  <section class="panel" :class="variant">
    <h2>{{ title }}</h2>
    <p v-if="message">{{ message }}</p>
    <p v-if="variant === 'error' && userHint" class="error-help">{{ userHint }}</p>
    <p v-if="variant === 'error' && !showHudMeta && compactContext" class="error-context">
      上下文：{{ compactContext }}
    </p>
    <div v-if="variant === 'error' && showHudMeta" class="error-meta">
      <p class="trace">错误码：{{ errorCode ?? '无' }}</p>
      <p class="trace">追踪 ID：{{ traceId || '无' }}</p>
      <p v-if="reasonCode" class="trace">原因：{{ reasonCode }}</p>
      <p v-if="errorCategory" class="trace">分类：{{ errorCategory }}</p>
      <p v-if="errorModel" class="trace">模型：{{ errorModel }}</p>
      <p v-if="errorOp" class="trace">操作：{{ errorOp }}</p>
      <p v-if="retryable !== undefined" class="trace">可重试：{{ retryable ? '是' : '否' }}</p>
      <p v-if="hint" class="trace">提示：{{ hint }}</p>
      <button v-if="traceId" class="trace-copy" @click="copyTrace">复制追踪 ID</button>
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
    <button v-if="onRetry" @click="onRetry">重试</button>
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
      actionRunFeedback.value = result.success ? '建议操作已执行。' : '建议操作未能执行。';
      emit('action-executed', { action: result.raw || result.kind, success: result.success });
    },
  });
  if (!ran && !actionRunFeedback.value) {
    actionRunFeedback.value = '当前上下文无法执行建议操作。';
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

.error-context {
  margin: 0;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.trace {
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

button {
  justify-self: start;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
  cursor: pointer;
}

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
</style>
