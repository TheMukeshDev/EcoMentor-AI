import '../css/variables.css';
import '../css/reset.css';
import '../css/base.css';
import '../css/layout.css';
import '../css/components.css';
import '../css/utilities.css';
import '../css/dashboard.css';
import '../css/premium-home.css';

import { htmlEscape, toast } from './utils.js';
import { initTheme, toggleTheme } from './theme.js';
import { api, fetchCsrfToken, clearCsrfToken, setAuthHandlers } from './api-client.js';
import { registerRoute, navigate, updateNav } from './router.js';
import { initAuthListener, logout as firebaseLogout, onAuthStateChange, authReady } from './auth_service.js';
import { setupAuthGuard } from './auth_guard.js';
import { subscribe, setState, getState } from './store.js';

export { htmlEscape, toast, api, fetchCsrfToken, registerRoute, navigate, initTheme };

window.addEventListener('error', (event) => {
  console.error('Global error:', event.error || event.message);
  toast('An unexpected error occurred. Please refresh the page.', 'error');
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled rejection:', event.reason);
  toast('An unexpected error occurred. Please try again.', 'error');
});

setAuthHandlers({ navigate, updateNav });

onAuthStateChange((user, profile) => {
  updateNav();
});

setupAuthGuard();

window.addEventListener('hashchange', () => navigate(window.location.hash));

async function logoutUser() {
  await firebaseLogout();
  clearCsrfToken();
  updateNav();
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

  // Theme toggles
  document.getElementById('theme-toggle-home')?.addEventListener('click', toggleTheme);
  document.getElementById('theme-toggle-dash')?.addEventListener('click', toggleTheme);

  // Home Mobile Drawer
  const mobileDrawer = document.getElementById('mobile-drawer');
  document.getElementById('mobile-menu-open')?.addEventListener('click', () => {
    mobileDrawer?.classList.add('open');
  });
  document.getElementById('mobile-menu-close')?.addEventListener('click', () => {
    mobileDrawer?.classList.remove('open');
  });
  document.getElementById('drawer-backdrop')?.addEventListener('click', () => {
    mobileDrawer?.classList.remove('open');
  });

  // Dashboard Sidebar Toggle (Desktop)
  const dashboardSidebar = document.getElementById('dashboard-sidebar');
  document.getElementById('sidebar-collapse-btn')?.addEventListener('click', () => {
    dashboardSidebar?.classList.toggle('collapsed');
  });

  // Dashboard Sidebar Toggle (Mobile)
  const dashboardOverlay = document.getElementById('dashboard-drawer-overlay');
  document.getElementById('mobile-sidebar-toggle')?.addEventListener('click', () => {
    dashboardSidebar?.classList.add('mobile-open');
  });
  dashboardOverlay?.addEventListener('click', () => {
    dashboardSidebar?.classList.remove('mobile-open');
  });

  // Quick Action Dropdown
  const quickActionContainer = document.getElementById('quick-action-container');
  document.getElementById('quick-action-btn')?.addEventListener('click', (e) => {
    e.stopPropagation();
    quickActionContainer?.classList.toggle('open');
  });
  document.addEventListener('click', (e) => {
    if (!quickActionContainer?.contains(e.target)) {
      quickActionContainer?.classList.remove('open');
    }
  });

  // Home Header Scroll Effect
  const homeHeader = document.getElementById('home-header');
  if (homeHeader) {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        homeHeader.classList.remove('at-top');
      } else {
        homeHeader.classList.add('at-top');
      }
    };
    window.addEventListener('scroll', handleScroll);
    handleScroll(); // init
  }

  // Logout Buttons
  document.getElementById('sidebar-logout-btn')?.addEventListener('click', (e) => {
    e.preventDefault();
    logoutUser();
  });
  document.getElementById('mobile-logout-btn')?.addEventListener('click', (e) => {
    e.preventDefault();
    logoutUser();
  });

  await authReady;

  updateNav();
  fetchCsrfToken();
  navigate(window.location.hash);
});
