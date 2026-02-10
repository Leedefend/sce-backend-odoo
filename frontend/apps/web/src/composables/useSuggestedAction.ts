import { computed, toValue, type MaybeRefOrGetter } from 'vue';
import {
  canRunSuggestedAction,
  executeSuggestedAction,
  parseSuggestedAction,
  suggestedActionHint,
  suggestedActionLabel,
  type SuggestedActionCapabilityOptions,
  type SuggestedActionExecuteOptions,
} from '../app/suggestedAction';

export function describeSuggestedAction(raw?: string, options: SuggestedActionCapabilityOptions = {}) {
  const parsed = parseSuggestedAction(raw);
  const canRun = canRunSuggestedAction(parsed, options);
  return {
    parsed,
    canRun,
    label: canRun ? suggestedActionLabel(parsed) : '',
    hint: suggestedActionHint(parsed),
  };
}

export function runSuggestedAction(raw?: string, options: SuggestedActionExecuteOptions = {}) {
  const parsed = parseSuggestedAction(raw);
  return executeSuggestedAction(parsed, options);
}

export function useSuggestedAction(
  raw: MaybeRefOrGetter<string | undefined>,
  options: MaybeRefOrGetter<SuggestedActionCapabilityOptions> = {},
) {
  const parsed = computed(() => parseSuggestedAction(toValue(raw)));
  const canRun = computed(() => canRunSuggestedAction(parsed.value, toValue(options)));
  const label = computed(() => (canRun.value ? suggestedActionLabel(parsed.value) : ''));
  const hint = computed(() => suggestedActionHint(parsed.value));

  function run(execOptions: SuggestedActionExecuteOptions = {}) {
    return executeSuggestedAction(parsed.value, execOptions);
  }

  return {
    parsed,
    canRun,
    label,
    hint,
    run,
  };
}
