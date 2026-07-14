import { computed, readonly, ref } from 'vue';
import { resolveProductPageIdentity, type PageIdentityInput, type ProductPageIdentity } from './pageIdentity';

const routeKey = ref('');
const identity = ref<ProductPageIdentity>(resolveProductPageIdentity({ fallbackTitle: '工作台' }));

export function beginPageIdentity(key: string, input: PageIdentityInput): void {
  routeKey.value = String(key || '').trim();
  identity.value = resolveProductPageIdentity(input);
}

export function publishPageIdentity(key: string, input: PageIdentityInput): boolean {
  const normalizedKey = String(key || '').trim();
  if (!normalizedKey || normalizedKey !== routeKey.value) return false;
  identity.value = resolveProductPageIdentity(input);
  return true;
}

export function clearPageIdentity(): void {
  routeKey.value = '';
  identity.value = resolveProductPageIdentity({ fallbackTitle: '工作台' });
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
