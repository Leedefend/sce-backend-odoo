<template>
  <section class="workbench">
    <header class="header">
      <div>
        <h2>Workbench</h2>
        <p class="meta">Safe landing for non-standard navigation targets.</p>
      </div>
      <div class="actions">
        <button class="ghost" @click="refresh">Refresh</button>
      </div>
    </header>

    <StatusPanel
      title="Workspace ready"
      :message="message"
      :variant="panelVariant"
    />

    <div class="details">
      <div class="detail">
        <span class="label">Reason</span>
        <span class="value">{{ reasonLabel }}</span>
      </div>
      <div class="detail">
        <span class="label">Menu</span>
        <span class="value">{{ menuId || 'N/A' }}</span>
      </div>
      <div class="detail">
        <span class="label">Action</span>
        <span class="value">{{ actionId || 'N/A' }}</span>
      </div>
      <div class="detail">
        <span class="label">Route</span>
        <span class="value">{{ route.fullPath }}</span>
      </div>
      <div v-if="showHud" class="detail">
        <span class="label">Last Intent</span>
        <span class="value">{{ lastIntent || 'N/A' }}</span>
      </div>
      <div v-if="showHud" class="detail">
        <span class="label">Trace</span>
        <span class="value">
          {{ lastTraceId || 'N/A' }}
          <button v-if="lastTraceId" class="ghost mini" @click="copyTrace">Copy</button>
        </span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { ErrorCodes } from '../app/error_codes';
import { useSessionStore } from '../stores/session';
import { isHudEnabled } from '../config/debug';

const route = useRoute();

const reason = computed(() => String(route.query.reason || ''));
const menuId = computed(() => Number(route.query.menu_id || 0) || undefined);
const actionId = computed(() => Number(route.query.action_id || 0) || undefined);
const session = useSessionStore();
const showHud = computed(() => isHudEnabled(route));
const lastTraceId = computed(() => session.lastTraceId || '');
const lastIntent = computed(() => session.lastIntent || '');

const reasonLabel = computed(() => {
  switch (reason.value) {
    case ErrorCodes.NAV_MENU_NO_ACTION:
      return 'Menu group (no action)';
    case ErrorCodes.ACT_NO_MODEL:
      return 'Action has no model';
    case ErrorCodes.ACT_UNSUPPORTED_TYPE:
      return 'Action type not supported';
    case ErrorCodes.CAPABILITY_MISSING:
      return 'Capability missing';
    default:
      return reason.value || 'Unknown';
  }
});

const message = computed(() => {
  switch (reason.value) {
    case ErrorCodes.NAV_MENU_NO_ACTION:
      return 'This menu is a directory. Select a submenu to continue.';
    case ErrorCodes.ACT_NO_MODEL:
      return 'This action opens a custom workspace without a model.';
    case ErrorCodes.ACT_UNSUPPORTED_TYPE:
      return 'This action type is not yet supported in the portal shell.';
    case ErrorCodes.CAPABILITY_MISSING:
      return 'This capability is not enabled for your account.';
    default:
      return 'Use the menu to continue.';
  }
});

const panelVariant = computed(() => {
  if (reason.value === ErrorCodes.CAPABILITY_MISSING) {
    return 'forbidden_capability';
  }
  return 'info';
});

function refresh() {
  window.location.reload();
}

async function copyTrace() {
  if (!lastTraceId.value) return;
  try {
    await navigator.clipboard.writeText(lastTraceId.value);
  } catch {
    // noop
  }
}
</script>

<style scoped>
.workbench {
  display: grid;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions {
  display: flex;
  gap: 8px;
}

.meta {
  color: #64748b;
  font-size: 14px;
}

.details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.detail {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 4px;
}

.ghost.mini {
  margin-left: 8px;
  padding: 4px 8px;
  font-size: 12px;
}

.label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94a3b8;
}

.value {
  font-weight: 600;
}

.ghost {
  background: transparent;
  color: #111827;
  border: 1px solid rgba(15, 23, 42, 0.12);
  padding: 10px 14px;
  border-radius: 10px;
  cursor: pointer;
}
</style>
