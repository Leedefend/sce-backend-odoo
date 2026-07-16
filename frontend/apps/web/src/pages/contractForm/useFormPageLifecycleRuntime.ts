import {
  nextTick,
  onActivated,
  onBeforeUnmount,
  onDeactivated,
  onMounted,
  watch,
  type Ref,
} from 'vue';
import type { ActionContract } from '@sc/schema';

export function isFormPageRouteOwner(routeName: unknown): boolean {
  return ['record', 'model-form', 'scene'].includes(String(routeName || ''));
}

export function useFormPageLifecycleRuntime(params: {
  contract: Ref<ActionContract | null>;
  formRouteIdentity: () => string;
  handleProjectContextChanged: (event: Event) => void;
  instanceRouteIdentity: Ref<string>;
  isComponentActive: Ref<boolean>;
  onFieldOrderDragEnd: () => void;
  onFieldOrderWindowDragOver: (event: DragEvent) => void;
  onFieldOrderWindowDragStop: () => void;
  onRelationDialogDocumentKeydown: (event: KeyboardEvent) => void;
  projectContextChangedEvent: string;
  routeIsOwned: () => boolean;
  reload: () => Promise<void>;
  retainedRouteIdentity: Ref<string>;
  status: Ref<string>;
  ensureFormInitialReload: () => void;
}) {
  watch(
    () => params.formRouteIdentity(),
    (identity) => {
      if (!params.isComponentActive.value || !params.routeIsOwned()) return;
      if (!params.instanceRouteIdentity.value && identity) params.instanceRouteIdentity.value = identity;
      if (params.instanceRouteIdentity.value && identity !== params.instanceRouteIdentity.value) {
        params.instanceRouteIdentity.value = identity;
      }
      if (identity && identity === params.retainedRouteIdentity.value && params.status.value === 'ok') return;
      void params.reload();
    },
    { immediate: true },
  );

  onMounted(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener(params.projectContextChangedEvent, params.handleProjectContextChanged);
      window.addEventListener('dragover', params.onFieldOrderWindowDragOver);
      window.addEventListener('drop', params.onFieldOrderWindowDragStop);
      window.addEventListener('dragend', params.onFieldOrderWindowDragStop);
    }
    if (typeof document !== 'undefined') {
      document.addEventListener('keydown', params.onRelationDialogDocumentKeydown);
    }
    void nextTick(() => params.ensureFormInitialReload());
  });

  onActivated(() => {
    params.isComponentActive.value = true;
    if (!params.routeIsOwned()) return;
    const identity = params.formRouteIdentity();
    if (identity && identity !== params.retainedRouteIdentity.value) {
      void params.reload();
    }
    void nextTick(() => params.ensureFormInitialReload());
  });

  onDeactivated(() => {
    params.isComponentActive.value = false;
  });

  onBeforeUnmount(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener(params.projectContextChangedEvent, params.handleProjectContextChanged);
      window.removeEventListener('dragover', params.onFieldOrderWindowDragOver);
      window.removeEventListener('drop', params.onFieldOrderWindowDragStop);
      window.removeEventListener('dragend', params.onFieldOrderWindowDragStop);
    }
    if (typeof document !== 'undefined') {
      document.removeEventListener('keydown', params.onRelationDialogDocumentKeydown);
    }
    params.onFieldOrderDragEnd();
  });
}
