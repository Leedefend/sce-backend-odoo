<template>
  <Teleport to="body">
    <div v-if="visible" class="attachment-viewer-backdrop" @click.self="close">
      <section class="attachment-viewer" role="dialog" aria-modal="true" aria-label="附件查看">
        <header class="attachment-viewer-header">
          <div class="attachment-viewer-title">
            <h3>{{ displayName }}</h3>
            <p v-if="statusText">{{ statusText }}</p>
          </div>
          <div class="attachment-viewer-actions">
            <button class="ghost" type="button" :disabled="!canDownload" @click="downloadCurrent">下载</button>
            <button class="ghost" type="button" @click="close">关闭</button>
          </div>
        </header>

        <div class="attachment-viewer-body">
          <div v-if="loading" class="attachment-viewer-state">附件加载中...</div>
          <div v-else-if="errorMessage" class="attachment-viewer-state attachment-viewer-state--error">
            {{ errorMessage }}
          </div>
          <iframe
            v-else-if="previewUrl"
            class="attachment-viewer-frame"
            :src="previewUrl"
            :title="displayName"
          />
          <div v-else class="attachment-viewer-state">
            <strong>{{ displayName }}</strong>
            <span>{{ unsupportedText }}</span>
          </div>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue';
import { downloadFile } from '../../api/files';
import type { FileDownloadRequest, FileDownloadResponse } from '@sc/schema';

const INLINE_MIMETYPE_PREFIXES = ['image/', 'text/'];
const INLINE_MIMETYPES = new Set(['application/pdf']);

const visible = ref(false);
const loading = ref(false);
const errorMessage = ref('');
const payload = ref<FileDownloadResponse | null>(null);
const fallbackName = ref('');
const previewUrl = ref('');

const displayName = computed(() => payload.value?.name || fallbackName.value || '附件');
const mimetype = computed(() => payload.value?.mimetype || 'application/octet-stream');
const canDownload = computed(() => Boolean(payload.value?.datas || payload.value?.url));
const statusText = computed(() => {
  if (loading.value) return '正在读取附件';
  if (errorMessage.value) return '附件不可用';
  if (previewUrl.value) return mimetype.value;
  if (payload.value) return '当前文件暂不支持在线预览';
  return '';
});
const unsupportedText = computed(() => {
  if (!payload.value) return '';
  return `当前类型 ${mimetype.value} 暂不支持在线预览，可下载后查看。`;
});

function canPreviewInline(value: string) {
  const normalized = String(value || '').trim().toLowerCase();
  return INLINE_MIMETYPES.has(normalized) || INLINE_MIMETYPE_PREFIXES.some((prefix) => normalized.startsWith(prefix));
}

function base64ToBlob(datas: string, value: string) {
  const binary = atob(datas || '');
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Blob([bytes], { type: value || 'application/octet-stream' });
}

function revokePreviewUrl() {
  if (!previewUrl.value || !previewUrl.value.startsWith('blob:')) return;
  URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = '';
}

function resetPayload() {
  revokePreviewUrl();
  payload.value = null;
  errorMessage.value = '';
}

async function open(params: FileDownloadRequest, name?: string) {
  fallbackName.value = name || '';
  visible.value = true;
  loading.value = true;
  resetPayload();
  try {
    const result = await downloadFile(params);
    payload.value = result;
    const data = result.datas || '';
    const type = result.mimetype || 'application/octet-stream';
    if (data && canPreviewInline(type)) {
      previewUrl.value = URL.createObjectURL(base64ToBlob(data, type));
    } else if (!data && result.url && !result.url.startsWith('legacy-file')) {
      previewUrl.value = result.url;
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '附件打开失败';
  } finally {
    loading.value = false;
  }
}

function close() {
  visible.value = false;
  loading.value = false;
  resetPayload();
}

function downloadBlob(blob: Blob, name: string) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = name || 'download';
  link.click();
  URL.revokeObjectURL(objectUrl);
}

function downloadCurrent() {
  const current = payload.value;
  if (!current) return;
  if (current.datas) {
    downloadBlob(base64ToBlob(current.datas, current.mimetype || ''), displayName.value);
    return;
  }
  if (current.url && !current.url.startsWith('legacy-file')) {
    window.open(current.url, '_blank', 'noopener');
  }
}

onBeforeUnmount(() => {
  resetPayload();
});

defineExpose({ open, close });
</script>

<style scoped>
.attachment-viewer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--sc-app-overlay);
}

.attachment-viewer {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  width: min(1040px, 100%);
  height: min(760px, calc(100vh - 48px));
  min-height: 420px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  box-shadow: var(--sc-app-shadow-modal);
  overflow: hidden;
}

.attachment-viewer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--sc-app-border);
}

.attachment-viewer-title {
  min-width: 0;
}

.attachment-viewer-title h3 {
  margin: 0;
  color: var(--sc-app-text-primary);
  font-size: 14px;
  font-weight: 650;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-viewer-title p {
  margin: 4px 0 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.attachment-viewer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: none;
}

.attachment-viewer-body {
  min-height: 0;
  background: var(--sc-app-muted-bg);
}

.attachment-viewer-frame {
  width: 100%;
  height: 100%;
  border: 0;
  background: var(--sc-app-panel);
}

.attachment-viewer-state {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  height: 100%;
  min-height: 260px;
  padding: 24px;
  color: var(--sc-app-text-secondary);
  text-align: center;
}

.attachment-viewer-state strong {
  max-width: 100%;
  color: var(--sc-app-text-primary);
  overflow-wrap: anywhere;
}

.attachment-viewer-state span {
  max-width: 560px;
  line-height: 1.6;
}

.attachment-viewer-state--error {
  color: var(--sc-app-danger-text);
}

@media (max-width: 720px) {
  .attachment-viewer-backdrop {
    padding: 0;
  }

  .attachment-viewer {
    width: 100%;
    height: 100vh;
    min-height: 100vh;
    border-radius: 0;
  }

  .attachment-viewer-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
