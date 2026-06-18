const API_BASE = '/api';

export async function api(path, options = {}) {
  const token = localStorage.getItem('id_token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.message || `Request failed (${res.status})`);
  }
  return res.json();
}

function toast(message, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  el.setAttribute('role', 'alert');
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

export { toast };

// Dark mode
function initTheme() {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = saved || (prefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', theme);
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.textContent = theme === 'dark' ? '\u2600' : '\u263E';
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.textContent = next === 'dark' ? '\u2600' : '\u263E';
  if (window._carbonChart instanceof Chart) {
    window._carbonChart.destroy();
    window._carbonChart = null;
  }
}

// Nav
function updateNav() {
  const token = localStorage.getItem('id_token');
  document.querySelectorAll('.auth-hidden').forEach(el => el.style.display = token ? '' : 'none');
  document.querySelectorAll('.auth-visible').forEach(el => el.style.display = token ? 'none' : '');
}

function closeNav() {
  const nav = document.getElementById('nav-links');
  const toggle = document.getElementById('nav-toggle');
  if (nav) nav.classList.remove('open');
  if (toggle) toggle.setAttribute('aria-expanded', 'false');
}

// Router
const routes = {};

function registerRoute(path, renderFn) {
  routes[path] = renderFn;
}

function navigate(hash) {
  const path = hash.replace(/^#\/?/, '/') || '/';
  const app = document.getElementById('app');

  const renderFn = routes[path];
  if (renderFn) {
    app.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading...</span></div>';
    Promise.resolve(renderFn()).then(() => {
      updateNav();
      document.querySelectorAll('[data-nav]').forEach(l => {
        l.removeAttribute('aria-current');
        if (l.getAttribute('href') === hash || (hash === '' && l.getAttribute('href') === '#/')) {
          l.setAttribute('aria-current', 'page');
        }
      });
    });
  } else {
    app.innerHTML = `
      <div class="error-state" style="padding:80px 20px">
        <span class="empty-icon" style="font-size:4rem">&#128683;</span>
        <h2 style="margin-bottom:8px">Page Not Found</h2>
        <p style="color:var(--color-text-secondary);margin-bottom:20px">The page you're looking for doesn't exist.</p>
        <a href="#/" class="btn btn-primary">Go Home</a>
      </div>
    `;
  }

  closeNav();
  document.getElementById('main-content')?.focus();
}

window.addEventListener('hashchange', () => navigate(window.location.hash));
window.addEventListener('load', () => {
  initTheme();
  document.getElementById('theme-toggle')?.addEventListener('click', toggleTheme);
  document.getElementById('nav-toggle')?.addEventListener('click', () => {
    const nav = document.getElementById('nav-links');
    const toggle = document.getElementById('nav-toggle');
    const open = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open);
  });
  document.getElementById('logout-btn')?.addEventListener('click', () => {
    localStorage.removeItem('id_token');
    updateNav();
    navigate('');
  });
  updateNav();
  navigate(window.location.hash);
});

export { registerRoute, navigate };
