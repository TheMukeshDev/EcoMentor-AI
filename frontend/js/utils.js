/**
 * Utility functions for the EcoMentor frontend.
 *
 * Provides HTML sanitization and toast notification helpers.
 *
 * @module utils
 */

/** @type {Object<string, string>} HTML entity escape map. */
const HTML_ESCAPE_MAP = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

/** @type {RegExp} Matches characters that need HTML escaping. */
const HTML_ESCAPE_REGEX = /[&<>"']/g;

/** @type {number} Default toast display duration in milliseconds. */
const TOAST_DURATION_MS = 3000;

/**
 * Escape a string for safe insertion into HTML.
 *
 * @param {string} str - The string to escape.
 * @returns {string} The escaped string, or the original value if not a string.
 */
export function htmlEscape(str) {
  if (typeof str !== 'string') return str;
  return str.replace(HTML_ESCAPE_REGEX, char => HTML_ESCAPE_MAP[char]);
}

/**
 * Display a toast notification message.
 *
 * The toast auto-dismisses after 3 seconds, but pauses
 * the timer while the user hovers over it.
 *
 * @param {string} message - The message to display.
 * @param {'info'|'success'|'warning'|'error'} [type='info'] - The toast type.
 */
export function toast(message, type = 'info') {
  const toastElement = document.createElement('div');
  toastElement.className = `toast ${type}`;
  toastElement.textContent = message;
  toastElement.setAttribute('role', 'alert');
  document.body.appendChild(toastElement);

  let dismissTimer = setTimeout(() => toastElement.remove(), TOAST_DURATION_MS);

  toastElement.addEventListener('mouseenter', () => {
    clearTimeout(dismissTimer);
  });
  toastElement.addEventListener('mouseleave', () => {
    dismissTimer = setTimeout(() => toastElement.remove(), TOAST_DURATION_MS);
  });
}
