import type { Ref } from 'vue';
import type { ActionContract } from '@sc/schema';

export function useContractDebugExportRuntime(params: {
  actionId: () => number;
  contract: Ref<ActionContract | null>;
  contractMeta: Ref<Record<string, unknown> | null>;
  modelName: () => string;
}) {
  function contractDebugPayload() {
    return JSON.stringify(
      {
        action_id: params.actionId(),
        model: params.modelName(),
        contract: params.contract.value,
        meta: params.contractMeta.value || {},
      },
      null,
      2,
    );
  }

  async function copyContractJson() {
    if (!params.contract.value) return;
    try {
      await navigator.clipboard.writeText(contractDebugPayload());
    } catch {
      // Clipboard access can be blocked by browser permissions.
    }
  }

  function exportContractJson() {
    if (!params.contract.value) return;
    const blob = new Blob([contractDebugPayload()], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `contract_form_${params.modelName() || 'unknown'}_${params.actionId() || 'na'}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return {
    copyContractJson,
    exportContractJson,
  };
}
