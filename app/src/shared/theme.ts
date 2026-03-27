// Theme management for LLMLaunchpad UI
// Provides a simple dark/light toggle stored in localStorage.
// The theme store updates the <html> element's "dark" class accordingly.

import { writable } from 'svelte/store';

export type Theme = 'light' | 'dark';

// Persisted theme store
export const theme = writable<Theme>('light');

/**
 * Initialize the theme based on saved preference or system setting.
 * Call this once on app startup (e.g., in App.svelte onMount).
 */
export function initTheme(): void {
  const saved = localStorage.getItem('theme') as Theme | null;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initial: Theme = saved ?? (prefersDark ? 'dark' : 'light');

  // Set the initial class on the html element
  document.documentElement.classList.toggle('dark', initial === 'dark');
  theme.set(initial);

  // Subscribe to changes and persist them
  theme.subscribe((value) => {
    document.documentElement.classList.toggle('dark', value === 'dark');
    localStorage.setItem('theme', value);
  });
}

/**
 * Toggle the current theme between light and dark.
 */
export function toggleTheme(): void {
  theme.update((current) => (current === 'light' ? 'dark' : 'light'));
}
