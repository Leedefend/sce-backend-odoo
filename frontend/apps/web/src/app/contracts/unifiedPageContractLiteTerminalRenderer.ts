import type { LiteTerminalClient } from './unifiedPageContractLiteTerminal';
import type {
  LiteTerminalRendererInput,
  LiteTerminalRendererInputSnapshot,
} from './unifiedPageContractLiteTerminalRendererInput';

export type LiteTerminalViewNodeKind = 'field' | 'action';

export type LiteTerminalViewNode = {
  nodeId: string;
  kind: LiteTerminalViewNodeKind;
  sourceId: string;
  order: number;
};

export type LiteTerminalRendererOutput = {
  clientType: LiteTerminalClient;
  pageId: string;
  sceneKey: string;
  model: string;
  viewType: LiteTerminalRendererInput['viewType'];
  contractVersion: '2.0.0';
  nodes: LiteTerminalViewNode[];
  nodeCount: number;
  fieldNodeCount: number;
  actionNodeCount: number;
};

export type LiteTerminalRendererOutputSnapshot = {
  outputs: LiteTerminalRendererOutput[];
};

function toFieldNode(widgetId: string, order: number): LiteTerminalViewNode {
  return {
    nodeId: `node.${widgetId}`,
    kind: 'field',
    sourceId: widgetId,
    order,
  };
}

function toActionNode(actionId: string, order: number): LiteTerminalViewNode {
  return {
    nodeId: `node.${actionId}`,
    kind: 'action',
    sourceId: actionId,
    order,
  };
}

export function createLiteTerminalRendererOutput(input: LiteTerminalRendererInput): LiteTerminalRendererOutput {
  const fieldNodes = input.widgetIds.map(toFieldNode);
  const actionNodes = input.actionIds.map((actionId, index) => toActionNode(actionId, fieldNodes.length + index));
  const nodes = [...fieldNodes, ...actionNodes];
  return {
    clientType: input.clientType,
    pageId: input.pageId,
    sceneKey: input.sceneKey,
    model: input.model,
    viewType: input.viewType,
    contractVersion: input.contractVersion,
    nodes,
    nodeCount: nodes.length,
    fieldNodeCount: fieldNodes.length,
    actionNodeCount: actionNodes.length,
  };
}

export function createLiteTerminalRendererOutputSnapshot(
  snapshot: LiteTerminalRendererInputSnapshot,
): LiteTerminalRendererOutputSnapshot {
  return {
    outputs: snapshot.inputs.map(createLiteTerminalRendererOutput),
  };
}
