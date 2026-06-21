/**
 * Client-side hash-based router.
 *
 * Manages route registration, navigation, layout switching,
 * and active navigation link state.
 *
 * @module router
 */

import { requireAuth } from './auth_guard.js';
import { getState } from './store.js';

/** @type {Object<string, Function>} Registered route handlers. */
const routes = {};

/**
 * Register a route handler for a given path.
 * @param {string} path - The route path (e.g. '/dashboard').
 * @param {Function} renderFn - Async function to render the page content.
 */
export function registerRoute(path, renderFn) {
  routes[path] = renderFn;
}

/** @type {Function|null} */
let _beforeRouteChange = null;

/**
 * Register a callback invoked before every route change.
 * @param {Function} callback - The pre-navigation callback.
 */
export function onBeforeRouteChange(callback) {
  _beforeRouteChange = callback;
}

/** @type {string|null} */
let currentRenderedRoute = null;

/** Routes that use the homepage layout. */
const HOME_ROUTES = ['/', '/login', '/signup'];

/**
 * Navigate to a hash-based route.
 * Handles auth guards, layout switching, and scroll management.
 *
 * @param {string} hash - The hash string (e.g. '#/dashboard').
 */
export function navigate(hash) {
  if (getState('auth_initialized') !== true) {
    showLoadingSpinner();
    import('./auth_service.js').then(({ authReady }) => {
      authReady.then(() => navigate(hash));
    });
    return;
  }

  const isAnchor = hash && hash.startsWith('#') && !hash.startsWith('#/');
  let path = isAnchor ? '/' : (hash.replace(/^#\/?/, '/') || '/');

  const redirect = requireAuth(path);
  if (redirect) {
    path = redirect.replace(/^#\/?/, '/') || '/';
    window.location.hash = redirect;
    return;
  }

  applyLayoutClass(path);
  if (_beforeRouteChange) _beforeRouteChange();

  const app = document.getElementById('app');
  const renderFn = routes[path];

  if (renderFn) {
    renderRoute(app, path, hash, isAnchor, renderFn);
  } else {
    renderNotFound(app, path);
  }

  closeAllNavigation();
  document.getElementById('main-content')?.focus();
}

/**
 * Update navigation link visibility based on authentication state.
 * Toggles `.auth-hidden` and `.auth-visible` elements.
 */
export function updateNav() {
  const isInitialized = getState('auth_initialized') === true;
  const authenticated = isInitialized
    ? getState('is_authenticated') === true
    : !!localStorage.getItem('id_token');

  document.querySelectorAll('.auth-hidden').forEach(element => {
    element.style.display = authenticated ? '' : 'none';
  });
  document.querySelectorAll('.auth-visible').forEach(element => {
    element.style.display = authenticated ? 'none' : '';
  });
}

// ---------------------------------------------------------------------------
// Private helpers
// ---------------------------------------------------------------------------

/**
 * Show a loading spinner in the main app container.
 */
function showLoadingSpinner() {
  const app = document.getElementById('app');
  if (app) {
    app.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading...</span></div>'; /* safe HTML - static spinner */
  }
}

/**
 * Apply the correct body layout class based on the current route.
 * @param {string} path - The resolved route path.
 */
function applyLayoutClass(path) {
  document.body.className = HOME_ROUTES.includes(path)
    ? 'layout-home'
    : 'layout-dashboard';
}

/**
 * Render a matched route, handling anchors and scroll position.
 *
 * @param {HTMLElement} app - The app container element.
 * @param {string} path - The resolved route path.
 * @param {string} hash - The original hash string.
 * @param {boolean} isAnchor - Whether this is an in-page anchor navigation.
 * @param {Function} renderFn - The route's render function.
 */
function renderRoute(app, path, hash, isAnchor, renderFn) {
  if (currentRenderedRoute === path && isAnchor) {
    scrollToAnchor(hash);
    return;
  }

  if (currentRenderedRoute !== path || !isAnchor) {
    showLoadingSpinner();
    Promise.resolve(renderFn()).then(() => {
      currentRenderedRoute = path;
      updateNav();
      updateActiveNavLinks(hash);

      if (isAnchor) {
        setTimeout(() => scrollToAnchor(hash), 100);
      } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  }
}

/**
 * Render a 404 Not Found page.
 * @param {HTMLElement} app - The app container element.
 * @param {string} path - The unmatched route path.
 */
function renderNotFound(app, path) {
  if (path !== '/') {
    console.warn(`Route not found: "${path}"`);
  }
  app.innerHTML = /* safe HTML - static 404 page */ `
    <div class="error-state" style="padding:80px 20px">
      <span class="empty-icon" style="font-size:4rem">&#128683;</span>
      <h2 style="margin-bottom:8px">Page Not Found</h2>
      <p style="color:var(--color-text-secondary);margin-bottom:20px">The page you're looking for doesn't exist.</p>
      <a href="#/" class="btn btn-primary">Go Home</a>
    </div>
  `;
}

/**
 * Update aria-current attributes on navigation links.
 * @param {string} hash - The current hash string.
 */
function updateActiveNavLinks(hash) {
  document.querySelectorAll('[data-nav]').forEach(link => {
    link.removeAttribute('aria-current');
    const href = link.getAttribute('href');
    if (href === hash || (hash === '' && href === '#/')) {
      link.setAttribute('aria-current', 'page');
    }
  });
}

/**
 * Smooth-scroll to an anchor element.
 * @param {string} hash - The hash string (e.g. '#hp-features').
 */
function scrollToAnchor(hash) {
  const element = document.getElementById(hash.substring(1));
  if (element) element.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Close all open navigation drawers and sidebars.
 */
function closeAllNavigation() {
  const mobileDrawer = document.getElementById('mobile-drawer');
  if (mobileDrawer) mobileDrawer.classList.remove('open');

  const dashboardSidebar = document.getElementById('dashboard-sidebar');
  if (dashboardSidebar && window.innerWidth <= 768) {
    dashboardSidebar.classList.remove('mobile-open');
  }
}
