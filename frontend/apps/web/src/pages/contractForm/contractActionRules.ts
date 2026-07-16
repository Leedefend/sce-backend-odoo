import type { ActionContract } from '@sc/schema';
import { resolveUnifiedPageContractV2 } from '../../app/contracts/unifiedPageContractV2';
import { parseMaybeJsonRecord } from '../../app/contractRuntime';

export function resolveContractActionRules(contract: ActionContract | null) {
  const rules = parseMaybeJsonRecord(resolveUnifiedPageContractV2(contract)?.actionContract).actionRuleList;
  return Array.isArray(rules)
    ? rules.filter((row): row is Record<string, unknown> => Boolean(row && typeof row === 'object' && !Array.isArray(row)))
    : [];
}

export function fieldRequiresServerOnchange(rules: Array<Record<string, unknown>>, fieldName: string) {
  return rules.some((rule) => {
    const source = String(rule.sourceWidgetId || rule.source_widget_id || '').trim();
    const trigger = String(rule.triggerType || rule.trigger_type || '').trim().toLowerCase();
    const dispatch = String(rule.dispatchMode || rule.dispatch_mode || '').trim().toLowerCase();
    return source === `field.${fieldName}`
      && ['change', 'select', 'blur'].includes(trigger)
      && dispatch.startsWith('server');
  });
}
