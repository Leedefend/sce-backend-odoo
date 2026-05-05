import type {
  LiteTerminalClient,
  LiteTerminalConsumerBoundary,
} from './unifiedPageContractLiteTerminal';
import type { LiteTerminalContractStoreSnapshot } from './unifiedPageContractLiteTerminalStore';

export type LiteTerminalRendererInput = {
  clientType: LiteTerminalClient;
  pageId: string;
  sceneKey: string;
  model: string;
  viewType: LiteTerminalConsumerBoundary['viewType'];
  contractVersion: '2.0.0';
  widgetIds: string[];
  fieldCodes: string[];
  actionIds: string[];
  widgetCount: number;
  fieldCount: number;
  actionCount: number;
};

export type LiteTerminalRendererInputSnapshot = {
  inputs: LiteTerminalRendererInput[];
};

function unique(values: string[]): string[] {
  return Array.from(new Set(values.filter((value) => value.trim().length > 0)));
}

export function createLiteTerminalRendererInput(boundary: LiteTerminalConsumerBoundary): LiteTerminalRendererInput {
  const widgetIds = unique(boundary.widgetIds);
  const fieldCodes = unique(boundary.fieldCodes);
  const actionIds = unique(boundary.actionIds);
  return {
    clientType: boundary.clientType,
    pageId: boundary.pageId,
    sceneKey: boundary.sceneKey,
    model: boundary.model,
    viewType: boundary.viewType,
    contractVersion: boundary.contractVersion,
    widgetIds,
    fieldCodes,
    actionIds,
    widgetCount: widgetIds.length,
    fieldCount: fieldCodes.length,
    actionCount: actionIds.length,
  };
}

export function createLiteTerminalRendererInputSnapshot(
  snapshot: LiteTerminalContractStoreSnapshot,
): LiteTerminalRendererInputSnapshot {
  return {
    inputs: snapshot.entries.map(createLiteTerminalRendererInput),
  };
}
