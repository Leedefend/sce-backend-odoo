import {
  parseLiteTerminalContract,
  type LiteTerminalClient,
  type LiteTerminalConsumerBoundary,
} from './unifiedPageContractLiteTerminal';

export type LiteTerminalContractStoreSnapshot = {
  entries: LiteTerminalConsumerBoundary[];
};

export type LiteTerminalContractStore = {
  setFromContract(value: unknown): LiteTerminalConsumerBoundary | null;
  get(clientType: LiteTerminalClient, pageId: string): LiteTerminalConsumerBoundary | null;
  list(): LiteTerminalConsumerBoundary[];
  clear(): void;
  snapshot(): LiteTerminalContractStoreSnapshot;
};

function keyOf(clientType: LiteTerminalClient, pageId: string): string {
  return `${clientType}:${pageId}`;
}

export function createLiteTerminalContractStore(): LiteTerminalContractStore {
  const entries = new Map<string, LiteTerminalConsumerBoundary>();

  return {
    setFromContract(value: unknown) {
      const boundary = parseLiteTerminalContract(value);
      if (!boundary) return null;
      entries.set(keyOf(boundary.clientType, boundary.pageId), boundary);
      return boundary;
    },
    get(clientType: LiteTerminalClient, pageId: string) {
      return entries.get(keyOf(clientType, pageId)) || null;
    },
    list() {
      return Array.from(entries.values());
    },
    clear() {
      entries.clear();
    },
    snapshot() {
      return {
        entries: Array.from(entries.values()),
      };
    },
  };
}
