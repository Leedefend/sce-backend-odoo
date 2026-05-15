<template>
  <aside v-if="visible" class="hud">
    <h3>{{ title }}</h3>
    <div v-if="actions?.length" class="actions">
      <button
        v-for="action in actions"
        :key="action.key"
        type="button"
        class="action-btn"
        @click="action.onClick()"
      >
        {{ action.label }}
      </button>
    </div>
    <p v-if="message" class="message">{{ message }}</p>
    <div class="grid">
      <div v-for="entry in entries" :key="entry.label" class="row">
        <span class="label">{{ entry.label }}</span>
        <span class="value">{{ entry.value || '-' }}</span>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
defineProps<{
  title?: string;
  entries: Array<{ label: string; value?: unknown }>;
  actions?: Array<{ key: string; label: string; onClick: () => void }>;
  message?: string;
  visible: boolean;
}>();
</script>

<style scoped>
.hud {
  position: fixed;
  right: 16px;
  bottom: 16px;
  width: 300px;
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--sc-app-text-primary);
  color: var(--sc-app-panel);
  border: 1px solid var(--sc-app-border-strong);
  box-shadow: var(--sc-semantic-shadow-modal);
  z-index: 10;
}

.hud h3 {
  margin: 0 0 10px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--sc-app-panel);
}

.grid {
  display: grid;
  gap: 6px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.action-btn {
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-text-secondary);
  color: var(--sc-app-panel);
  border-radius: 8px;
  padding: 4px 8px;
  font-size: 11px;
  cursor: pointer;
}

.message {
  margin: 0 0 8px;
  font-size: 11px;
  color: var(--sc-app-muted-bg);
}

.row {
  display: grid;
  gap: 4px;
}

.label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--sc-app-border-strong);
}

.value {
  font-size: 12px;
  word-break: break-all;
}
</style>
