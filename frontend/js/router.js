import { requireAuth } from './auth_guard.js';
import { getState } from './store.js';

const routes = {};

export function registerRoute(path, renderFn) {
  routes[path] = renderFn;
}

let _beforeRouteChange = null;

export function onBeforeRouteChange(fn) {
  _beforeRouteChange = fn;
}

let currentRenderedRoute = null;

export function navigate(hash) {
  if (getState('auth_initialized') !== true) {
    const app = document.getElementById('app');
    if (app) {
      app.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading...</span></div>';
    }
    import('./auth_service.js').then(({ authReady }) => {
      authReady.then(() => navigate(hash));
    });
    return;
  }

  let isAnchor = hash && hash.startsWith('#') && !hash.startsWith('#/');
  let path = isAnchor ? '/' : (hash.replace(/^#\/?/, '/') || '/');

  const redirect = requireAuth(path);
  if (redirect) {
    path = redirect.replace(/^#\/?/, '/') || '/';
    window.location.hash = redirect;
    return;
  }

  const app = document.getElementById('app');
  const renderFn = routes[path];

  // Update layout class based on route
  const homeRoutes = ['/', '/login', '/signup'];
  if (homeRoutes.includes(path)) {
    document.body.className = 'layout-home';
  } else {
    document.body.className = 'layout-dashboard';
  }

  if (_beforeRouteChange) _beforeRouteChange();
  
  if (renderFn) {
    if (currentRenderedRoute === path && isAnchor) {
      const el = document.getElementById(hash.substring(1));
      if (el) el.scrollIntoView({ behavior: 'smooth' });
      closeNav();
      return;
    }

    if (currentRenderedRoute !== path || !isAnchor) {
      app.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading...</span></div>';
      Promise.resolve(renderFn()).then(() => {
        currentRenderedRoute = path;
        updateNav();
        document.querySelectorAll('[data-nav]').forEach(l => {
          l.removeAttribute('aria-current');
          if (l.getAttribute('href') === hash || (hash === '' && l.getAttribute('href') === '#/')) {
            l.setAttribute('aria-current', 'page');
          }
        });
        
        if (isAnchor) {
          setTimeout(() => {
            const el = document.getElementById(hash.substring(1));
            if (el) el.scrollIntoView({ behavior: 'smooth' });
          }, 100);
        } else {
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    }
  } else {
    if (path !== '/') {
      console.warn(`Route not found: "${path}"`);
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
  const authenticated = getState('auth_initialized') === true ? getState('is_authenticated') === true : !!localStorage.getItem('id_token');
  document.querySelectorAll('.auth-hidden').forEach(el => el.style.display = authenticated ? '' : 'none');
  document.querySelectorAll('.auth-visible').forEach(el => el.style.display = authenticated ? 'none' : '');
}

function closeNav() {
  const mobileDrawer = document.getElementById('mobile-drawer');
  if (mobileDrawer) mobileDrawer.classList.remove('open');
  
  const dashboardSidebar = document.getElementById('dashboard-sidebar');
  if (dashboardSidebar && window.innerWidth <= 768) {
    dashboardSidebar.classList.remove('mobile-open');
  }
}
