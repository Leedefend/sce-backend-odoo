import { computed, watch, type ComputedRef } from 'vue';
import { resolveProductPageIdentity, type PageIdentityInput } from './pageIdentity';
import { publishPageIdentity } from './pageIdentityRuntime';

interface PublishedPageIdentityOptions {
  routeKey: () => string;
  active?: () => boolean;
  onTitle?: (title: string) => void;
  immediate?: boolean;
}

export function usePublishedPageIdentity(
  input: ComputedRef<PageIdentityInput>,
  options: PublishedPageIdentityOptions,
) {
  const identity = computed(() => resolveProductPageIdentity(input.value));
  watch(input, (value) => {
    if (options.active && !options.active()) return;
    publishPageIdentity(options.routeKey(), value);
    options.onTitle?.(resolveProductPageIdentity(value).title);
  }, { deep: true, immediate: options.immediate });
  return identity;
}
