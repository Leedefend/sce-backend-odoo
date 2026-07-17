<template>
  <a
    :href="disabled ? undefined : href"
    :class="['sc-btn', `sc-btn-${variant}`]"
    :aria-disabled="disabled || undefined"
    @click="disabled && $event.preventDefault()"
  ><slot /></a>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  href: string;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  disabled?: boolean;
}>(), { variant: 'secondary', disabled: false });
</script>
