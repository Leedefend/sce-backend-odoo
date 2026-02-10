<template>
  <section class="panel" :class="variant">
    <h2>{{ title }}</h2>
    <p v-if="message">{{ message }}</p>
    <div v-if="variant === 'error'" class="error-meta">
      <p class="trace">Error code: {{ errorCode ?? 'N/A' }}</p>
      <p class="trace">Trace: {{ traceId || 'N/A' }}</p>
      <p v-if="reasonCode" class="trace">Reason: {{ reasonCode }}</p>
      <p v-if="errorCategory" class="trace">Category: {{ errorCategory }}</p>
      <p v-if="retryable !== undefined" class="trace">Retryable: {{ retryable ? 'yes' : 'no' }}</p>
      <p v-if="hint" class="trace">Hint: {{ hint }}</p>
      <p v-if="suggestedAction" class="trace">Suggested: {{ suggestedAction }}</p>
      <button v-if="traceId" class="trace-copy" @click="copyTrace">Copy trace</button>
    </div>
    <button v-if="onRetry" @click="onRetry">Retry</button>
  </section>
</template>

<script setup lang="ts">
const props = defineProps<{
  title: string;
  message?: string;
  traceId?: string;
  errorCode?: number | string | null;
  reasonCode?: string;
  errorCategory?: string;
  retryable?: boolean;
  hint?: string;
  suggestedAction?: string;
  variant?: 'error' | 'info' | 'forbidden_capability';
  onRetry?: () => void;
}>();

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
</style>
