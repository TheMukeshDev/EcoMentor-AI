import { getCurrentToken } from './auth_service.js';

const API_BASE = import.meta.env.VITE_API_URL || '/api';
let csrfToken = '';
let navigateFn = null;
let updateNavFn = null;

export function setAuthHandlers(handlers) {
  if (handlers.navigate) navigateFn = handlers.navigate;
  if (handlers.updateNav) updateNavFn = handlers.updateNav;
}

export async function api(path, options = {}) {
  const token = await getCurrentToken() || localStorage.getItem('id_token');
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
    const res = await api('/auth/csrf-token');
    csrfToken = res.token || res.csrf_token || res.data?.csrf_token || '';
  } catch (_) { }
}

export function clearCsrfToken() {
  csrfToken = '';
}

export async function apiGetCached(path, ttlMs = 30000) {
  const cacheKey = `api_cache_${path}`;
  const cached = sessionStorage.getItem(cacheKey);
  if (cached) {
    try {
      const { data, timestamp } = JSON.parse(cached);
      if (Date.now() - timestamp < ttlMs) {
        return data;
      }
    } catch {}
  }
  const result = await api(path);
  sessionStorage.setItem(cacheKey, JSON.stringify({ data: result, timestamp: Date.now() }));
  return result;
}

export function clearCache() {
  Object.keys(sessionStorage).filter(k => k.startsWith('api_cache_')).forEach(k => sessionStorage.removeItem(k));
}
