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

function attachmentIdFromWebContentUrl(url: string): number {
  const clean = String(url || '').trim();
  const direct = clean.match(/^\/web\/content\/(\d+)(?:[/?#]|$)/);
  if (direct) return Number(direct[1] || 0) || 0;
  const modelField = clean.match(/^\/web\/content\/ir\.attachment\/(\d+)\//);
  if (modelField) return Number(modelField[1] || 0) || 0;
  try {
    const parsed = new URL(clean, window.location.origin);
    const id = Number(parsed.searchParams.get('id') || parsed.searchParams.get('attachment_id') || 0);
    return Number.isFinite(id) && id > 0 ? Math.trunc(id) : 0;
  } catch {
    return 0;
  }
}

export function attachmentLinkDownloadParams(
  link: { name: string; url: string },
  context?: { model?: string; res_id?: number },
): FileDownloadRequest | null {
  const url = String(link.url || '').trim();
  if (url.startsWith('legacy-file://') || url.startsWith('legacy-file-id://')) {
    return {
      url,
      model: context?.model,
      res_id: context?.res_id,
      name: link.name,
    };
  }
  if (url.startsWith('/web/content/')) {
    const id = attachmentIdFromWebContentUrl(url);
    return id ? { id, name: link.name } : null;
  }
  return null;
}

function downloadBlob(blob: Blob, name: string) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = name || 'download';
  link.click();
  URL.revokeObjectURL(objectUrl);
}

function previewBlob(objectUrl: string, name: string, previewWindow?: Window | null) {
  if (!previewWindow) {
    window.open(objectUrl, '_blank', 'noopener');
    return;
  }
  const doc = previewWindow.document;
  doc.title = name || '附件预览';
  const iframe = doc.createElement('iframe');
  iframe.src = objectUrl;
  iframe.title = name || '附件预览';
  iframe.style.border = '0';
  iframe.style.width = '100vw';
  iframe.style.height = '100vh';
  iframe.style.display = 'block';
  doc.documentElement.style.margin = '0';
  doc.body.style.margin = '0';
  doc.body.replaceChildren(iframe);
}

export function openDownloadedFile(payload: FileDownloadResponse, fallbackName?: string, previewWindow?: Window | null) {
  const name = payload.name || fallbackName || 'download';
  const mimetype = payload.mimetype || 'application/octet-stream';
  if (!payload.datas && payload.url && !payload.url.startsWith('legacy-file')) {
    if (previewWindow) {
      const link = previewWindow.document.createElement('a');
      link.href = payload.url;
      link.rel = 'noopener';
      link.textContent = '打开附件';
      previewWindow.document.body.replaceChildren(link);
      previewWindow.setTimeout(() => previewWindow.location.replace(payload.url), 0);
    } else {
      window.open(payload.url, '_blank', 'noopener');
    }
    return;
  }
  const blob = base64ToBlob(payload.datas || '', mimetype);
  if (canPreviewInline(mimetype)) {
    const objectUrl = URL.createObjectURL(blob);
    previewBlob(objectUrl, name, previewWindow);
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

export async function previewAttachmentReferenceLink(
  link: { name: string; url: string },
  context?: { model?: string; res_id?: number },
) {
  const params = attachmentLinkDownloadParams(link, context);
  if (params) {
    await previewOrDownloadFile(params, link.name);
    return;
  }
  openExternalAttachmentUrl(link.url);
}
