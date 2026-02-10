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
  entries: Array<{ label: string; value?: string | number | null }>;
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
  background: rgba(15, 23, 42, 0.92);
  color: #e2e8f0;
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.4);
  z-index: 10;
}

.hud h3 {
  margin: 0 0 10px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #f8fafc;
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
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(15, 23, 42, 0.45);
  color: #e2e8f0;
  border-radius: 8px;
  padding: 4px 8px;
  font-size: 11px;
  cursor: pointer;
}

.message {
  margin: 0 0 8px;
  font-size: 11px;
  color: #cbd5e1;
}

.row {
  display: grid;
  gap: 4px;
}

.label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94a3b8;
}

.value {
  font-size: 12px;
  word-break: break-all;
}
</style>
