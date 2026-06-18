import { api, toast, registerRoute, htmlEscape } from './main.js';
import { dashboardSkeleton } from './skeletons.js';

async function renderDashboard() {
  const app = document.getElementById('app');
  app.innerHTML = dashboardSkeleton();

  try {
    const [summaryRes, trendsRes, missionRes, personalityRes] = await Promise.all([
      api('/dashboard/summary').catch(() => ({ data: {} })),
      api('/dashboard/history?period=last_30').catch(() => ({ data: [] })),
      api('/ai/daily-mission').catch(() => ({ data: null })),
      api('/ai/eco-personality').catch(() => ({ data: null })),
    ]);

    const summary = summaryRes.data || {};
    const history = trendsRes.data || [];
    const mission = missionRes.data;
    const personality = personalityRes.data;

    app.innerHTML = `
      <div class="dashboard-header">
        <h1>Dashboard</h1>
        ${personality ? `<span class="personality-badge">${htmlEscape(personality.personality) || 'Eco Guardian'}</span>` : ''}
      </div>

      <div class="card-grid">
        <div class="card">
          <div class="card-title">Carbon Score</div>
          <div class="card-value">${summary.current_score?.toFixed(1) || '0'}</div>
          <div style="color:var(--color-text-muted);font-size:0.85rem">today</div>
        </div>
        <div class="card">
          <div class="card-title">Weekly Average</div>
          <div class="card-value">${summary.weekly_average?.toFixed(1) || '0'}</div>
          <div style="color:var(--color-text-muted);font-size:0.85rem">past 7 days</div>
        </div>
        <div class="card">
          <div class="card-title">Streak</div>
          <div class="card-value">${summary.streak || 0}</div>
          <div style="color:var(--color-text-muted);font-size:0.85rem">consecutive days</div>
        </div>
        <div class="card">
          <div class="card-title">Activities</div>
          <div class="card-value">${summary.activities_logged || 0}</div>
          <div style="color:var(--color-text-muted);font-size:0.85rem">total logged</div>
        </div>
      </div>

      ${mission ? `
        <div class="mission-card">
          <div class="mission-text">
            <h3>Today's Mission</h3>
            <p>${htmlEscape(mission.challenge) || ''}</p>
          </div>
          <span class="mission-reward">+${mission.reward || 0} pts</span>
        </div>
      ` : ''}

      <div class="chart-container">
        <h3>Carbon Trend</h3>
        <div class="chart-wrapper">
          <canvas id="carbonChart"></canvas>
        </div>
        <div style="display:flex;gap:8px;margin-top:12px">
          <button class="btn btn-secondary chart-range active" data-range="7">7 Days</button>
          <button class="btn btn-secondary chart-range" data-range="30">30 Days</button>
        </div>
      </div>

      <div class="section">
        <h2 class="section-title" style="text-align:left;margin-bottom:16px">Eco Insights</h2>
        <div class="card-grid">
          <div class="card">
            <div class="card-title">Strengths</div>
            <p style="color:var(--color-text-secondary);font-size:0.9rem">${htmlEscape(personality?.strength) || 'Start logging to discover your strengths'}</p>
          </div>
          <div class="card">
            <div class="card-title">Focus Area</div>
            <p style="color:var(--color-text-secondary);font-size:0.9rem">${htmlEscape(personality?.weakness) || 'Log more activities for personalized insights'}</p>
          </div>
        </div>
      </div>
    `;

    renderChart(history);

    document.querySelectorAll('.chart-range').forEach(btn => {
      btn.addEventListener('click', async () => {
        document.querySelectorAll('.chart-range').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const days = btn.dataset.range;
        const res = await api(`/dashboard/history?period=last_${days}`).catch(() => ({ data: [] }));
        renderChart(res.data || []);
      });
    });
  } catch (err) {
    app.innerHTML = `
      <div class="error-state">
        <span class="empty-icon">&#9888;</span>
        <p>${htmlEscape(err.message)}</p>
        <button class="btn btn-primary" onclick="window.location.hash='#/dashboard'">Retry</button>
      </div>
    `;
  }
}

function getCSSVar(name, fallback) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

async function renderChart(history) {
  const canvas = document.getElementById('carbonChart');
  if (!canvas) return;

  if (window._carbonChart) {
    if (typeof window._carbonChart.destroy === 'function') window._carbonChart.destroy();
    window._carbonChart = null;
  }

  const labels = history.map(e => {
    const d = e.date || '';
    return d.slice(5);
  });
  const scores = history.map(e => e.carbon_score || 0);
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const primary = getCSSVar('--color-primary', '#2d6a4f');
  const muted = getCSSVar('--color-text-muted', '#718096');

  const { default: Chart } = await import('chart.js');
  const ctx = canvas.getContext('2d');
  window._carbonChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Carbon Score',
        data: scores,
        borderColor: primary,
        backgroundColor: isDark ? 'rgba(82,183,136,0.15)' : 'rgba(45,106,79,0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' },
          ticks: { color: muted },
        },
        x: {
          grid: { display: false },
          ticks: { color: muted },
        },
      },
    },
  });
}

registerRoute('/dashboard', renderDashboard);
