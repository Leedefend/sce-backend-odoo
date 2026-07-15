import { parseMaybeJsonRecord } from '../../app/contractRuntime';
import { normalizeSceneActionProtocol } from '../../app/sceneActionProtocol';

function actionMethod(row: Record<string, unknown>) {
  return String(row.method || parseMaybeJsonRecord(row.payload).method || '').trim();
}

export function selectAuthoritativeBusinessActionRows(
  nativeFormContract: Record<string, unknown> | undefined,
  workflowRows: Array<Record<string, unknown>>,
) {
  const businessActions = (Array.isArray(nativeFormContract?.business_actions)
    ? nativeFormContract.business_actions : []).map((row) => parseMaybeJsonRecord(row));
  const authoritativeMutationMethods = new Set(
    businessActions.filter((row) => Boolean(normalizeSceneActionProtocol(row)?.mutation)).map(actionMethod).filter(Boolean),
  );
  const retainedWorkflowRows = workflowRows.filter((row) => {
    const method = actionMethod(row);
    return !method || !authoritativeMutationMethods.has(method);
  });
  const nativeRows = [
    ...businessActions,
    ...(Array.isArray(nativeFormContract?.header_buttons) ? nativeFormContract.header_buttons : []),
    ...(Array.isArray(nativeFormContract?.button_box) ? nativeFormContract.button_box : []),
  ].map((row) => parseMaybeJsonRecord(row));
  return { workflowRows: retainedWorkflowRows, nativeRows };
}
