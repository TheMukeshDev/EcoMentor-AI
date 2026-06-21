import { api, registerRoute, htmlEscape } from './main.js';
import { getState } from './store.js';

async function renderProfile() {
  const app = document.getElementById('app');
  app.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading profile...</span></div>'; /* safe HTML - static spinner */

  try {
    const profile = getState('user_profile') || await api('/auth/profile').then(r => r.data || r).catch(() => ({}));

    const photoURL = profile.photoURL || '';
    const name = profile.name || profile.displayName || 'Eco User';
    const email = profile.email || 'No email';
    const level = profile.level || 1;
    const streak = profile.streak || 0;
    const ecoScore = profile.ecoScore || 0;
    const totalSaved = profile.totalCarbonSaved || 0;
    const badges = profile.badges || [];
    const createdAt = profile.createdAt || profile.created_at || '';

    app.innerHTML = /* safe HTML - content escaped with htmlEscape() */ `
      <div style="max-width:500px;margin:0 auto">
        <h1 style="margin-bottom:24px">Profile</h1>

        <div class="card" style="text-align:center;margin-bottom:24px">
          <div style="margin:0 auto 12px;width:80px;height:80px;border-radius:50%;overflow:hidden;background:var(--color-primary-bg);display:flex;align-items:center;justify-content:center;font-size:2.5rem">
            ${photoURL ? `<img src="${htmlEscape(photoURL)}" alt="" style="width:100%;height:100%;object-fit:cover">` : '&#127807;'}
          </div>
          <h2 style="margin-bottom:4px">${htmlEscape(name)}</h2>
          <p style="color:var(--color-text-muted);margin-bottom:8px">${htmlEscape(email)}</p>
          ${createdAt ? `<p style="color:var(--color-text-muted);font-size:0.85rem">Member since ${new Date(createdAt).toLocaleDateString()}</p>` : ''}
        </div>

        <div class="card-grid">
          <div class="card">
            <div class="card-title">Level</div>
            <div class="card-value">${level}</div>
          </div>
          <div class="card">
            <div class="card-title">Eco Score</div>
            <div class="card-value">${ecoScore}</div>
          </div>
          <div class="card">
            <div class="card-title">Streak</div>
            <div class="card-value">${streak}</div>
          </div>
          <div class="card">
            <div class="card-title">CO&#8322; Saved</div>
            <div class="card-value">${totalSaved.toFixed(1)}</div>
          </div>
        </div>

        ${badges.length > 0 ? `
        <div class="card" style="margin-bottom:24px">
          <div class="card-title" style="margin-bottom:12px">Badges</div>
          <div class="badges-row">
            ${badges.map(b => {
              const name = typeof b === 'string' ? b : (b.name || 'Badge');
              return `<span class="badge-item earned" style="display:inline-flex;padding:6px 12px;min-width:auto">
                <span style="font-size:0.85rem">${htmlEscape(name)}</span>
              </span>`;
            }).join('')}
          </div>
        </div>` : ''}

        <div class="card" style="margin-bottom:24px">
          <div class="card-title" style="margin-bottom:12px">Account</div>
          <p style="font-size:0.9rem;color:var(--color-text-secondary)">
            ${profile.emailVerified !== undefined
              ? `Email verified: ${profile.emailVerified ? '&#10003;' : '&#10007;'}`
              : email ? 'Email confirmed on file' : ''}
          </p>
        </div>
      </div>
    `;
  } catch (err) {
    app.innerHTML = /* safe HTML - error escaped with htmlEscape() */ `
      <div class="error-state">
        <span class="empty-icon">&#9888;</span>
        <p>${htmlEscape(err.message)}</p>
        <button class="btn btn-primary" onclick="window.location.hash='#/profile'">Retry</button>
      </div>
    `;
  }
}

registerRoute('/profile', renderProfile);
