<template>
  <section class="panel" :class="variant">
    <h2>{{ title }}</h2>
    <p v-if="message">{{ message }}</p>
    <p v-if="variant === 'error' && userHint" class="error-help">{{ userHint }}</p>
    <p v-if="variant === 'error' && !showHudMeta && compactContext" class="error-context">
      上下文：{{ compactContext }}
    </p>
    <div v-if="variant === 'error' && showHudMeta" class="error-meta">
      <p class="trace">处理状态：{{ errorCode ?? '无' }}</p>
      <p class="trace">处理编号：{{ traceId || '无' }}</p>
      <p v-if="reasonCode" class="trace">原因：{{ reasonLabel }}</p>
      <p v-if="errorCategory" class="trace">分类：{{ errorCategory }}</p>
      <p v-if="errorModel" class="trace">业务对象：{{ errorModel }}</p>
      <p v-if="errorOp" class="trace">操作：{{ errorOp }}</p>
      <p v-if="retryable !== undefined" class="trace">可重试：{{ retryable ? '是' : '否' }}</p>
      <p v-if="hint" class="trace">提示：{{ hint }}</p>
      <button v-if="traceId" class="trace-copy" @click="copyTrace">复制处理编号</button>
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
const reasonLabel = computed(() => resolveStatusReasonLabel(props.reasonCode));
const operationLabel = computed(() => resolveStatusOperationLabel(errorOp.value));
const compactContext = computed(() => {
  const reason = reasonLabel.value;
  const operation = operationLabel.value;
  if (operation && props.reasonCode) return `${operation} · ${reason}`;
  if (operation) return operation;
  if (props.reasonCode) return reason;
  return '';
});
const userHint = computed(() => {
  if (showHudMeta.value) return '';
  return props.hint || '';
});

function resolveStatusReasonLabel(reason: unknown): string {
  const raw = String(reason || '').trim();
  const key = raw.toUpperCase();
  const mapping: Record<string, string> = {
    ACTION_UNSUPPORTED: '当前操作暂不可用',
    EXECUTE_FAILED: '操作未完成',
    PERMISSION_DENIED: '权限不足',
    ACCESS_DENIED: '权限不足',
    NOT_FOUND: '记录不存在',
    BUSINESS_RULE_FAILED: '业务规则限制',
    VALIDATION_ERROR: '校验未通过',
    MISSING_PARAMS: '参数不完整',
    CONFLICT: '数据已变化',
    NETWORK_ERROR: '网络连接问题',
    SYSTEM_ERROR: '系统处理问题',
    INTERNAL_ERROR: '系统处理问题',
    UNKNOWN: '待确认',
  };
  if (!raw) return '待确认';
  return mapping[key] || raw.replace(/[_-]+/g, ' ').toLowerCase().replace(/(^|\s)\S/g, (s) => s.toUpperCase());
}

function resolveStatusOperationLabel(op: unknown): string {
  const raw = String(op || '').trim().toLowerCase();
  const mapping: Record<string, string> = {
    read: '数据读取',
    search: '数据查询',
    search_read: '数据查询',
    load: '页面加载',
    write: '数据保存',
    create: '数据新增',
    unlink: '数据删除',
    delete: '数据删除',
    execute: '业务操作',
    action: '业务操作',
    export: '数据导出',
    export_csv: '数据导出',
    import: '数据导入',
  };
  return mapping[raw] || '';
}

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
