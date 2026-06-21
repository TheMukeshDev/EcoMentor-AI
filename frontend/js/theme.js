/**
 * Theme management module.
 *
 * Handles dark/light mode detection, persistence, and toggling
 * with support for updating toggle button state and chart cleanup.
 *
 * @module theme
 */

/**
 * Initialize the theme based on saved preference or system setting.
 * Should be called once during application bootstrap.
 */
export function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = savedTheme || (prefersDark ? 'dark' : 'light');
  applyTheme(theme);
}

/**
 * Toggle between light and dark themes.
 * Persists the choice to localStorage and destroys any active chart
 * so it can be re-rendered with the correct color scheme.
 */
export function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
  applyTheme(nextTheme);
  localStorage.setItem('theme', nextTheme);
  destroyActiveChart();
}

/**
 * Apply a theme to the document and update toggle button icons.
 * @param {string} theme - Either 'dark' or 'light'.
 */
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const icon = theme === 'dark' ? '\u2600' : '\u263E';

  const toggleButton = document.getElementById('theme-toggle');
  if (toggleButton) toggleButton.textContent = icon;

  document.querySelectorAll('.theme-toggle').forEach(button => {
    button.setAttribute('aria-pressed', String(theme === 'dark'));
  });
}

/**
 * Destroy the currently active carbon chart instance if it exists.
 * This allows the chart to be re-created with updated theme colors.
 */
function destroyActiveChart() {
  if (window._carbonChart && typeof window._carbonChart.destroy === 'function') {
    window._carbonChart.destroy();
    window._carbonChart = null;
  }
}
