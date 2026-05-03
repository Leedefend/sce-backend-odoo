import {
  isUnifiedPageContractLite,
  type LiteClientType,
  type UnifiedPageContractLite,
} from './unifiedPageContractLite';

export const LITE_TERMINAL_CLIENTS = ['web_pc', 'wx_mini', 'harmony_h5'] as const satisfies readonly LiteClientType[];

export type LiteTerminalClient = typeof LITE_TERMINAL_CLIENTS[number];

export type LiteTerminalConsumerBoundary = {
  clientType: LiteTerminalClient;
  pageId: string;
  sceneKey: string;
  model: string;
  viewType: UnifiedPageContractLite['pageInfo']['viewType'];
  contractVersion: '2.0.0';
  widgetIds: string[];
  fieldCodes: string[];
  actionIds: string[];
};

function collectWidgets(containers: UnifiedPageContractLite['layoutContract']['containerList']) {
  const widgets: UnifiedPageContractLite['layoutContract']['containerList'][number]['widgetList'] = [];
  const visit = (rows: UnifiedPageContractLite['layoutContract']['containerList']) => {
    rows.forEach((container) => {
      widgets.push(...container.widgetList);
      visit(container.children);
    });
  };
  visit(containers);
  return widgets;
}

export function isLiteTerminalClient(value: unknown): value is LiteTerminalClient {
  return LITE_TERMINAL_CLIENTS.includes(value as LiteTerminalClient);
}

export function createLiteTerminalConsumerBoundary(contract: UnifiedPageContractLite): LiteTerminalConsumerBoundary {
  const widgets = collectWidgets(contract.layoutContract.containerList);
  return {
    clientType: contract.pageInfo.clientType,
    pageId: contract.pageInfo.pageId,
    sceneKey: contract.pageInfo.sceneKey,
    model: contract.pageInfo.model,
    viewType: contract.pageInfo.viewType,
    contractVersion: contract.pageInfo.contractVersion,
    widgetIds: widgets.map((widget) => widget.widgetId),
    fieldCodes: widgets.map((widget) => widget.fieldCode),
    actionIds: contract.actionContract.actionRuleList.map((action) => action.actionId),
  };
}

export function parseLiteTerminalContract(value: unknown): LiteTerminalConsumerBoundary | null {
  if (!isUnifiedPageContractLite(value)) return null;
  if (!isLiteTerminalClient(value.pageInfo.clientType)) return null;
  return createLiteTerminalConsumerBoundary(value);
}
