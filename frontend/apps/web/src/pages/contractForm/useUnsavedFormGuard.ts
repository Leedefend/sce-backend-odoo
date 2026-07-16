import { onActivated, onBeforeUnmount, onDeactivated, onMounted, type Ref } from 'vue';
import { useRouter, type NavigationGuard } from 'vue-router';

export function useUnsavedFormGuard(params: {
  dirty: () => boolean;
  busy: Ref<boolean>;
  confirmLeave: () => Promise<boolean>;
}) {
  const router = useRouter();
  let removeRouteGuard: (() => void) | null = null;
  let allowNextNavigation = false;
  const beforeUnload = (event: BeforeUnloadEvent) => {
    if (!params.dirty() || params.busy.value) return;
    event.preventDefault();
    event.returnValue = '';
  };

  const routeGuard: NavigationGuard = async () => {
    if (allowNextNavigation) {
      allowNextNavigation = false;
      return true;
    }
    if (!params.dirty() || params.busy.value) return true;
    return params.confirmLeave();
  };

  const navigateAfterConfirm = async (navigate: () => void | Promise<void>) => {
    if (params.dirty() && !params.busy.value && !(await params.confirmLeave())) return false;
    allowNextNavigation = true;
    await navigate();
    window.setTimeout(() => { allowNextNavigation = false; }, 0);
    return true;
  };

  const installRouteGuard = () => {
    if (removeRouteGuard) return;
    removeRouteGuard = router.beforeEach(routeGuard);
  };

  const removeInstalledRouteGuard = () => {
    removeRouteGuard?.();
    removeRouteGuard = null;
  };

  onMounted(() => {
    installRouteGuard();
    window.addEventListener('beforeunload', beforeUnload);
  });
  onActivated(installRouteGuard);
  onDeactivated(removeInstalledRouteGuard);
  onBeforeUnmount(() => {
    removeInstalledRouteGuard();
    window.removeEventListener('beforeunload', beforeUnload);
  });
  return { navigateAfterConfirm };
}
