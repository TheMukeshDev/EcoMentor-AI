// CSS imports (Vite bundles these)
import '../css/variables.css';
import '../css/reset.css';
import '../css/base.css';
import '../css/layout.css';
import '../css/components.css';
import '../css/utilities.css';

// Feature modules
import { htmlEscape, toast } from './utils.js';
import { initTheme, toggleTheme } from './theme.js';
import { api, fetchCsrfToken, clearCsrfToken, setAuthHandlers } from './api-client.js';
import { registerRoute, navigate, updateNav } from './router.js';

// Re-export for page modules
export { htmlEscape, toast, api, fetchCsrfToken, registerRoute, navigate, initTheme };

setAuthHandlers({ navigate, updateNav });

window.addEventListener('hashchange', () => navigate(window.location.hash));
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
  document.getElementById('theme-toggle')?.addEventListener('click', toggleTheme);
  document.getElementById('nav-toggle')?.addEventListener('click', () => {
    const nav = document.getElementById('nav-links');
    const toggle = document.getElementById('nav-toggle');
    const open = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open);
  });
  document.getElementById('logout-btn')?.addEventListener('click', () => {
    localStorage.removeItem('id_token');
    clearCsrfToken();
    updateNav();
    navigate('');
  });
  updateNav();
  fetchCsrfToken();
  navigate(window.location.hash);
});
