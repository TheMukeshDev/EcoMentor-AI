import { registerRoute } from './main.js';

function renderSettings() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <div style="max-width:500px;margin:0 auto">
      <h1 style="margin-bottom:24px">Settings</h1>

      <div class="card" style="margin-bottom:16px">
        <div class="card-title">Theme</div>
        <div style="margin-top:12px">
          <button class="btn btn-secondary" id="settings-theme-toggle">Toggle Dark Mode</button>
        </div>
      </div>

      <div class="card" style="margin-bottom:16px">
        <div class="card-title">Account</div>
        <p style="margin-top:8px;color:var(--color-text-secondary);font-size:0.9rem">Account settings are managed through your profile.</p>
        <a href="#/profile" class="btn btn-ghost" style="margin-top:8px">View Profile</a>
      </div>

      <div class="card" style="margin-bottom:16px">
        <div class="card-title">About</div>
        <p style="margin-top:8px;color:var(--color-text-secondary);font-size:0.9rem">EcoMentor AI v1.0.0 &mdash; Track, understand, and reduce your carbon footprint.</p>
      </div>
    </div>
  `;

  document.getElementById('settings-theme-toggle')?.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  });
}

registerRoute('/settings', renderSettings);
