import { intentRequest } from './intents';
import type { FileDownloadRequest, FileDownloadResponse, FileUploadRequest, FileUploadResponse } from '@sc/schema';

export async function uploadFile(params: FileUploadRequest) {
  return intentRequest<FileUploadResponse>({
    intent: 'file.upload',
    params,
  });
}

export async function downloadFile(params: FileDownloadRequest) {
  return intentRequest<FileDownloadResponse>({
    intent: 'file.download',
    params,
  });
}

export async function fileToBase64(file: File): Promise<{ data: string; mimetype: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === 'string' ? reader.result : '';
      const base64 = result.includes(',') ? result.split(',')[1] : result;
      resolve({ data: base64, mimetype: file.type || 'application/octet-stream' });
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}
