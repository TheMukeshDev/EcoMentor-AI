const API_BASE = '/api';
let csrfToken = '';
let navigateFn = null;
let updateNavFn = null;

export function setAuthHandlers(handlers) {
  if (handlers.navigate) navigateFn = handlers.navigate;
  if (handlers.updateNav) updateNavFn = handlers.updateNav;
}

export async function api(path, options = {}) {
  const token = localStorage.getItem('id_token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (csrfToken && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method || '')) {
    headers['X-CSRF-Token'] = csrfToken;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem('id_token');
      csrfToken = '';
      if (updateNavFn) updateNavFn();
      if (navigateFn) navigateFn('#/login');
      throw new Error('Session expired. Please log in again.');
    }
    const body = await res.json().catch(() => ({}));
    throw new Error(body.message || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function fetchCsrfToken() {
  try {
    const res = await fetch('/api/auth/csrf-token');
    const data = await res.json();
    csrfToken = data.token || data.csrf_token || '';
  } catch (_) { }
}

export function clearCsrfToken() {
  csrfToken = '';
}
