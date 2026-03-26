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
  background: white;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 16px 28px rgba(15, 23, 42, 0.08);
}

.title {
  margin: 0;
  font-size: 20px;
}

.subtitle {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.primary {
  padding: 8px 14px;
  border-radius: 10px;
  border: 0;
  background: #0f172a;
  color: #fff;
  cursor: pointer;
}

.pill {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  background: #e2e8f0;
  color: #1e293b;
}

.pill.mode {
  background: #eff6ff;
  color: #1d4ed8;
}

.pill.count {
  background: #f8fafc;
  color: #334155;
}

.pill.ok {
  background: #dcfce7;
  color: #14532d;
}

.pill.error {
  background: #fee2e2;
  color: #991b1b;
}

.pill.loading {
  background: #e0f2fe;
  color: #075985;
}

.pill.empty {
  background: #fef3c7;
  color: #92400e;
}

.ghost {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: transparent;
  color: #111827;
  cursor: pointer;
}

.primary:disabled,
.ghost:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
