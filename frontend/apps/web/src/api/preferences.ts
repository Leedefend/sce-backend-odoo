import { intentRequest } from './intents';
import type { UserViewPreferenceContract } from '@sc/schema';

export type ListColumnPreference = {
  visible_columns?: string[];
  hidden_columns?: string[];
  column_order?: string[];
  column_widths?: Record<string, number>;
};

export type UserViewPreferenceScope = {
  action_id?: number;
  model?: string;
  view_type?: string;
  preference_key?: string;
};

const preferenceCache = new Map<string, UserViewPreferenceContract>();
const preferenceInFlight = new Map<string, Promise<UserViewPreferenceContract>>();

function preferenceScopeKey(scope: UserViewPreferenceScope): string {
  return [
    Number(scope.action_id || 0) || 0,
    String(scope.model || '').trim(),
    String(scope.view_type || 'list').trim() || 'list',
    String(scope.preference_key || 'list_columns').trim() || 'list_columns',
  ].join('|');
}

export async function getUserViewPreference(scope: UserViewPreferenceScope) {
  const key = preferenceScopeKey(scope);
  const cached = preferenceCache.get(key);
  if (cached) {
    return cached;
  }
  const existing = preferenceInFlight.get(key);
  if (existing) {
    return existing;
  }
  const request = intentRequest<UserViewPreferenceContract>({
    intent: 'user.view.preference.get',
    params: {
      action_id: scope.action_id,
      model: scope.model || '',
      view_type: scope.view_type || 'list',
      preference_key: scope.preference_key || 'list_columns',
    },
  });
  preferenceInFlight.set(key, request);
  try {
    const result = await request;
    preferenceCache.set(key, result);
    return result;
  } finally {
    preferenceInFlight.delete(key);
  }
}

export async function setUserViewPreference(scope: UserViewPreferenceScope, preference: ListColumnPreference) {
  const key = preferenceScopeKey(scope);
  const result = await intentRequest<UserViewPreferenceContract>({
    intent: 'user.view.preference.set',
    params: {
      action_id: scope.action_id,
      model: scope.model || '',
      view_type: scope.view_type || 'list',
      preference_key: scope.preference_key || 'list_columns',
      preference,
    },
  });
  preferenceCache.set(key, result);
  return result;
}
