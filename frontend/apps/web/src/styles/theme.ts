const THEME_KEY = 'sc_theme';

export type ScTheme = 'light' | 'dark' | 'system';

function resolveSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined' || !window.matchMedia) return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function applyTheme(theme: ScTheme): void {
  const root = document.documentElement;
  const resolved = theme === 'system' ? resolveSystemTheme() : theme;
  if (resolved === 'dark') root.setAttribute('data-sc-theme', 'dark');
  else root.removeAttribute('data-sc-theme');
}

export function bootTheme(): void {
  let theme: ScTheme = 'system';
  try {
    const stored = localStorage.getItem(THEME_KEY) as ScTheme | null;
    if (stored === 'light' || stored === 'dark' || stored === 'system') theme = stored;
  } catch {
    theme = 'system';
  }
  applyTheme(theme);
}


export function nextTheme(current: ScTheme): ScTheme {
  if (current === 'system') return 'light';
  if (current === 'light') return 'dark';
  return 'system';
}

export function persistTheme(theme: ScTheme): void {
  try { localStorage.setItem(THEME_KEY, theme); } catch { /* ignore storage failures */ }
  applyTheme(theme);
}
