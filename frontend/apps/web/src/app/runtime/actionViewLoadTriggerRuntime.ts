import { resolveListControlTransition } from './actionViewInteractionRuntime';

export function resolveReloadTriggerPlan(): {
  shouldSyncRoute: boolean;
  shouldLoad: boolean;
} {
  return {
    shouldSyncRoute: false,
    shouldLoad: true,
  };
}

export function resolveSearchTriggerPlan(options: {
  value: string;
}): {
  nextSearchTerm: string | null;
  nextGroupWindowOffset: number;
  shouldSyncRoute: boolean;
  shouldLoad: boolean;
} {
  const transition = resolveListControlTransition({ control: 'search', value: options.value });
  return {
    nextSearchTerm: transition.nextSearchTerm,
    nextGroupWindowOffset: transition.nextGroupWindowOffset,
    shouldSyncRoute: true,
    shouldLoad: true,
  };
}

export function resolveSortTriggerPlan(options: {
  value: string;
}): {
  nextSortValue: string | null;
  nextGroupWindowOffset: number;
  shouldSyncRoute: boolean;
  shouldLoad: boolean;
} {
  const transition = resolveListControlTransition({ control: 'sort', value: options.value });
  return {
    nextSortValue: transition.nextSortValue,
    nextGroupWindowOffset: transition.nextGroupWindowOffset,
    shouldSyncRoute: true,
    shouldLoad: true,
  };
}

export function resolveFilterTriggerPlan(options: {
  value: 'all' | 'active' | 'archived';
}): {
  nextFilterValue: 'all' | 'active' | 'archived' | null;
  nextGroupWindowOffset: number;
  shouldClearSelection: boolean;
  shouldSyncRoute: boolean;
  shouldLoad: boolean;
} {
  const transition = resolveListControlTransition({ control: 'filter', value: options.value });
  return {
    nextFilterValue: transition.nextFilterValue,
    nextGroupWindowOffset: transition.nextGroupWindowOffset,
    shouldClearSelection: transition.shouldClearSelection,
    shouldSyncRoute: true,
    shouldLoad: true,
  };
}

export function resolveTriggerGroupWindowOffset(options: {
  nextGroupWindowOffset: number;
  currentGroupWindowOffset: number;
}): number {
  return Number.isFinite(options.nextGroupWindowOffset)
    ? options.nextGroupWindowOffset
    : options.currentGroupWindowOffset;
}
