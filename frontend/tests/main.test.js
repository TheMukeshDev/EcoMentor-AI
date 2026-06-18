import { describe, it, expect, beforeEach, vi, beforeAll } from 'vitest';

const store = {};
vi.stubGlobal('localStorage', {
  getItem: (key) => store[key] ?? null,
  setItem: (key, value) => { store[key] = String(value); },
  removeItem: (key) => { delete store[key]; },
  clear: () => { Object.keys(store).forEach(k => delete store[k]); },
  get length() { return Object.keys(store).length; },
  key: (i) => Object.keys(store)[i] ?? null,
});

beforeAll(() => {
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
  window.matchMedia = vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
});

function clearStorage() {
  Object.keys(store).forEach(k => delete store[k]);
}

global.Chart = class Chart {
  constructor() { this.destroy = vi.fn(); }
};

describe('htmlEscape', () => {
  it('escapes HTML special chars', async () => {
    const { htmlEscape } = await import('../js/main.js');
    expect(htmlEscape('&<>"\'')).toBe('&amp;&lt;&gt;&quot;&#39;');
  });

  it('returns numbers as-is', async () => {
    const { htmlEscape } = await import('../js/main.js');
    expect(htmlEscape(42)).toBe(42);
    expect(htmlEscape(0)).toBe(0);
  });

  it('passes safe strings through unchanged', async () => {
    const { htmlEscape } = await import('../js/main.js');
    expect(htmlEscape('hello world')).toBe('hello world');
  });

  it('handles undefined and null', async () => {
    const { htmlEscape } = await import('../js/main.js');
    expect(htmlEscape(undefined)).toBe(undefined);
    expect(htmlEscape(null)).toBe(null);
  });

  it('escapes script injection', async () => {
    const { htmlEscape } = await import('../js/main.js');
    expect(htmlEscape('<script>alert(1)</script>'))
      .toBe('&lt;script&gt;alert(1)&lt;/script&gt;');
  });
});

describe('api', () => {
  beforeEach(() => {
    clearStorage();
    vi.restoreAllMocks();
  });

  it('injects Authorization header when token exists', async () => {
    localStorage.setItem('id_token', 'test-token');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: 'ok' }),
    });
    global.fetch = mockFetch;

    const { api } = await import('../js/main.js');
    await api('/test');

    const headers = mockFetch.mock.calls[0][1].headers;
    expect(headers['Authorization']).toBe('Bearer test-token');
  });

  it('throws with server error message on non-ok response', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ message: 'Bad request' }),
    });
    global.fetch = mockFetch;

    const { api } = await import('../js/main.js');
    await expect(api('/fail')).rejects.toThrow('Bad request');
  });

  it('throws status fallback when no error message', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    });
    global.fetch = mockFetch;

    const { api } = await import('../js/main.js');
    await expect(api('/fail')).rejects.toThrow('Request failed (500)');
  });

  it('includes CSRF token for POST requests', async () => {
    localStorage.setItem('id_token', 'test-token');
    const mockFetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ csrf_token: 'csrf-abc' }),
    }).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: 'ok' }),
    });
    global.fetch = mockFetch;

    const { api, fetchCsrfToken } = await import('../js/main.js');
    await fetchCsrfToken();
    await api('/test', { method: 'POST', body: '{}' });

    const reqHeaders = mockFetch.mock.calls[1][1].headers;
    expect(reqHeaders['X-CSRF-Token']).toBe('csrf-abc');
  });
});

describe('toast', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('creates toast element with role="alert"', async () => {
    const { toast } = await import('../js/main.js');
    toast('Hello', 'success');

    const el = document.querySelector('.toast');
    expect(el).toBeTruthy();
    expect(el.textContent).toBe('Hello');
    expect(el.className).toBe('toast success');
    expect(el.getAttribute('role')).toBe('alert');
  });

  it('removes toast after 3 seconds', async () => {
    vi.useFakeTimers();
    const { toast } = await import('../js/main.js');
    toast('Temp', 'info');

    expect(document.querySelector('.toast')).toBeTruthy();

    vi.advanceTimersByTime(3000);
    expect(document.querySelector('.toast')).toBeNull();

    vi.useRealTimers();
  });
});

describe('initTheme', () => {
  beforeEach(() => {
    clearStorage();
    document.documentElement.removeAttribute('data-theme');
    document.body.innerHTML = '<button id="theme-toggle"></button>';
    window.matchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
  });

  it('defaults to light theme when no preference', async () => {
    const { initTheme } = await import('../js/main.js');
    initTheme();
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('reads saved theme from localStorage', async () => {
    localStorage.setItem('theme', 'dark');
    const { initTheme } = await import('../js/main.js');
    initTheme();
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });
});
