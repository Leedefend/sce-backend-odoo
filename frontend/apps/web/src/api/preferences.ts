import { intentRequest } from './intents';
import type { UserViewPreferenceContract } from '@sc/schema';

export type ListColumnPreference = {
  visible_columns?: string[];
  hidden_columns?: string[];
};

export type UserViewPreferenceScope = {
  action_id?: number;
  model?: string;
  view_type?: string;
  preference_key?: string;
};

export async function getUserViewPreference(scope: UserViewPreferenceScope) {
  return intentRequest<UserViewPreferenceContract>({
    intent: 'user.view.preference.get',
    params: {
      action_id: scope.action_id,
      model: scope.model || '',
      view_type: scope.view_type || 'list',
      preference_key: scope.preference_key || 'list_columns',
    },
  });
}

export async function setUserViewPreference(scope: UserViewPreferenceScope, preference: ListColumnPreference) {
  return intentRequest<UserViewPreferenceContract>({
    intent: 'user.view.preference.set',
    params: {
      action_id: scope.action_id,
      model: scope.model || '',
      view_type: scope.view_type || 'list',
      preference_key: scope.preference_key || 'list_columns',
      preference,
    },
  });
}
