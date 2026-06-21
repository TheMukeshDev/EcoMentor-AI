import { getToken, setToken } from './auth.js';

const API_BASE = import.meta.env.VITE_API_URL || '/api';
const REQUEST_TIMEOUT_MS = 15000;
let csrfToken = '';
let navigateFn = null;
let updateNavFn = null;

export function setAuthHandlers(handlers) {
  if (handlers.navigate) navigateFn = handlers.navigate;
  if (handlers.updateNav) updateNavFn = handlers.updateNav;
}

/**
 * Makes an authenticated request to the API.
 * @param {string} path - The API endpoint path.
 * @param {RequestInit} [options={}] - Fetch options.
 * @returns {Promise<any>} The parsed JSON response.
 * @throws {Error} If the request fails or is unauthorized.
 */
export async function api(path, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    } else if (!path.includes('/public') && !path.includes('/auth')) {
      throw new Error('Authentication required');
    }
    if (csrfToken && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method || '')) {
      headers['X-CSRF-Token'] = csrfToken;
    }
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers, signal: controller.signal });
    if (!res.ok) {
      if (res.status === 401) {
        setToken(null);
        csrfToken = '';
        if (updateNavFn) updateNavFn();
        if (navigateFn) navigateFn('#/login');
        throw new Error('Session expired. Please log in again.');
      }
      const body = await res.json().catch(() => ({}));
      throw new Error(body.message || `Request failed (${res.status})`);
    }
    return res.json();
  } finally {
    clearTimeout(timeoutId);
  }
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

/**
 * Fetches data from the API and caches it in sessionStorage.
 * @param {string} path - The API endpoint path.
 * @param {number} [ttlMs=30000] - Time to live in milliseconds.
 * @returns {Promise<any>} The cached or newly fetched data.
 */
export async function apiGetCached(path, ttlMs = 30000) {
  const cacheKey = `api_cache_${path}`;
  const cached = sessionStorage.getItem(cacheKey);
  if (cached) {
    try {
      const { data, timestamp } = JSON.parse(cached);
      if (Date.now() - timestamp < ttlMs) {
        return data;
      }
    } catch (error) {
      console.warn(`Cache corrupted for ${path}, clearing...`, error);
      sessionStorage.removeItem(cacheKey);
    }
  }
  const result = await api(path);
  sessionStorage.setItem(cacheKey, JSON.stringify({ data: result, timestamp: Date.now() }));
  return result;
}

export function clearCache() {
  Object.keys(sessionStorage).filter(k => k.startsWith('api_cache_')).forEach(k => sessionStorage.removeItem(k));
}
