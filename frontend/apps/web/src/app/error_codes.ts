export const ErrorCodes = {
  NAV_MENU_NO_ACTION: 'NAV_MENU_NO_ACTION',
  ACT_NO_MODEL: 'ACT_NO_MODEL',
  ACT_UNSUPPORTED_TYPE: 'ACT_UNSUPPORTED_TYPE',
  CAPABILITY_MISSING: 'CAPABILITY_MISSING',
  AUTH_401: 'AUTH_401',
  AUTH_403: 'AUTH_403',
  NOT_FOUND_404: 'NOT_FOUND_404',
} as const;

export type ErrorCode = (typeof ErrorCodes)[keyof typeof ErrorCodes];
