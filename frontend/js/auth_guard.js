import { getState, subscribe } from './store.js';
import { navigate } from './router.js';

const protectedRoutes = [
  '/dashboard',
  '/log',
  '/coach',
  '/leaderboard',
  '/achievements',
  '/report',
  '/profile',
  '/settings',
];

const guestOnlyRoutes = ['/login', '/signup'];

export function isAuthenticated() {
  return getState('is_authenticated') === true || !!localStorage.getItem('id_token');
}

export function requireAuth(route) {
  if (protectedRoutes.includes(route) && !isAuthenticated()) {
    return '#/login';
  }
  if (guestOnlyRoutes.includes(route) && isAuthenticated()) {
    return '#/dashboard';
  }
  return null;
}

export function setupAuthGuard() {
  subscribe('is_authenticated', (authed) => {
    const hash = window.location.hash || '#/';
    const path = hash.replace(/^#\/?/, '/') || '/';
    if (!authed && protectedRoutes.includes(path)) {
      navigate('#/login');
    }
    if (authed && guestOnlyRoutes.includes(path)) {
      navigate('#/dashboard');
    }
  });
}
