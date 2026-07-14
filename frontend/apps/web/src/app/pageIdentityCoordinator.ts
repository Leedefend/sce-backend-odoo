import { resolveProductPageIdentity, type PageIdentityInput, type ProductPageIdentity } from './pageIdentity';

export interface PageIdentityCoordinator {
  begin: (key: string, input: PageIdentityInput) => ProductPageIdentity;
  publish: (key: string, input: PageIdentityInput) => ProductPageIdentity | null;
  clear: () => ProductPageIdentity;
  currentKey: () => string;
}

export function createPageIdentityCoordinator(): PageIdentityCoordinator {
  let activeKey = '';
  return {
    begin(key, input) {
      activeKey = String(key || '').trim();
      return resolveProductPageIdentity(input);
    },
    publish(key, input) {
      const normalizedKey = String(key || '').trim();
      if (!normalizedKey || normalizedKey !== activeKey) return null;
      return resolveProductPageIdentity(input);
    },
    clear() {
      activeKey = '';
      return resolveProductPageIdentity({ fallbackTitle: '工作台' });
    },
    currentKey() {
      return activeKey;
    },
  };
}
