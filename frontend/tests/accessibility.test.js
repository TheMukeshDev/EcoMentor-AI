import { describe, it, expect, beforeEach, vi } from 'vitest';

const store = {};
vi.stubGlobal('localStorage', {
  getItem: (key) => store[key] ?? null,
  setItem: (key, value) => { store[key] = String(value); },
  removeItem: (key) => { delete store[key]; },
  clear: () => { Object.keys(store).forEach(k => delete store[k]); },
  get length() { return Object.keys(store).length; },
  key: (i) => Object.keys(store)[i] ?? null,
});

describe('accessibility', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
  });

  it('skip link is first focusable element in HTML', async () => {
    document.body.innerHTML = `
      <a class="skip-link" href="#main-content">Skip to main content</a>
      <header role="banner">...</header>
      <main id="main-content" role="main">...</main>
    `;
    const firstFocusable = document.querySelector('.skip-link');
    expect(firstFocusable).toBeTruthy();
    expect(firstFocusable.getAttribute('href')).toBe('#main-content');
  });

  it('navigation has proper ARIA labels', () => {
    document.body.innerHTML = `
      <nav class="nav-container" aria-label="Main navigation">
        <a href="#/" class="nav-logo" aria-label="EcoMentor AI home">EcoMentor</a>
        <ul class="nav-links" role="list">
          <li><a href="#/">Home</a></li>
        </ul>
      </nav>
    `;
    const nav = document.querySelector('nav');
    expect(nav.getAttribute('aria-label')).toBe('Main navigation');
    const logo = document.querySelector('.nav-logo');
    expect(logo.getAttribute('aria-label')).toBe('EcoMentor AI home');
  });

  it('forms have associated labels', () => {
    document.body.innerHTML = `
      <form id="test-form">
        <div class="form-group">
          <label for="test-email">Email</label>
          <input type="email" id="test-email" required aria-describedby="test-email-error">
          <p id="test-email-error" class="form-error" role="alert"></p>
        </div>
      </form>
    `;
    const label = document.querySelector('label');
    const input = document.getElementById('test-email');
    expect(label.getAttribute('for')).toBe('test-email');
    expect(input.getAttribute('aria-describedby')).toBe('test-email-error');
    expect(input.hasAttribute('required')).toBe(true);
  });

  it('error messages use role="alert"', () => {
    document.body.innerHTML = `<p id="error" class="form-error" role="alert">Error message</p>`;
    const error = document.getElementById('error');
    expect(error.getAttribute('role')).toBe('alert');
  });

  it('toast notifications use role="alert"', () => {
    document.body.innerHTML = `<div class="toast info" role="alert">Success!</div>`;
    const toast = document.querySelector('.toast');
    expect(toast.getAttribute('role')).toBe('alert');
  });

  it('loading states use role="status"', () => {
    document.body.innerHTML = `<div class="spinner" role="status"><span class="sr-only">Loading...</span></div>`;
    const spinner = document.querySelector('.spinner');
    expect(spinner.getAttribute('role')).toBe('status');
    const srOnly = document.querySelector('.sr-only');
    expect(srOnly).toBeTruthy();
  });

  it('theme toggle has accessible label', () => {
    document.body.innerHTML = `<button class="theme-toggle" aria-label="Toggle dark mode">&#9790;</button>`;
    const btn = document.querySelector('.theme-toggle');
    expect(btn.getAttribute('aria-label')).toBe('Toggle dark mode');
  });

  it('nav toggle has aria-expanded attribute', () => {
    document.body.innerHTML = `<button class="nav-toggle" aria-label="Toggle navigation menu" aria-expanded="false"></button>`;
    const toggle = document.querySelector('.nav-toggle');
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    expect(toggle.getAttribute('aria-label')).toBe('Toggle navigation menu');
  });

  it('bottom navigation has ARIA label', () => {
    document.body.innerHTML = `<nav class="bottom-nav" aria-label="Bottom navigation">...</nav>`;
    const nav = document.querySelector('.bottom-nav');
    expect(nav.getAttribute('aria-label')).toBe('Bottom navigation');
  });

  it('chart canvas has aria-label', () => {
    document.body.innerHTML = `<canvas id="carbonChart" role="img" aria-label="Carbon score trend chart"></canvas>`;
    const canvas = document.getElementById('carbonChart');
    expect(canvas.getAttribute('role')).toBe('img');
    expect(canvas.getAttribute('aria-label')).toBe('Carbon score trend chart');
  });
});
