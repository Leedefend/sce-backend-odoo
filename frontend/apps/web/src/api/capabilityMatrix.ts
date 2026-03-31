import { apiRequestRaw } from './client';

export interface CapabilityMatrixItem {
  key: string;
  label: string;
  icon?: string;
  desc?: string;
  target_url?: string | null;
  action_id?: number | null;
  menu_id?: number | null;
  scene_key?: string | null;
  allowed: boolean;
  deny_reason?: string[];
  capability_state?: string;
  order?: number;
}

export interface CapabilityMatrixSection {
  key: string;
  label: string;
  icon?: string;
  sequence?: number;
  items: CapabilityMatrixItem[];
}

export interface CapabilityMatrixContract {
  sections: CapabilityMatrixSection[];
  schema_version?: string;
}

interface CapabilityMatrixEnvelope {
  data?: CapabilityMatrixContract;
}

export async function fetchCapabilityMatrix(): Promise<{
  readonly data: CapabilityMatrixContract;
  readonly traceId: string;
}> {
  const response = await apiRequestRaw<CapabilityMatrixEnvelope>('/api/contract/capability_matrix');
  return {
    data: response.body?.data || { sections: [] },
    traceId: response.traceId,
  };
}
