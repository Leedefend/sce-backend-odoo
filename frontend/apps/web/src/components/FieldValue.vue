<template>
  <span v-if="attachmentLinks.length" class="attachment-links">
    <a
      v-for="link in attachmentLinks"
      :key="`${link.name}-${link.url}`"
      :href="link.url"
      target="_blank"
      rel="noopener"
    >
      {{ link.name }}
    </a>
  </span>
  <span v-else>{{ display }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { FieldDescriptor } from '@sc/schema';
import { formatDisplayValue, parseAttachmentReferenceLinks } from '../utils/display';

const props = defineProps<{ value: unknown; field?: FieldDescriptor }>();

const display = computed(() => {
  return formatDisplayValue(props.value, props.field);
});

const attachmentLinks = computed(() => parseAttachmentReferenceLinks(props.value));
</script>

<style scoped>
.attachment-links {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px 8px;
}

.attachment-links a {
  color: var(--sc-primary, #2563eb);
  text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
