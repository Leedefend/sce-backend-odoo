import type { ContractAction } from './types';

function isConfigurationAction(action: ContractAction) {
  const label = String(action.label || '').trim();
  const key = String(action.key || '').trim().toLowerCase();
  const source = String(action.sourceWidgetId || '').trim().toLowerCase();
  return label.includes('设置') || key.includes('setting') || key.includes('config') || source.includes('setting') || source.includes('config');
}

export function groupContractHeaderActions(params: {
  actions: ContractAction[];
  intakeMode: boolean;
  nativeTree: boolean;
  configurationMode: boolean;
  productRecord: boolean;
  isSubmitAction: (action: ContractAction) => boolean;
}) {
  const visible = params.intakeMode
    ? []
    : params.actions
      .filter((action) => !params.nativeTree || action.sourceWidgetId === 'page.header')
      .filter((action) => Boolean(action.mutation) || !params.isSubmitAction(action));
  const business = params.configurationMode ? [] : visible.filter((action) => !isConfigurationAction(action));
  const primary = business.find((action) => action.presentationTier === 'primary');
  const direct = params.productRecord
    ? [...(primary ? [primary] : []), ...business.filter((action) => action.presentationTier === 'secondary' && action.key !== primary?.key).slice(0, 2)]
    : business;
  const directKeys = new Set(direct.map((action) => action.key));
  return {
    direct,
    overflow: params.productRecord ? business.filter((action) => !directKeys.has(action.key)) : [],
    configuration: visible.filter((action) => isConfigurationAction(action) && action.enabled),
  };
}
