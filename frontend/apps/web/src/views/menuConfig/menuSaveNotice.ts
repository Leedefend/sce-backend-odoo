const MENU_CONFIG_SAVE_NOTICE_KEY = 'sc_menu_config_save_notice';

export function storedMenuSaveNotice() {
  if (typeof window === 'undefined') return '';
  return String(window.sessionStorage.getItem(MENU_CONFIG_SAVE_NOTICE_KEY) || '').trim();
}

export function persistMenuSaveNotice(value: string) {
  if (typeof window === 'undefined') return;
  if (value) window.sessionStorage.setItem(MENU_CONFIG_SAVE_NOTICE_KEY, value);
  else window.sessionStorage.removeItem(MENU_CONFIG_SAVE_NOTICE_KEY);
}
