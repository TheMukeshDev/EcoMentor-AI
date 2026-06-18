import { api, registerRoute, htmlEscape } from './main.js';

async function renderProfile() {
  const app = document.getElementById('app');
  app.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading profile...</span></div>';

  try {
    const profileRes = await api('/auth/profile').catch(() => ({ data: {} }));
    const profile = profileRes.data || {};

    app.innerHTML = `
      <div style="max-width:500px;margin:0 auto">
        <h1 style="margin-bottom:24px">Profile</h1>

        <div class="card" style="text-align:center;margin-bottom:24px">
          <div style="font-size:4rem;margin-bottom:8px">&#127807;</div>
          <h2 style="margin-bottom:4px">${htmlEscape(profile.name) || 'Eco User'}</h2>
          <p style="color:var(--color-text-muted)">${htmlEscape(profile.email) || 'No email'}</p>
        </div>

        <div class="card-grid">
          <div class="card">
            <div class="card-title">Total Points</div>
            <div class="card-value">${profile.points || 0}</div>
          </div>
          <div class="card">
            <div class="card-title">Level</div>
            <div class="card-value">${htmlEscape(profile.level) || 'Beginner'}</div>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    app.innerHTML = `
      <div class="error-state">
        <span class="empty-icon">&#9888;</span>
        <p>${htmlEscape(err.message)}</p>
        <button class="btn btn-primary" onclick="window.location.hash='#/profile'">Retry</button>
      </div>
    `;
  }
}

registerRoute('/profile', renderProfile);
