import { watch, type Ref } from 'vue';
import type { LocationQueryRaw, Router } from 'vue-router';

export function useFormAuxiliaryWatchersRuntime(params: {
  autosaveSource: () => unknown[];
  businessCategoryCode: () => string;
  businessCategoryLabel: () => string;
  chatterLoading: () => boolean;
  collaborationReady: () => boolean;
  currentQuery: () => Record<string, unknown>;
  isActive: () => boolean;
  isProjectIntake: () => boolean;
  loadNativeChatterTimeline: () => Promise<void>;
  modelName: () => string;
  nativeChatterAutoLoadKey: Ref<string>;
  persistIntakeAutosave: () => void;
  recordId: () => number | null;
  router: Router;
}) {
  watch(
    () => params.autosaveSource(),
    () => {
      params.persistIntakeAutosave();
    },
  );

  watch(
    () => ({
      label: params.businessCategoryLabel(),
      code: params.businessCategoryCode(),
    }),
    (state) => {
      if (!params.isActive()) return;
      if (!state.label) return;
      const query = params.currentQuery();
      const hasRouteLabel = String(query.current_business_category_label || query.default_business_category_label || '').trim();
      if (hasRouteLabel) return;
      const nextQuery: LocationQueryRaw = {
        ...Object.fromEntries(
          Object.entries(query).map(([key, value]) => [
            key,
            Array.isArray(value)
              ? value.filter((item): item is string => typeof item === 'string')
              : String(value || ''),
          ]),
        ),
        current_business_category_label: state.label,
        default_business_category_label: state.label,
      };
      if (state.code) {
        nextQuery.current_business_category_code = String(query.current_business_category_code || state.code);
        nextQuery.default_business_category_code = String(query.default_business_category_code || state.code);
      }
      void params.router.replace({ query: nextQuery });
    },
  );

  watch(
    () => ({
      model: params.modelName(),
      recordId: params.recordId(),
      collaborationReady: params.collaborationReady(),
      projectIntake: params.isProjectIntake(),
    }),
    (state) => {
      if (!params.isActive()) return;
      if (state.projectIntake || !state.model || !state.recordId || !state.collaborationReady) return;
      const key = `${state.model}:${state.recordId}`;
      if (params.nativeChatterAutoLoadKey.value === key || params.chatterLoading()) return;
      params.nativeChatterAutoLoadKey.value = key;
      void params.loadNativeChatterTimeline();
    },
    { immediate: true },
  );
}
