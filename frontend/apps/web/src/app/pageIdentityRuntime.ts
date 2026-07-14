import { computed, readonly, ref } from 'vue';
import { resolveProductPageIdentity, type PageIdentityInput, type ProductPageIdentity } from './pageIdentity';
import { createPageIdentityCoordinator } from './pageIdentityCoordinator';

const routeKey = ref('');
const identity = ref<ProductPageIdentity>(resolveProductPageIdentity({ fallbackTitle: '工作台' }));
const coordinator = createPageIdentityCoordinator();

export function beginPageIdentity(key: string, input: PageIdentityInput): void {
  identity.value = coordinator.begin(key, input);
  routeKey.value = coordinator.currentKey();
}

export function publishPageIdentity(key: string, input: PageIdentityInput): boolean {
  const published = coordinator.publish(key, input);
  if (!published) return false;
  identity.value = published;
  return true;
}

export function clearPageIdentity(): void {
  identity.value = coordinator.clear();
  routeKey.value = coordinator.currentKey();
}

export function usePageIdentityRuntime() {
  return {
    routeKey: readonly(routeKey),
    identity: readonly(identity),
    title: computed(() => identity.value.title),
    subtitle: computed(() => identity.value.subtitle || ''),
    breadcrumbs: computed(() => identity.value.breadcrumbs),
  };
}
