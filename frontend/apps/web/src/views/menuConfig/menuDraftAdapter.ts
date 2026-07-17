import type { MenuConfigMenu, MenuConfigPolicy } from '../../api/menuConfig';

export type DraftPolicy = {
  policy_id: number;
  menu_id: number;
  target_parent_menu_id: number;
  custom_label: string;
  sequence_override: number;
  visible: boolean;
  role_group_ids: number[];
  note: string;
};

export function defaultDraft(menu: MenuConfigMenu, policy?: MenuConfigPolicy): DraftPolicy {
  return {
    policy_id: Number(policy?.id || 0), menu_id: menu.id,
    target_parent_menu_id: Number(policy?.target_parent_menu_id || 0),
    custom_label: String(policy?.custom_label || ''), sequence_override: Number(policy?.sequence_override || 0),
    visible: policy?.visible ?? true,
    role_group_ids: Array.isArray(policy?.role_group_ids) ? policy.role_group_ids.map(Number).filter(Boolean) : [],
    note: String(policy?.note || ''),
  };
}

export function cloneDraft(draft: DraftPolicy): DraftPolicy { return { ...draft, role_group_ids: [...draft.role_group_ids] }; }
export function defaultDraftForEmpty(): DraftPolicy {
  return { policy_id: 0, menu_id: 0, target_parent_menu_id: 0, custom_label: '', sequence_override: 0, visible: true, role_group_ids: [], note: '' };
}
export function normalizeDraft(draft: DraftPolicy) {
  return JSON.stringify({
    policy_id: draft.policy_id || 0, menu_id: draft.menu_id, target_parent_menu_id: draft.target_parent_menu_id || 0,
    custom_label: draft.custom_label.trim(), sequence_override: Number(draft.sequence_override || 0), visible: Boolean(draft.visible),
    role_group_ids: [...draft.role_group_ids].map(Number).filter(Boolean).sort((a, b) => a - b), note: draft.note.trim(),
  });
}
export function inputValue(event: Event) { return String((event.target as HTMLInputElement).value || ''); }
export function numericValue(event: Event) { return Number((event.target as HTMLInputElement | HTMLSelectElement).value || 0); }
export function checkedValue(event: Event) { return Boolean((event.target as HTMLInputElement).checked); }
