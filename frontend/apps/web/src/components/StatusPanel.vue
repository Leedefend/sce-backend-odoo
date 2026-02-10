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
      <button v-if="suggestedActionLabel" class="trace-copy" @click="runSuggestedAction">
        {{ suggestedActionLabel }}
      </button>
    </div>
    <button v-if="onRetry" @click="onRetry">Retry</button>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';

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
  onSuggestedAction?: (action: string) => boolean | void;
}>();

function normalizeSuggestedAction(value?: string) {
  return String(value || '').trim().toLowerCase();
}

type SuggestedActionKind =
  | 'refresh'
  | 'retry'
  | 'relogin'
  | 'check_permission'
  | 'open_record'
  | 'open_scene'
  | 'open_url'
  | '';

type SuggestedActionParsed = {
  kind: SuggestedActionKind;
  raw: string;
  model?: string;
  recordId?: number;
  sceneKey?: string;
  url?: string;
};

function parseSuggestedAction(value?: string): SuggestedActionParsed {
  const raw = normalizeSuggestedAction(value);
  if (!raw) return { kind: '', raw: '' };
  if (raw === 'refresh' || raw === 'refresh_list') return { kind: 'refresh', raw };
  if (raw === 'retry' || raw === 'retry_later') return { kind: 'retry', raw };
  if (raw === 'relogin' || raw === 'login_again') return { kind: 'relogin', raw };
  if (raw === 'check_permission' || raw === 'request_permission') return { kind: 'check_permission', raw };
  if (raw === 'open_record') return { kind: 'open_record', raw };
  if (raw.startsWith('open_record:')) {
    const parts = raw.split(':');
    if (parts.length >= 3) {
      const recordId = Number(parts[2]);
      if (parts[1] && Number.isFinite(recordId) && recordId > 0) {
        return { kind: 'open_record', raw, model: parts[1], recordId };
      }
    }
  }
  if (raw.startsWith('open_scene:')) {
    const sceneKey = raw.slice('open_scene:'.length).trim();
    if (sceneKey) return { kind: 'open_scene', raw, sceneKey };
  }
  if (raw.startsWith('open_url:')) {
    const url = raw.slice('open_url:'.length).trim();
    if (url.startsWith('/')) return { kind: 'open_url', raw, url };
  }
  return { kind: '', raw };
}

function safeNavigate(path: string) {
  if (!path.startsWith('/')) return;
  window.location.href = path;
}

const canRunSuggestedAction = computed(() => {
  const parsed = parseSuggestedAction(props.suggestedAction);
  if (!parsed.kind) return false;
  if (parsed.kind === 'refresh' || parsed.kind === 'retry') return typeof props.onRetry === 'function';
  if (parsed.kind === 'open_record') {
    if (parsed.model && parsed.recordId) return true;
    return typeof props.onSuggestedAction === 'function';
  }
  if (parsed.kind === 'open_scene') return Boolean(parsed.sceneKey);
  if (parsed.kind === 'open_url') return Boolean(parsed.url);
  if (parsed.kind === 'check_permission' || parsed.kind === 'relogin') return true;
  return false;
});

const suggestedActionLabel = computed(() => {
  const kind = parseSuggestedAction(props.suggestedAction).kind;
  if (!canRunSuggestedAction.value) return '';
  if (kind === 'refresh') return 'Refresh now';
  if (kind === 'retry') return 'Retry now';
  if (kind === 'relogin') return 'Go to login';
  if (kind === 'check_permission') return 'View permissions';
  if (kind === 'open_record') return 'Open record';
  if (kind === 'open_scene') return 'Open scene';
  if (kind === 'open_url') return 'Open link';
  return '';
});

function runSuggestedAction() {
  const parsed = parseSuggestedAction(props.suggestedAction);
  if (!parsed.kind) return;
  const rawAction = parsed.raw;
  if (props.onSuggestedAction && rawAction) {
    const handled = props.onSuggestedAction(rawAction);
    if (handled) return;
  }
  if ((parsed.kind === 'refresh' || parsed.kind === 'retry') && props.onRetry) {
    props.onRetry();
    return;
  }
  if (parsed.kind === 'relogin') {
    const redirect = encodeURIComponent(`${window.location.pathname}${window.location.search}`);
    safeNavigate(`/login?redirect=${redirect}`);
    return;
  }
  if (parsed.kind === 'check_permission') {
    safeNavigate('/usage-analytics');
    return;
  }
  if (parsed.kind === 'open_scene' && parsed.sceneKey) {
    safeNavigate(`/s/${encodeURIComponent(parsed.sceneKey)}`);
    return;
  }
  if (parsed.kind === 'open_record' && parsed.model && parsed.recordId) {
    safeNavigate(`/r/${encodeURIComponent(parsed.model)}/${parsed.recordId}`);
    return;
  }
  if (parsed.kind === 'open_url' && parsed.url) {
    safeNavigate(parsed.url);
    return;
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
