import { ref, type Ref } from 'vue';
import { fileToBase64, uploadFile } from '../../api/files';

export type PendingNativeAttachment = {
  key: string;
  name: string;
  size: number;
  file: File;
};

export type NativeAttachmentViewerLike = {
  open: (target: { id: number }, name?: string) => Promise<void> | void;
};

export function useNativeAttachmentRuntime(params: {
  model: () => string;
  recordId: () => number;
  maxBytes: () => number;
  resolveLabel: (key: string, fallback: string) => string;
  reloadTimeline: (resId?: number, model?: string) => Promise<void>;
  viewerRef: Ref<NativeAttachmentViewerLike | null>;
  onPendingUploadFailed: (message: string) => void;
}) {
  const uploading = ref(false);
  const error = ref('');
  const pendingAttachments = ref<PendingNativeAttachment[]>([]);

  function clearError() {
    error.value = '';
  }

  function clearPendingAttachments() {
    pendingAttachments.value = [];
  }

  async function onAttachmentSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || !params.model() || uploading.value) return;
    error.value = '';
    if (file.size > params.maxBytes()) {
      error.value = params.resolveLabel('size_exceeded', '文件过大');
      input.value = '';
      return;
    }
    const recordId = params.recordId();
    if (!recordId) {
      pendingAttachments.value = [
        ...pendingAttachments.value,
        {
          key: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
          name: file.name,
          size: file.size,
          file,
        },
      ];
      input.value = '';
      return;
    }
    uploading.value = true;
    try {
      const { data, mimetype } = await fileToBase64(file);
      await uploadFile({
        model: params.model(),
        res_id: recordId,
        name: file.name,
        mimetype,
        data,
      });
      await params.reloadTimeline();
    } catch (err) {
      error.value = err instanceof Error ? err.message : params.resolveLabel('upload_failed', '附件上传失败');
    } finally {
      uploading.value = false;
      input.value = '';
    }
  }

  function removePendingAttachment(key: string) {
    pendingAttachments.value = pendingAttachments.value.filter((item) => item.key !== key);
  }

  async function uploadPendingAttachments(resId: number): Promise<boolean> {
    const modelName = params.model();
    if (!pendingAttachments.value.length || !modelName) return true;
    error.value = '';
    uploading.value = true;
    try {
      for (const item of pendingAttachments.value) {
        const { data, mimetype } = await fileToBase64(item.file);
        await uploadFile({
          model: modelName,
          res_id: resId,
          name: item.name,
          mimetype,
          data,
        });
      }
      pendingAttachments.value = [];
      await params.reloadTimeline(resId, modelName);
      return true;
    } catch (err) {
      error.value = err instanceof Error ? err.message : params.resolveLabel('upload_failed', '附件上传失败');
      params.onPendingUploadFailed(error.value);
      return false;
    } finally {
      uploading.value = false;
    }
  }

  async function openAttachment(att: { id?: number; name?: string; mimetype?: string }) {
    if (!att?.id) return;
    error.value = '';
    try {
      await params.viewerRef.value?.open({ id: Number(att.id) }, att.name);
    } catch (err) {
      error.value = err instanceof Error ? err.message : params.resolveLabel('download_failed', '附件下载失败');
    }
  }

  return {
    uploading,
    error,
    pendingAttachments,
    clearError,
    clearPendingAttachments,
    onAttachmentSelected,
    removePendingAttachment,
    uploadPendingAttachments,
    openAttachment,
  };
}
