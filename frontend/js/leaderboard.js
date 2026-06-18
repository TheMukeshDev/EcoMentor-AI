import { api, registerRoute, htmlEscape } from './main.js';
import { leaderboardSkeleton } from './skeletons.js';

async function renderLeaderboard() {
  const app = document.getElementById('app');
  app.innerHTML = leaderboardSkeleton();

  try {
    const res = await api('/leaderboard/global').catch(() => ({ data: [] }));
    const entries = res.data || [];

    const LEVEL_COLORS = {
      'Beginner': '#94a3b8',
      'Explorer': '#52b788',
      'Eco Warrior': '#2d6a4f',
      'Planet Hero': '#fbbf24',
    };

    app.innerHTML = `
      <div class="leaderboard-page">
        <h1>Leaderboard</h1>
        ${entries.length === 0 ? `
          <div class="empty-state">
            <span class="empty-icon">&#127942;</span>
            <p>No entries yet. Be the first!</p>
          </div>
        ` : `
          <div style="overflow-x:auto">
            <table class="lb-table" role="table">
              <caption style="caption-side:bottom;padding:8px;font-size:0.8rem;color:var(--color-text-muted)">Top ${entries.length} users ranked by points</caption>
              <thead>
                <tr>
                  <th scope="col" class="lb-rank-col">#</th>
                  <th scope="col">Name</th>
                  <th scope="col">Level</th>
                  <th scope="col">Points</th>
                </tr>
              </thead>
              <tbody>
                ${entries.map((e, i) => `
                  <tr>
                    <td class="lb-rank-col"><span class="lb-rank ${i < 3 ? `top-${i + 1}` : ''}">${i + 1}</span></td>
                    <td><strong>${htmlEscape(e.name || e.uid?.slice(0, 8)) || 'Anonymous'}</strong></td>
                    <td><span class="lb-level" style="background:${LEVEL_COLORS[e.level] || '#94a3b8'}20;color:${LEVEL_COLORS[e.level] || '#94a3b8'}">${htmlEscape(e.level) || 'Beginner'}</span></td>
                    <td><strong>${e.points || 0}</strong></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `}
      </div>
    `;
  } catch (err) {
    app.innerHTML = `
      <div class="error-state">
        <span class="empty-icon">&#9888;</span>
        <p>${htmlEscape(err.message)}</p>
        <button class="btn btn-primary" onclick="window.location.hash='#/leaderboard'">Retry</button>
      </div>
    `;
  }
}

registerRoute('/leaderboard', renderLeaderboard);
