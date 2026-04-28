type Dict = Record<string, unknown>;

type ContractActionSelection = 'none' | 'single' | 'multi';

type MutationContract = {
  type?: string;
  model?: string;
  operation?: string;
  payload_schema?: { required?: string[] };
  [key: string]: unknown;
};
type ProjectionRefreshPolicy = {
  on_success?: string[];
  on_failure?: string[];
  [key: string]: unknown;
};

type ContractActionButton = {
  key: string;
  label: string;
  kind: string;
  level: string;
  actionId: number | null;
  methodName: string;
  model: string;
  target: string;
  url: string;
  selection: ContractActionSelection;
  visibleProfiles: string[];
  context: Record<string, unknown>;
  domainRaw: string;
  enabled: boolean;
  hint: string;
  mutation?: MutationContract;
  refreshPolicy?: ProjectionRefreshPolicy;
};

type UseActionViewContractActionButtonRuntimeOptions = {
  selectedIds: { value: number[] };
  resolvedModelRef: { value: string };
  modelRef: { value: string };
  userGroupsXmlids: () => string[];
  pageText: (key: string, fallback: string) => string;
  isActionViewNumericToken: (value: unknown) => boolean;
  hasActionViewNoiseMarker: (key: unknown, label: unknown, name: unknown, xmlId: unknown) => boolean;
  normalizeSceneActionProtocol: (row: unknown) => { mutation?: MutationContract; refresh_policy?: ProjectionRefreshPolicy } | null;
  parseContractContextRaw: (value: unknown) => Dict;
  normalizeActionKind: (value: unknown) => string;
  toPositiveInt: (value: unknown) => number | null;
  detectObjectMethodFromActionKey: (key: string, methodName: string) => string;
};

export function useActionViewContractActionButtonRuntime(options: UseActionViewContractActionButtonRuntimeOptions) {
  function toContractActionButton(
    row: Dict,
    dedup: Set<string>,
  ): ContractActionButton | null {
    const key = String(row.key || '').trim();
    if (!key || dedup.has(key)) return null;
    const rawLabel = String(row.label || key).trim();
    if (!rawLabel || options.isActionViewNumericToken(key) || options.isActionViewNumericToken(rawLabel)) return null;
    if (options.hasActionViewNoiseMarker(key, rawLabel, row.name, row.xml_id)) return null;
    dedup.add(key);

    const protocol = options.normalizeSceneActionProtocol(row);
    const targetPayload = options.parseContractContextRaw(row.target);
    const legacyPayload = options.parseContractContextRaw(row.payload);
    const payload = Object.keys(targetPayload).length ? targetPayload : legacyPayload;

    const explicitKind = options.normalizeActionKind(row.kind);
    const hasOpenTarget = Boolean(
      options.toPositiveInt(payload.action_id)
      || options.toPositiveInt(payload.ref)
      || String(payload.url || payload.route || '').trim(),
    );
    const kind = protocol?.mutation
      ? 'mutation'
      : hasOpenTarget
        ? 'open'
        : explicitKind;
    const actionId = options.toPositiveInt(payload.action_id) ?? options.toPositiveInt(payload.ref);
    const methodName = options.detectObjectMethodFromActionKey(key, String(payload.method || '').trim());
    const level = String(row.level || '').trim().toLowerCase();
    const selectionRaw = String(row.selection || 'none').toLowerCase();
    const selection: ContractActionSelection =
      selectionRaw === 'single' || selectionRaw === 'multi' ? selectionRaw : 'none';
    const visibleProfiles = Array.isArray(row.visible_profiles)
      ? (row.visible_profiles as unknown[])
        .map((item) => String(item || '').trim().toLowerCase())
        .filter(Boolean)
      : [];
    const groups = Array.isArray(row.groups_xmlids) ? (row.groups_xmlids as string[]) : [];
    const userGroups = options.userGroupsXmlids();
    const allowedByGroup = !groups.length || groups.some((group) => userGroups.includes(group));
    const selectedCount = options.selectedIds.value.length;
    const enabledBySelection =
      selection == 'none' ? true : selection === 'single' ? selectedCount === 1 : selectedCount > 0;
    const enabled = allowedByGroup && enabledBySelection;
    const hint = allowedByGroup
      ? enabledBySelection
        ? ''
        : selection === 'single'
          ? options.pageText('hint_select_single_record', '请选择 1 条记录')
          : options.pageText('hint_select_record_first', '请先选择记录')
      : options.pageText('hint_permission_denied', '权限不足');
    return {
      key,
      label: rawLabel,
      kind,
      level,
      actionId,
      methodName,
      model: String(row.target_model || row.model || protocol?.mutation?.model || options.resolvedModelRef.value || options.modelRef.value || '').trim(),
      target: String(payload.target || '').trim(),
      url: String(payload.url || payload.route || '').trim(),
      selection,
      visibleProfiles,
      context: options.parseContractContextRaw(payload.context_raw),
      domainRaw: String(payload.domain_raw || '').trim(),
      enabled,
      hint,
      mutation: protocol?.mutation,
      refreshPolicy: protocol?.refresh_policy,
    };
  }

  return {
    toContractActionButton,
  };
}
