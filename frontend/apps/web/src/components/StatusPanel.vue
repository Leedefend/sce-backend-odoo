<template>
  <section class="panel" :class="variant">
    <h2>{{ title }}</h2>
    <p v-if="message">{{ message }}</p>
    <div v-if="variant === 'error'" class="error-meta">
      <p class="trace">Error code: {{ errorCode ?? 'N/A' }}</p>
      <p class="trace">Trace: {{ traceId || 'N/A' }}</p>
      <p v-if="hint" class="trace">Hint: {{ hint }}</p>
    </div>
    <button v-if="onRetry" @click="onRetry">Retry</button>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  message?: string;
  traceId?: string;
  errorCode?: number | null;
  hint?: string;
  variant?: 'error' | 'info';
  onRetry?: () => void;
}>();
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
</style>
