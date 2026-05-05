import type { LiteTerminalClient } from './unifiedPageContractLiteTerminal';
import type {
  LiteTerminalRendererOutput,
  LiteTerminalRendererOutputSnapshot,
  LiteTerminalViewNode,
} from './unifiedPageContractLiteTerminalRenderer';

export type LiteTerminalPageIntegration = {
  clientType: LiteTerminalClient;
  pageId: string;
  sceneKey: string;
  model: string;
  viewType: LiteTerminalRendererOutput['viewType'];
  contractVersion: '2.0.0';
  rootNodeId: string;
  mountedNodes: LiteTerminalViewNode[];
  mountedNodeCount: number;
  ready: boolean;
};

export type LiteTerminalPageIntegrationSnapshot = {
  pages: LiteTerminalPageIntegration[];
};

export function createLiteTerminalPageIntegration(output: LiteTerminalRendererOutput): LiteTerminalPageIntegration {
  return {
    clientType: output.clientType,
    pageId: output.pageId,
    sceneKey: output.sceneKey,
    model: output.model,
    viewType: output.viewType,
    contractVersion: output.contractVersion,
    rootNodeId: `root.${output.pageId}`,
    mountedNodes: output.nodes,
    mountedNodeCount: output.nodeCount,
    ready: output.nodeCount > 0,
  };
}

export function createLiteTerminalPageIntegrationSnapshot(
  snapshot: LiteTerminalRendererOutputSnapshot,
): LiteTerminalPageIntegrationSnapshot {
  return {
    pages: snapshot.outputs.map(createLiteTerminalPageIntegration),
  };
}
