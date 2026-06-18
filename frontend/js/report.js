import { api, registerRoute, htmlEscape } from './main.js';

async function renderReport() {
  const app = document.getElementById('app');
  app.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading report...</span></div>';

  try {
    const [summaryRes, trendsRes] = await Promise.all([
      api('/dashboard/summary').catch(() => ({ data: {} })),
      api('/dashboard/history?period=last_30').catch(() => ({ data: [] })),
    ]);

    const summary = summaryRes.data || {};
    const history = trendsRes.data || [];
    const avg = history.length > 0
      ? (history.reduce((s, e) => s + (e.carbon_score || 0), 0) / history.length).toFixed(1)
      : 'N/A';

    app.innerHTML = `
      <div style="max-width:600px;margin:0 auto">
        <h1 style="margin-bottom:8px">Weekly Report</h1>
        <p style="color:var(--color-text-secondary);margin-bottom:24px">Your carbon impact summary</p>

        <div class="card-grid">
          <div class="card">
            <div class="card-title">Current Score</div>
            <div class="card-value">${summary.current_score?.toFixed(1) || '0'}</div>
          </div>
          <div class="card">
            <div class="card-title">30-Day Avg</div>
            <div class="card-value">${avg}</div>
          </div>
          <div class="card">
            <div class="card-title">Streak</div>
            <div class="card-value">${summary.streak || 0} days</div>
          </div>
          <div class="card">
            <div class="card-title">Total Activities</div>
            <div class="card-value">${summary.activities_logged || 0}</div>
          </div>
        </div>

        ${history.length === 0 ? `
          <div class="empty-state">
            <span class="empty-icon">&#128202;</span>
            <p>No data yet. Start logging activities to see your report.</p>
          </div>
        ` : ''}
      </div>
    `;
  } catch (err) {
    app.innerHTML = `
      <div class="error-state">
        <span class="empty-icon">&#9888;</span>
        <p>${htmlEscape(err.message)}</p>
        <button class="btn btn-primary" onclick="window.location.hash='#/report'">Retry</button>
      </div>
    `;
  }
}

registerRoute('/report', renderReport);
