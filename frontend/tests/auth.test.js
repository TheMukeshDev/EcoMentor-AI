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
    matches: false, media: query, onchange: null,
    addListener: vi.fn(), removeListener: vi.fn(),
    addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
  }));
});

function clearStorage() {
  Object.keys(store).forEach(k => delete store[k]);
}

describe('auth module', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="app"></div>';
    clearStorage();
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
  });

  it('registers /login and /signup routes', async () => {
    // Import auth.js — it calls registerRoute at module level
    await import('../js/auth.js');
    const { navigate } = await import('../js/main.js');

    // Trigger /login route
    navigate('#/login');
    await new Promise(r => setTimeout(r, 20));

    const loginForm = document.getElementById('login-form');
    expect(loginForm).toBeTruthy();
    expect(document.getElementById('login-email')).toBeTruthy();
    expect(document.getElementById('login-password')).toBeTruthy();
  });

  it('renders signup form via navigate', async () => {
    await import('../js/auth.js');
    const { navigate } = await import('../js/main.js');

    navigate('#/signup');
    await new Promise(r => setTimeout(r, 20));

    const signupForm = document.getElementById('signup-form');
    expect(signupForm).toBeTruthy();
    expect(document.getElementById('signup-name')).toBeTruthy();
    expect(document.getElementById('signup-email')).toBeTruthy();
    expect(document.getElementById('signup-password')).toBeTruthy();
  });

  it('displays email validation error on empty login submit', async () => {
    await import('../js/auth.js');
    const { navigate } = await import('../js/main.js');

    navigate('#/login');
    await new Promise(r => setTimeout(r, 20));

    // Click submit with empty fields
    document.querySelector('#login-form button[type="submit"]').click();
    await new Promise(r => setTimeout(r, 10));

    expect(document.getElementById('login-email-error').textContent).toBe('Email is required');
  });

  it('displays password validation error on empty password', async () => {
    await import('../js/auth.js');
    const { navigate } = await import('../js/main.js');

    navigate('#/login');
    await new Promise(r => setTimeout(r, 20));

    document.getElementById('login-email').value = 'test@example.com';
    document.querySelector('#login-form button[type="submit"]').click();
    await new Promise(r => setTimeout(r, 10));

    expect(document.getElementById('login-password-error').textContent).toBe('Password is required');
  });

  it('calls api on successful login', async () => {
    await import('../js/auth.js');
    const { navigate } = await import('../js/main.js');

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: { id_token: 'test-token' } }),
    });
    global.fetch = mockFetch;

    navigate('#/login');
    await new Promise(r => setTimeout(r, 20));

    document.getElementById('login-email').value = 'a@b.com';
    document.getElementById('login-password').value = 'password123';
    document.querySelector('#login-form button[type="submit"]').click();
    await new Promise(r => setTimeout(r, 30));

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/auth/login',
      expect.objectContaining({ method: 'POST' })
    );
    expect(localStorage.getItem('id_token')).toBe('test-token');
  });

  it('shows api error message on login failure', async () => {
    await import('../js/auth.js');
    const { navigate } = await import('../js/main.js');

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: () => Promise.resolve({ message: 'Invalid credentials' }),
    });

    navigate('#/login');
    await new Promise(r => setTimeout(r, 20));

    document.getElementById('login-email').value = 'a@b.com';
    document.getElementById('login-password').value = 'wrong';
    document.querySelector('#login-form button[type="submit"]').click();
    await new Promise(r => setTimeout(r, 20));

    expect(document.getElementById('login-error').textContent).toBe('Invalid credentials');
  });

  it('clears token and shows session expired on 401', async () => {
    await import('../js/auth.js');
    const { navigate } = await import('../js/main.js');

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ message: 'Token expired' }),
    });

    navigate('#/login');
    await new Promise(r => setTimeout(r, 20));

    // Set token after navigating to login so auth guard doesn't redirect away
    localStorage.setItem('id_token', 'expired-token');

    document.getElementById('login-email').value = 'a@b.com';
    document.getElementById('login-password').value = 'password';
    document.querySelector('#login-form button[type="submit"]').click();
    await new Promise(r => setTimeout(r, 20));

    expect(localStorage.getItem('id_token')).toBeNull();
    expect(document.getElementById('login-error').textContent)
      .toBe('Session expired. Please log in again.');
  });

  it('displays signup name validation', async () => {
    await import('../js/auth.js');
    const { navigate } = await import('../js/main.js');

    navigate('#/signup');
    await new Promise(r => setTimeout(r, 20));

    document.querySelector('#signup-form button[type="submit"]').click();
    await new Promise(r => setTimeout(r, 10));

    expect(document.getElementById('signup-name-error').textContent).toBe('Name is required');
  });

  it('displays signup password validation', async () => {
    await import('../js/auth.js');
    const { navigate } = await import('../js/main.js');

    navigate('#/signup');
    await new Promise(r => setTimeout(r, 20));

    document.getElementById('signup-name').value = 'Test User';
    document.getElementById('signup-email').value = 'test@test.com';
    document.querySelector('#signup-form button[type="submit"]').click();
    await new Promise(r => setTimeout(r, 10));

    expect(document.getElementById('signup-password-error').textContent)
      .toBe('Password must be at least 6 characters');
  });
});
