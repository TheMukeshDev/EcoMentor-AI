const routes = {};

export function registerRoute(path, renderFn) {
  routes[path] = renderFn;
}

export function navigate(hash) {
  const path = hash.replace(/^#\/?/, '/') || '/';
  const app = document.getElementById('app');

  const renderFn = routes[path];
  if (renderFn) {
    app.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading...</span></div>';
    Promise.resolve(renderFn()).then(() => {
      updateNav();
      document.querySelectorAll('[data-nav], [data-bottom-nav]').forEach(l => {
        l.removeAttribute('aria-current');
        if (l.getAttribute('href') === hash || (hash === '' && l.getAttribute('href') === '#/')) {
          l.setAttribute('aria-current', 'page');
        }
      });
    });
  } else {
    if (path !== '/') {
      console.warn(`Route not found: "${path}" (from hash: "${hash}")`);
    }
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

export function updateNav() {
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
