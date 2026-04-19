<template>
  <header class="header">
    <div>
      <h2 class="title">{{ title }}</h2>
      <p class="subtitle">{{ subtitle }}</p>
    </div>
    <div class="actions">
      <button
        v-if="primaryActionLabel"
        class="primary"
        :disabled="loading"
        @click="onPrimaryAction?.()"
      >
        {{ primaryActionLabel }}
      </button>
      <span v-if="modeLabel" class="pill mode">{{ modeLabel }}</span>
      <span v-if="recordCount >= 0" class="pill count">{{ recordCount }} 条</span>
      <span class="pill" :class="status">{{ statusLabel }}</span>
      <button class="ghost" :disabled="loading" @click="onReload">刷新</button>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  subtitle: string;
  status: 'loading' | 'ok' | 'empty' | 'error';
  statusLabel: string;
  loading: boolean;
  onReload: () => void;
  primaryActionLabel?: string;
  onPrimaryAction?: () => void;
  modeLabel?: string;
  recordCount?: number;
}>();
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--ui-space-4);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 245, 239, 0.92));
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-md);
  padding: var(--ui-space-4) var(--ui-space-5);
  box-shadow: var(--ui-shadow-sm);
}

.title {
  margin: 0;
  font-size: var(--ui-font-size-xl);
  color: var(--ui-color-ink-strong);
}

.subtitle {
  margin: 6px 0 0;
  color: var(--ui-color-ink-muted);
  font-size: var(--ui-font-size-sm);
}

.actions {
  display: flex;
  gap: var(--ui-space-2);
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.primary {
  padding: 10px 16px;
  border-radius: var(--ui-radius-sm);
  border: 1px solid var(--ui-color-primary-700);
  background: var(--ui-color-primary-700);
  color: #fff;
  cursor: pointer;
  font-weight: var(--ui-font-weight-semibold);
  box-shadow: var(--ui-shadow-xs);
}

.pill {
  padding: 6px 10px;
  border-radius: var(--ui-radius-pill);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  background: rgba(93, 107, 121, 0.12);
  color: var(--ui-color-ink);
  border: 1px solid transparent;
  font-weight: var(--ui-font-weight-semibold);
}

.pill.mode {
  background: var(--ui-color-primary-050);
  color: var(--ui-color-primary-700);
}

.pill.count {
  background: rgba(255, 255, 255, 0.72);
  color: var(--ui-color-ink-muted);
  border-color: var(--ui-color-border);
}

.pill.ok {
  background: var(--ui-color-success-050);
  color: var(--ui-color-success-600);
}

.pill.error {
  background: var(--ui-color-danger-050);
  color: var(--ui-color-danger-600);
}

.pill.loading {
  background: var(--ui-color-primary-050);
  color: var(--ui-color-primary-700);
}

.pill.empty {
  background: var(--ui-color-warning-050);
  color: var(--ui-color-warning-600);
}

.ghost {
  padding: 10px 14px;
  border-radius: var(--ui-radius-sm);
  border: 1px solid var(--ui-color-border);
  background: rgba(255, 255, 255, 0.78);
  color: var(--ui-color-ink);
  cursor: pointer;
  box-shadow: var(--ui-shadow-xs);
}

.primary:disabled,
.ghost:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.primary:hover:not(:disabled),
.ghost:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--ui-shadow-sm);
}
</style>
