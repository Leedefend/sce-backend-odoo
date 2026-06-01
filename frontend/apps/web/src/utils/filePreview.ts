import { downloadFile } from '../api/files';
import type { FileDownloadRequest, FileDownloadResponse } from '@sc/schema';

const INLINE_MIMETYPE_PREFIXES = ['image/', 'text/'];
const INLINE_MIMETYPES = new Set([
  'application/pdf',
]);

function base64ToBlob(datas: string, mimetype: string) {
  const binary = atob(datas || '');
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: mimetype || 'application/octet-stream' });
}

function canPreviewInline(mimetype: string) {
  const normalized = String(mimetype || '').trim().toLowerCase();
  return INLINE_MIMETYPES.has(normalized) || INLINE_MIMETYPE_PREFIXES.some((prefix) => normalized.startsWith(prefix));
}

function downloadBlob(blob: Blob, name: string) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = name || 'download';
  link.click();
  URL.revokeObjectURL(objectUrl);
}

export function openDownloadedFile(payload: FileDownloadResponse, fallbackName?: string, previewWindow?: Window | null) {
  const name = payload.name || fallbackName || 'download';
  const mimetype = payload.mimetype || 'application/octet-stream';
  if (!payload.datas && payload.url && !payload.url.startsWith('legacy-file')) {
    if (previewWindow) {
      previewWindow.location.href = payload.url;
    } else {
      window.open(payload.url, '_blank', 'noopener');
    }
    return;
  }
  const blob = base64ToBlob(payload.datas || '', mimetype);
  if (canPreviewInline(mimetype)) {
    const objectUrl = URL.createObjectURL(blob);
    if (previewWindow) {
      previewWindow.location.href = objectUrl;
    } else {
      window.open(objectUrl, '_blank', 'noopener');
    }
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    return;
  }
  previewWindow?.close();
  downloadBlob(blob, name);
}

export async function previewOrDownloadFile(params: FileDownloadRequest, fallbackName?: string) {
  const previewWindow = window.open('', '_blank');
  try {
    if (previewWindow) {
      previewWindow.opener = null;
      previewWindow.document.title = fallbackName || '附件预览';
      previewWindow.document.body.textContent = '附件加载中...';
    }
    const payload = await downloadFile(params);
    openDownloadedFile(payload, fallbackName, previewWindow);
  } catch (err) {
    previewWindow?.close();
    throw err;
  }
}

export function openExternalAttachmentUrl(url: string) {
  const clean = String(url || '').trim();
  if (!clean) return;
  window.open(clean, '_blank', 'noopener');
}
