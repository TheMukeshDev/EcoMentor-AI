import { api, registerRoute, htmlEscape } from './main.js';

async function renderCoach() {
  const app = document.getElementById('app');
  app.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading coach...</span></div>';

  try {
    const missionRes = await api('/ai/daily-mission').catch(() => ({ data: null }));
    const mission = missionRes.data;

    app.innerHTML = `
      <div style="max-width:600px;margin:0 auto">
        <h1 style="margin-bottom:8px">AI Coach</h1>
        <p style="color:var(--color-text-secondary);margin-bottom:24px">Personalized tips and daily missions</p>

        ${mission ? `
          <div class="card" style="margin-bottom:24px">
            <div class="card-title">Today's Mission</div>
            <p style="margin:12px 0;font-size:1.1rem;line-height:1.5">${htmlEscape(mission.challenge)}</p>
            <span class="mission-reward">+${mission.reward || 0} pts</span>
          </div>
        ` : `
          <div class="empty-state">
            <span class="empty-icon">&#x1F9D1;&#x200D;&#x1F3EB;</span>
            <p>No missions available yet. Keep logging activities!</p>
          </div>
        `}

        <div class="card" style="margin-bottom:16px">
          <div class="card-title">Eco Tip</div>
          <p style="margin-top:8px;color:var(--color-text-secondary)">Switching to LED bulbs can reduce your electricity carbon footprint by up to 75%. Every small change adds up!</p>
        </div>

        <div class="card" style="margin-bottom:16px">
          <div class="card-title">Quick Challenge</div>
          <p style="margin-top:8px;color:var(--color-text-secondary)">Try a meat-free Monday to save approximately 8.5 kg CO&#8322; per week. That's 442 kg CO&#8322; saved per year!</p>
        </div>
      </div>
    `;
  } catch (err) {
    app.innerHTML = `
      <div class="error-state">
        <span class="empty-icon">&#9888;</span>
        <p>${htmlEscape(err.message)}</p>
        <button class="btn btn-primary" onclick="window.location.hash='#/coach'">Retry</button>
      </div>
    `;
  }
}

registerRoute('/coach', renderCoach);
