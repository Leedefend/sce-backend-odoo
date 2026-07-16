import type { FieldDescriptor } from '@sc/schema';

export type {
  FormRuntimeBusyKind as BusyKind,
  FormRuntimeStateEvent,
  FormRuntimeStateRefs,
  FormRuntimeStatus as UiStatus,
  FormRuntimeTransactionName,
  FormSubmissionFeedback as SubmissionFeedback,
} from './runtimeStateProtocol';
export type { FormRuntimeStateSnapshot } from './runtimeStateReducer';

export const MANY2ONE_CREATE_OPTION = '__create__';
export const MANY2ONE_SEARCH_MORE_OPTION = '__search_more__';
export const MANY2ONE_OPEN_RECORD_OPTION = '__open_record__';
export const PROJECT_CONTEXT_CHANGED_EVENT = 'sc:project-context-changed';

export type ContractAction = {
  key: string;
  label: string;
  kind: string;
  level: string;
  selection: 'none' | 'single' | 'multi';
  actionId: number | null;
  methodName: string;
  targetModel: string;
  context: Record<string, unknown>;
  domainRaw: string;
  target: string;
  url: string;
  enabled: boolean;
  hint: string;
  intent: string;
  semantic: string;
  sourceWidgetId: string;
  clientMode: string;
  visibleProfiles: Array<'create' | 'edit' | 'readonly'>;
  requiredParams: string[];
  requiresReason: boolean;
  presentationTier?: 'primary' | 'secondary' | 'overflow' | string;
  destructive?: boolean;
  requiresConfirmation?: boolean;
  actionSafety?: {
    classification: 'safe' | 'danger';
    requiresConfirm: boolean;
    confirmMessage: string;
    reasonCode: string;
  };
  mutation?: {
    type: string;
    model: string;
    operation: string;
    payload_schema?: Record<string, unknown>;
  };
  refreshPolicy?: {
    on_success: string[];
    on_failure?: string[];
    mode?: string;
    scope?: string;
    debounce_ms?: number;
  };
};

export type NativeChatterAction = {
  key: string;
  label: string;
  intent: string;
  mode: string;
  payload: Record<string, unknown>;
  enabled: boolean;
  hint: string;
};

export type LayoutNode = {
  key: string;
  kind: 'header' | 'sheet' | 'group' | 'notebook' | 'page' | 'field';
  name: string;
  label: string;
  readonly: boolean;
  required: boolean;
  widget?: string;
  widgetSemantics?: Record<string, unknown>;
  spanClass?: string;
  descriptor?: FieldDescriptor;
};

export type LowCodeFieldSize = 'normal' | 'wide' | 'full' | 'large';

export type RelationOption = {
  id: number;
  label: string;
  color?: number | null;
  switchContext?: {
    code: string;
    label: string;
    defaultValues: Record<string, unknown>;
  };
};

export type RelationSearchColumn = {
  name: string;
  label: string;
};

export type RelationSearchRow = {
  id: number;
  label: string;
  values: Record<string, unknown>;
};

export type RelationUiLabels = Record<string, string>;

export type StatusbarState = {
  value: string | number;
  label: string;
};

export type NativeStatusbarVm = {
  visible: boolean;
  field: string;
  current: string;
  states: StatusbarState[];
  reachedValues: string[];
  readonly: boolean;
};

export type One2ManyInlineRow = {
  key: string;
  id: number | null;
  isNew: boolean;
  removed: boolean;
  dirty: boolean;
  dirtyFields: string[];
  values: Record<string, unknown>;
};

export type One2ManyColumn = {
  name: string;
  label: string;
  ttype: string;
  required: boolean;
  readonly?: boolean;
  selection?: Array<[string, string]>;
};

export type ContractAccessPolicy = {
  mode: 'allow' | 'degrade' | 'block';
  reasonCode: string;
  message: string;
  blockedFields: Array<{ field: string; model: string; reasonCode: string }>;
  degradedFields: Array<{ field: string; model: string; reasonCode: string }>;
};

export type ContractPromptField = {
  name: string;
  label: string;
  required: boolean;
  defaultValue: string;
  options: Array<{ value: string; label: string }>;
};

export type ContractFieldGovernanceAction = {
  key: string;
  label: string;
  value: string;
  checked: boolean;
  disabled: boolean;
  title: string;
  raw: Record<string, unknown>;
};

export type ContractFieldGovernanceRow = {
  fieldKey: string;
  label: string;
  actions: ContractFieldGovernanceAction[];
};

export type FormConfigAuditResult = {
  businessConfigFormFields: string[];
  businessConfigFormLayoutFields: string[];
  hasBusinessConfigFormLayout: boolean;
  layoutMatchesFields: boolean;
  legacyPolicyFields: string[];
  skippedLegacyPolicyFields: string[];
  activeLegacyPolicyFields: string[];
  hasConflict: boolean;
};

export type FormConfigOperationLogEntry = {
  id: string;
  at: string;
  operator: string;
  action: string;
  summary: string;
  status: 'pending' | 'saved' | 'reverted' | 'done';
};

export class ContractAccessPolicyError extends Error {
  reasonCode: string;

  constructor(message: string, reasonCode: string) {
    super(message);
    this.name = 'ContractAccessPolicyError';
    this.reasonCode = reasonCode;
  }
}
