<template>
  <span v-if="attachmentLinks.length" class="attachment-links">
    <a
      v-for="link in attachmentLinks"
      :key="`${link.name}-${link.url}`"
      href="#"
      target="_blank"
      rel="noopener"
      @click.prevent="previewAttachmentLink(link)"
    >
      {{ link.name }}
    </a>
  </span>
  <span v-else>{{ display }}</span>
  <AttachmentViewer ref="attachmentViewerRef" />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { FieldDescriptor } from '@sc/schema';
import AttachmentViewer from './attachment/AttachmentViewer.vue';
import { formatDisplayValue, parseAttachmentReferenceLinks } from '../utils/display';
import { attachmentLinkDownloadParams, openExternalAttachmentUrl } from '../utils/filePreview';

const props = defineProps<{ value: unknown; field?: FieldDescriptor }>();
const attachmentViewerRef = ref<InstanceType<typeof AttachmentViewer> | null>(null);

const display = computed(() => {
  return formatDisplayValue(props.value, props.field);
});

const attachmentLinks = computed(() => parseAttachmentReferenceLinks(props.value));

async function previewAttachmentLink(link: { name: string; url: string }) {
  const params = attachmentLinkDownloadParams(link);
  if (params) {
    await attachmentViewerRef.value?.open(params, link.name);
    return;
  }
  openExternalAttachmentUrl(link.url);
}
</script>

<style scoped>
.attachment-links {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px 8px;
}

.attachment-links a {
  color: var(--sc-primary, var(--sc-app-accent));
  text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
