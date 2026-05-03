import type { LiteTerminalClient } from './unifiedPageContractLiteTerminal';
import type {
  LiteTerminalPageIntegration,
  LiteTerminalPageIntegrationSnapshot,
} from './unifiedPageContractLiteTerminalPageIntegration';

export type LiteTerminalRuntimeMountStatus = 'mounted';

export type LiteTerminalRuntimeMount = {
  clientType: LiteTerminalClient;
  pageId: string;
  sceneKey: string;
  model: string;
  viewType: LiteTerminalPageIntegration['viewType'];
  contractVersion: '2.0.0';
  rootNodeId: string;
  mountedNodeCount: number;
  status: LiteTerminalRuntimeMountStatus;
};

export type LiteTerminalRuntimeMountSnapshot = {
  mounts: LiteTerminalRuntimeMount[];
};

export function createLiteTerminalRuntimeMount(page: LiteTerminalPageIntegration): LiteTerminalRuntimeMount {
  return {
    clientType: page.clientType,
    pageId: page.pageId,
    sceneKey: page.sceneKey,
    model: page.model,
    viewType: page.viewType,
    contractVersion: page.contractVersion,
    rootNodeId: page.rootNodeId,
    mountedNodeCount: page.mountedNodeCount,
    status: 'mounted',
  };
}

export function createLiteTerminalRuntimeMountSnapshot(
  snapshot: LiteTerminalPageIntegrationSnapshot,
): LiteTerminalRuntimeMountSnapshot {
  return {
    mounts: snapshot.pages.map(createLiteTerminalRuntimeMount),
  };
}
