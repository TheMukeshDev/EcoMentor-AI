import '../css/variables.css';
import '../css/reset.css';
import '../css/base.css';
import '../css/layout.css';
import '../css/components.css';
import '../css/utilities.css';
import '../css/dashboard.css';

import { htmlEscape, toast } from './utils.js';
import { initTheme, toggleTheme } from './theme.js';
import { api, fetchCsrfToken, clearCsrfToken, setAuthHandlers } from './api-client.js';
import { registerRoute, navigate, updateNav, updateBottomNav } from './router.js';
import { initAuthListener, logout as firebaseLogout, onAuthStateChange } from './auth_service.js';
import { setupAuthGuard } from './auth_guard.js';
import { subscribe, setState, getState } from './store.js';

export { htmlEscape, toast, api, fetchCsrfToken, registerRoute, navigate, initTheme };

setAuthHandlers({ navigate, updateNav });

onAuthStateChange((user, profile) => {
  updateNav();
  updateBottomNav();
});

setupAuthGuard();

window.addEventListener('hashchange', () => navigate(window.location.hash));

async function logoutUser() {
  await firebaseLogout();
  clearCsrfToken();
  updateNav();
  updateBottomNav();
  navigate('');
  toast('Logged out successfully', 'info');
}

window.addEventListener('load', async () => {
  await Promise.all([
    import('./home.js'),
    import('./auth.js'),
    import('./dashboard.js'),
    import('./activities.js'),
    import('./leaderboard.js'),
    import('./achievements.js'),
    import('./coach.js'),
    import('./report.js'),
    import('./profile.js'),
    import('./settings.js'),
  ]);

  initTheme();
  initAuthListener();

  document.getElementById('theme-toggle')?.addEventListener('click', toggleTheme);
  document.getElementById('nav-toggle')?.addEventListener('click', () => {
    const nav = document.getElementById('nav-links');
    const toggle = document.getElementById('nav-toggle');
    const open = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open);
  });

  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      logoutUser();
    });
  }

  const storedUser = localStorage.getItem('firebase_user');
  if (storedUser) {
    setState('is_authenticated', true);
  }

  updateNav();
  updateBottomNav();
  fetchCsrfToken();
  navigate(window.location.hash);
});
