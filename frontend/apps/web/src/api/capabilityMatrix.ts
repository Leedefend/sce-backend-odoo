import { intentRequestRaw } from './intents';

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

interface AppCatalogAppRow {
  key?: string;
  label?: string;
  icon?: string | null;
}

interface AppCatalogEnvelope {
  apps?: AppCatalogAppRow[];
}

export async function fetchCapabilityMatrix(): Promise<{
  readonly data: CapabilityMatrixContract;
  readonly traceId: string;
}> {
  const response = await intentRequestRaw<AppCatalogEnvelope>({
    intent: 'app.catalog',
    params: {
      scene: 'web',
    },
    silentErrors: true,
  });
  const apps = Array.isArray(response.data?.apps) ? response.data.apps : [];
  const section: CapabilityMatrixSection = {
    key: 'app_catalog',
    label: '应用目录能力面',
    icon: 'apps',
    sequence: 1,
    items: apps.map((app, index) => ({
      key: String(app?.key || `app_${index}`),
      label: String(app?.label || app?.key || `应用 ${index + 1}`),
      icon: String(app?.icon || ''),
      desc: '通过 intent 渠道投影的应用入口能力。',
      allowed: true,
      capability_state: 'ready',
      order: index,
    })),
  };
  return {
    data: { sections: section.items.length ? [section] : [] },
    traceId: response.traceId,
  };
}
