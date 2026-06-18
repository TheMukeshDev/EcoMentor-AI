import { api, toast, registerRoute, htmlEscape } from './main.js';
import { apiGetCached, clearCache } from './api-client.js';
import { getState, subscribe } from './store.js';
import { onBeforeRouteChange } from './router.js';
import { dashboardSkeleton } from './skeletons.js';

let dashboardCharts = {};
let refreshInterval = null;
let profile = {};
let isRendering = false;

function getProfile() {
  return getState('user_profile') || JSON.parse(localStorage.getItem('firebase_user') || '{}');
}

async function renderDashboard() {
  if (isRendering) return;
  isRendering = true;
  
  const app = document.getElementById('app');
  app.innerHTML = dashboardSkeleton();
  profile = getProfile();

  try {
    const [summaryRes, historyRes, insightsRes, trendsRes] = await Promise.all([
      apiGetCached('/dashboard/summary', 15000).catch(() => ({ data: {} })),
      apiGetCached('/dashboard/history?period=last_30', 30000).catch(() => ({ data: [] })),
      apiGetCached('/dashboard/insights', 15000).catch(() => ({ data: {} })),
      apiGetCached('/dashboard/trends', 15000).catch(() => ({ data: {} })),
    ]);

    const summary = summaryRes.data || summaryRes || {};
    const history = (historyRes.data || historyRes || []);
    const insights = insightsRes.data || insightsRes || {};
    const trends = trendsRes.data || trendsRes || {};

    let recs = [];
    try {
      const recRes = await apiGetCached('/ai/recommendations', 60000);
      recs = recRes.data || recRes || [];
    } catch {}

    renderFullDashboard(app, profile, summary, history, insights, trends, recs);
    
    // Only init listeners if they aren't bound, by attaching to body and delegating
    if (!window.__dashboardListenersInit) {
      initRangeButtons();
      initChallenges();
      window.__dashboardListenersInit = true;
    }
    
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(() => clearCache(), 120000);
  } catch (err) {
    app.innerHTML = `
      <div class="error-state">
        <span class="empty-icon">&#9888;</span>
        <p>${htmlEscape(err.message)}</p>
        <button class="btn btn-primary" onclick="window.location.hash='#/dashboard'">Retry</button>
      </div>
    `;
  } finally {
    isRendering = false;
  }
}

function renderFullDashboard(app, profile, summary, history, insights, trends, recs) {
  const name = profile.name || profile.displayName || 'Eco Hero';
  const photo = profile.photoURL || '';
  const level = profile.level || 1;
  const streak = profile.streak || summary.streak || 0;
  const ecoScore = profile.ecoScore || summary.current_score || 50;
  const prevScore = trends.previous_week_avg || ecoScore;
  const direction = trends.direction || 'stable';
  const change = trends.change || 0;
  const badges = profile.badges || ['Eco Beginner'];

  const aiMsg = generateAIMessage(direction, change);

  const co2Saved = summary.totalCarbonSaved || profile.totalCarbonSaved || 0;
  const treesEq = (co2Saved / 21).toFixed(1);
  const waterSaved = (co2Saved * 15).toFixed(0);
  const elecSaved = (co2Saved * 4).toFixed(0);

  const ringDashoffset = 314.159 - (314.159 * ecoScore / 100);
  const ringColor = getScoreColor(ecoScore);

  let lbHtml = '<div class="leaderboard-preview-item" style="justify-content:center;color:var(--color-text-muted)">Leaderboard loading...</div>';
  renderLeaderboardPreview().then(h => { lbHtml = h; const el = document.getElementById('lbPreview'); if (el) el.innerHTML = h; });

  const scorePct = Math.min(100, Math.round((ecoScore / 100) * 100));

  app.innerHTML = `
<div class="dashboard-container">

  <section class="dashboard-hero" role="region" aria-label="Welcome">
    <div class="dashboard-hero-avatar">
      ${photo ? `<img src="${htmlEscape(photo)}" alt="" style="width:100%;height:100%;border-radius:50%;object-fit:cover">` : '&#127807;'}
    </div>
    <div class="dashboard-hero-content">
      <div class="dashboard-hero-greeting">Welcome Back</div>
      <div class="dashboard-hero-name">${htmlEscape(name)}</div>
      <div class="dashboard-hero-stats">
        <span class="dashboard-hero-stat"><span class="dashboard-hero-stat-icon">&#127942;</span> Level ${level}</span>
        <span class="dashboard-hero-stat"><span class="dashboard-hero-stat-icon">&#128293;</span> ${streak} day streak</span>
        <span class="dashboard-hero-stat"><span class="dashboard-hero-stat-icon">&#127919;</span> ${ecoScore} pts</span>
      </div>
      <div class="weekly-progress">
        <div class="weekly-progress-bar">
          <div class="weekly-progress-fill" style="width:${scorePct}%"></div>
        </div>
        <span class="weekly-progress-label">${scorePct}% weekly goal</span>
      </div>
      ${aiMsg ? `<div class="dashboard-hero-message">${htmlEscape(aiMsg)}</div>` : ''}
    </div>
  </section>

  <section class="dashboard-section" role="region" aria-label="Eco Score">
    <div class="eco-score-card">
      <div class="eco-score-ring" role="img" aria-label="Eco Score: ${ecoScore} out of 100">
        <svg viewBox="0 0 120 120" width="120" height="120">
          <circle class="eco-score-ring-bg" cx="60" cy="60" r="50"/>
          <circle class="eco-score-ring-fill" id="scoreRing" cx="60" cy="60" r="50"
            stroke="${ringColor}" stroke-dasharray="314.159" stroke-dashoffset="${ringDashoffset}"/>
        </svg>
        <div class="eco-score-ring-text">
          <span class="eco-score-ring-value">${ecoScore}</span>
          <span class="eco-score-ring-label">Eco Score</span>
        </div>
      </div>
      <div class="eco-score-details">
        <div class="eco-score-previous">Previous: ${prevScore.toFixed(1)}</div>
        <div class="eco-score-trend ${direction}">
          ${direction === 'up' ? '&#8593; Increased' : direction === 'down' ? '&#8595; Decreased' : '&#8596; Stable'}
          ${change > 0 ? ` by ${change}` : ''}
        </div>
        <div class="eco-score-improvement">${getScoreMsg(ecoScore, direction)}</div>
      </div>
    </div>
  </section>

  <section class="dashboard-section" role="region" aria-label="Carbon Footprint Analytics">
    <div class="dashboard-section-header">
      <h2 class="dashboard-section-title"><span class="dashboard-section-icon">&#128200;</span> Carbon Footprint Analytics</h2>
      <div class="chart-range-group" id="chartRangeGroup">
        <button class="chart-range-btn active" data-range="30" aria-pressed="true">30D</button>
        <button class="chart-range-btn" data-range="7" aria-pressed="false">7D</button>
      </div>
    </div>
    <div class="charts-grid">
      <div class="chart-card full-width">
        <div class="chart-card-title">Eco Score Trend</div>
        <div class="chart-card-wrapper tall"><canvas id="trendChart" role="img" aria-label="Eco score trend over time"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-card-title">Category Breakdown</div>
        <div class="chart-card-wrapper"><canvas id="categoryChart" role="img" aria-label="Carbon breakdown by category"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-card-title">Weekly Comparison</div>
        <div class="chart-card-wrapper"><canvas id="comparisonChart" role="img" aria-label="Weekly carbon comparison"></canvas></div>
      </div>
    </div>
  </section>

  <section class="dashboard-section" role="region" aria-label="AI Insights">
    <div class="dashboard-section-header">
      <h2 class="dashboard-section-title"><span class="dashboard-section-icon">&#128161;</span> AI Insights</h2>
    </div>
    <div class="insights-list">${renderInsights(insights, direction, change)}</div>
  </section>

  <section class="dashboard-section" role="region" aria-label="Recommendations">
    <div class="dashboard-section-header">
      <h2 class="dashboard-section-title"><span class="dashboard-section-icon">&#128640;</span> Smart Recommendations</h2>
    </div>
    <div class="recommendations-grid">${renderRecs(recs)}</div>
  </section>

  <section class="dashboard-section" role="region" aria-label="Achievements">
    <div class="dashboard-section-header">
      <h2 class="dashboard-section-title"><span class="dashboard-section-icon">&#127941;</span> Achievements</h2>
      <a href="#/achievements" class="dashboard-section-link">View All</a>
    </div>
    <div class="badges-row">${renderBadges(badges)}</div>
  </section>

  <section class="dashboard-section" role="region" aria-label="Leaderboard">
    <div class="dashboard-section-header">
      <h2 class="dashboard-section-title"><span class="dashboard-section-icon">&#127942;</span> Leaderboard</h2>
      <a href="#/leaderboard" class="dashboard-section-link">Full Rankings</a>
    </div>
    <div class="leaderboard-preview" id="lbPreview">${lbHtml}</div>
  </section>

  <section class="dashboard-section" role="region" aria-label="Challenges">
    <div class="dashboard-section-header">
      <h2 class="dashboard-section-title"><span class="dashboard-section-icon">&#127937;</span> Weekly Challenges</h2>
    </div>
    <div class="challenges-grid" id="challengesGrid">${renderChallengeCards()}</div>
  </section>

  <section class="dashboard-section" role="region" aria-label="AI Eco Mentor">
    <div class="eco-mentor-card">
      <div class="eco-mentor-label">&#129309; AI Eco Mentor</div>
      <div class="eco-mentor-message">
        ${ecoScore > 60
          ? 'Your biggest emission source might be transport. Focus there first for maximum impact.'
          : 'Completing this week\'s challenge could increase your eco score by 6 points. You\'ve got this!'}
      </div>
    </div>
  </section>

  <section class="dashboard-section" role="region" aria-label="Your Impact">
    <div class="dashboard-section-header">
      <h2 class="dashboard-section-title"><span class="dashboard-section-icon">&#127758;</span> Your Impact</h2>
    </div>
    <div class="impact-grid">
      <div class="impact-card">
        <div class="impact-icon">&#127807;</div>
        <div class="impact-value">${co2Saved.toFixed(1)}</div>
        <div class="impact-unit">kg CO&#8322;</div>
        <div class="impact-label">Carbon Saved</div>
      </div>
      <div class="impact-card">
        <div class="impact-icon">&#127794;</div>
        <div class="impact-value">${treesEq}</div>
        <div class="impact-unit">trees</div>
        <div class="impact-label">Trees Equivalent</div>
      </div>
      <div class="impact-card">
        <div class="impact-icon">&#128167;</div>
        <div class="impact-value">${waterSaved}</div>
        <div class="impact-unit">liters</div>
        <div class="impact-label">Water Saved</div>
      </div>
      <div class="impact-card">
        <div class="impact-icon">&#11047;</div>
        <div class="impact-value">${elecSaved}</div>
        <div class="impact-unit">kWh</div>
        <div class="impact-label">Electricity Saved</div>
      </div>
    </div>
  </section>

</div>`;

  renderTrendChart(history);
  renderCategoryChart(history);
  renderComparisonChart(history);
}

function renderInsights(insights, direction, change) {
  const items = [];
  if (insights.ai_insight) items.push({ icon: 'high', text: insights.ai_insight });
  if (insights.ai_tip) items.push({ icon: 'medium', text: insights.ai_tip });
  if (direction === 'down' && change > 0) {
    items.push({ icon: 'low', text: `Your carbon score dropped ${change} points! Keep up the eco-friendly habits.` });
  } else if (direction === 'up' && change > 0) {
    items.push({ icon: 'high', text: `Your score rose by ${change} points. Try our recommendations below to reverse the trend.` });
  } else {
    items.push({ icon: 'low', text: 'You\'re maintaining a stable footprint. Small daily changes lead to big impacts!' });
  }
  while (items.length < 3) items.push({ icon: 'medium', text: 'Log your activities daily for more personalized insights.' });
  return items.slice(0, 3).map(t => `
    <div class="insight-card">
      <div class="insight-icon ${t.icon}">${t.icon === 'high' ? '&#9888;' : t.icon === 'medium' ? '&#128161;' : '&#9989;'}</div>
      <div class="insight-text">${htmlEscape(t.text)}</div>
    </div>
  `).join('');
}

function renderRecs(recs) {
  const list = Array.isArray(recs) && recs.length > 0 ? recs : getDefaultRecs();
  return list.slice(0, 3).map(r => {
    const title = r.title || r.recommendation || r.tip || 'Eco tip';
    const impact = (r.impact || 'Medium').toLowerCase();
    const difficulty = (r.difficulty || 'Easy').toLowerCase();
    const co2 = r.co2 || r.estimated_savings || '';
    const points = r.points || r.reward || 0;
    return `
      <div class="recommendation-card">
        <div class="recommendation-title">${htmlEscape(title)}</div>
        <div class="recommendation-meta">
          <span class="recommendation-tag impact-${impact}">&#9650; ${impact} Impact</span>
          <span class="recommendation-tag difficulty-${difficulty}">${difficulty === 'easy' ? '&#9989;' : difficulty === 'medium' ? '&#9888;' : '&#128170;'} ${difficulty}</span>
        </div>
        ${co2 || points ? `<div class="recommendation-savings">
          ${co2 ? `<span class="recommendation-co2">&#127807; ${htmlEscape(co2)} CO&#8322;</span>` : ''}
          ${points ? `<span class="recommendation-points">&#11088; +${points} pts</span>` : ''}
        </div>` : ''}
      </div>`;
  }).join('');
}

function getDefaultRecs() {
  return [
    { title: 'Use public transport twice this week', impact: 'High', difficulty: 'Easy' },
    { title: 'Switch to LED bulbs', impact: 'Medium', difficulty: 'Easy' },
    { title: 'Reduce food waste by meal planning', impact: 'High', difficulty: 'Medium' },
  ];
}

function renderBadges(earned) {
  const all = [
    { id: 'eco-beginner', name: 'Eco Beginner', icon: '&#127793;' },
    { id: 'green-commuter', name: 'Green Commuter', icon: '&#128690;' },
    { id: 'energy-saver', name: 'Energy Saver', icon: '&#11047;' },
    { id: 'plant-hero', name: 'Plant Hero', icon: '&#127807;' },
    { id: 'climate-champion', name: 'Climate Champion', icon: '&#127758;' },
  ];
  const earnedIds = (earned || []).map(b => typeof b === 'string' ? b.toLowerCase().replace(/\s+/g, '-') : (b.id || ''));
  return all.map(b => `
    <div class="badge-item ${earnedIds.includes(b.id) ? 'earned' : 'locked'}">
      <div class="badge-icon">${b.icon}</div>
      <div class="badge-name">${b.name}</div>
      <div class="badge-status">${earnedIds.includes(b.id) ? '&#10003; Earned' : 'Locked'}</div>
    </div>`).join('');
}

async function renderLeaderboardPreview() {
  try {
    const lbRes = await apiGetCached('/leaderboard/global', 60000).catch(() => ({ data: [] }));
    const entries = lbRes.data || lbRes || [];
    if (!Array.isArray(entries) || entries.length === 0) {
      return '<div class="leaderboard-preview-item" style="justify-content:center;color:var(--color-text-muted)">No rankings yet</div>';
    }
    const myUid = profile.uid || '';
    return entries.slice(0, 5).map((e, i) => {
      const rank = e.rank || i + 1;
      const nm = e.name || e.displayName || `User ${rank}`;
      const sc = e.ecoScore || e.points || e.carbon_score || 0;
      const av = e.photoURL || '';
      const me = e.uid === myUid;
      return `
        <div class="leaderboard-preview-item ${me ? 'current-user' : ''}">
          <div class="leaderboard-rank ${rank <= 3 ? `top-${rank}` : ''}">${rank <= 3 ? ['&#127942;','&#129352;','&#129353;'][rank - 1] : rank}</div>
          <div class="leaderboard-preview-avatar">${av ? `<img src="${htmlEscape(av)}" alt="" style="width:36px;height:36px;border-radius:50%;object-fit:cover">` : '&#128100;'}</div>
          <div class="leaderboard-preview-name">${htmlEscape(nm)}${me ? ' (You)' : ''}</div>
          <div class="leaderboard-preview-score">${sc}</div>
        </div>`;
    }).join('');
  } catch {
    return '<div class="leaderboard-preview-item" style="justify-content:center;color:var(--color-text-muted)">Leaderboard unavailable</div>';
  }
}

function renderChallengeCards() {
  const challenges = [
    { id: 'no-car', title: 'No-Car Weekend', desc: 'Go car-free this weekend. Walk, bike, or use public transport.', reward: 100, difficulty: 'Medium' },
    { id: 'vegetarian', title: 'Vegetarian Day', desc: 'Try a meat-free day. Plant-based meals have a lower carbon footprint.', reward: 75, difficulty: 'Easy' },
    { id: 'reduce-ac', title: 'Reduce AC Usage', desc: 'Keep AC off for 4 hours today. Use a fan instead.', reward: 60, difficulty: 'Medium' },
  ];
  const completed = JSON.parse(sessionStorage.getItem('completed_challenges') || '[]');
  return challenges.map(c => {
    const done = completed.includes(c.id);
    return `
      <div class="challenge-card ${done ? 'completed' : ''}">
        <div class="challenge-title">${htmlEscape(c.title)}</div>
        <div class="challenge-description">${htmlEscape(c.desc)}</div>
        <div class="challenge-meta">
          <span class="challenge-reward">&#11088; +${c.reward} pts</span>
          <span>${c.difficulty}</span>
        </div>
        <button class="challenge-btn ${done ? 'completed' : 'active'}" data-challenge="${c.id}" ${done ? 'disabled' : ''}>
          ${done ? '&#10003; Completed' : 'Complete Challenge'}
        </button>
      </div>`;
  }).join('');
}

function generateAIMessage(direction, change) {
  if (direction === 'down' && change > 0) return `Great progress! Your emissions dropped ${change}% this week. Keep it up!`;
  if (direction === 'up' && change > 0) return `Your emissions rose ${change}% this week. Check your recommendations for ways to improve.`;
  return 'You\'re maintaining steady eco-habits. Small changes lead to big impacts over time!';
}

function getScoreColor(score) {
  if (score >= 80) return '#059669';
  if (score >= 60) return '#2d6a4f';
  if (score >= 40) return '#d97706';
  return '#dc2626';
}

function getScoreMsg(score) {
  if (score >= 80) return 'Excellent! You\'re an eco-champion!';
  if (score >= 60) return 'Good progress! Keep building on your habits.';
  if (score >= 40) return 'You\'re on your way. Try some recommendations above.';
  return 'Start with small changes - every bit counts!';
}

function initRangeButtons() {
  document.getElementById('chartRangeGroup')?.addEventListener('click', async (e) => {
    const btn = e.target.closest('.chart-range-btn');
    if (!btn || btn.classList.contains('active')) return;
    document.querySelectorAll('.chart-range-btn').forEach(b => {
      b.classList.remove('active');
      b.setAttribute('aria-pressed', 'false');
    });
    btn.classList.add('active');
    btn.setAttribute('aria-pressed', 'true');
    const days = btn.dataset.range;
    const res = await apiGetCached(`/dashboard/history?period=last_${days}`, 30000).catch(() => ({ data: [] }));
    const history = res.data || res || [];
    renderTrendChart(history);
    renderCategoryChart(history);
    renderComparisonChart(history);
  });
}

function initChallenges() {
  document.getElementById('challengesGrid')?.addEventListener('click', (e) => {
    const btn = e.target.closest('.challenge-btn.active');
    if (!btn) return;
    const id = btn.dataset.challenge;
    const completed = JSON.parse(sessionStorage.getItem('completed_challenges') || '[]');
    if (!completed.includes(id)) {
      completed.push(id);
      sessionStorage.setItem('completed_challenges', JSON.stringify(completed));
      btn.textContent = '\u2713 Completed';
      btn.classList.remove('active');
      btn.classList.add('completed');
      btn.disabled = true;
      btn.closest('.challenge-card')?.classList.add('completed');
      toast('Challenge completed! +Reward points earned.', 'success');
    }
  });
}

function getCSSVar(name, fallback) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

function renderTrendChart(history) {
  const canvas = document.getElementById('trendChart');
  const wrapper = canvas?.parentElement;
  if (!wrapper) return;
  if (dashboardCharts.trend) { dashboardCharts.trend.destroy(); delete dashboardCharts.trend; }
  
  if (!history || history.length === 0) {
    wrapper.innerHTML = `
      <div class="empty-state-small" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;padding:20px;color:var(--color-text-muted)">
        <span style="font-size:2rem;margin-bottom:8px">&#128200;</span>
        <p style="font-size:0.9rem;margin-bottom:12px">No carbon history data logged yet.</p>
        <a href="#/log" class="btn btn-primary" style="padding:6px 12px;font-size:0.8rem">Log Activity</a>
      </div>
    `;
    return;
  }

  if (!document.getElementById('trendChart')) {
    wrapper.innerHTML = '<canvas id="trendChart" role="img" aria-label="Eco score trend over time"></canvas>';
  }
  const activeCanvas = document.getElementById('trendChart');
  const labels = history.map(e => (e.date || '').slice(5));
  const scores = history.map(e => e.carbon_score || 0);
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const primary = getCSSVar('--color-primary', '#2d6a4f');
  const muted = getCSSVar('--color-text-muted', '#718096');
  import('chart.js').then(({ default: Chart }) => {
    dashboardCharts.trend = new Chart(activeCanvas.getContext('2d'), {
      type: 'line',
      data: { labels, datasets: [{ label: 'Eco Score', data: scores, borderColor: primary, backgroundColor: isDark ? 'rgba(82,183,136,0.15)' : 'rgba(45,106,79,0.1)', fill: true, tension: 0.4, pointRadius: 3, pointHoverRadius: 5 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }, ticks: { color: muted } }, x: { grid: { display: false }, ticks: { color: muted } } } },
    });
  });
}

function renderCategoryChart(history) {
  const canvas = document.getElementById('categoryChart');
  const wrapper = canvas?.parentElement;
  if (!wrapper) return;
  if (dashboardCharts.category) { dashboardCharts.category.destroy(); delete dashboardCharts.category; }

  if (!history || history.length === 0) {
    wrapper.innerHTML = `
      <div class="empty-state-small" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;padding:20px;color:var(--color-text-muted)">
        <span style="font-size:2rem;margin-bottom:8px">&#128173;</span>
        <p style="font-size:0.9rem;margin-bottom:12px">No categories tracked yet.</p>
        <a href="#/log" class="btn btn-primary" style="padding:6px 12px;font-size:0.8rem">Log Activity</a>
      </div>
    `;
    return;
  }

  if (!document.getElementById('categoryChart')) {
    wrapper.innerHTML = '<canvas id="categoryChart" role="img" aria-label="Carbon breakdown by category"></canvas>';
  }
  const activeCanvas = document.getElementById('categoryChart');
  const categories = ['Transport', 'Food', 'Electricity', 'Lifestyle'];
  const colors = ['#2d6a4f', '#d97706', '#2563eb', '#7c3aed'];
  const data = categories.map(cat => {
    const vals = history.map(e => e[cat.toLowerCase()] || 0);
    return vals.length ? (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : 0;
  });
  const muted = getCSSVar('--color-text-muted', '#718096');
  import('chart.js').then(({ default: Chart }) => {
    dashboardCharts.category = new Chart(activeCanvas.getContext('2d'), {
      type: 'doughnut',
      data: { labels: categories, datasets: [{ data, backgroundColor: colors.map(c => c + 'CC'), borderColor: colors, borderWidth: 2 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: muted, font: { size: 11 }, padding: 12 } } }, cutout: '65%' },
    });
  });
}

function renderComparisonChart(history) {
  const canvas = document.getElementById('comparisonChart');
  const wrapper = canvas?.parentElement;
  if (!wrapper) return;
  if (dashboardCharts.comparison) { dashboardCharts.comparison.destroy(); delete dashboardCharts.comparison; }

  if (!history || history.length === 0) {
    wrapper.innerHTML = `
      <div class="empty-state-small" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;padding:20px;color:var(--color-text-muted)">
        <span style="font-size:2rem;margin-bottom:8px">&#128202;</span>
        <p style="font-size:0.9rem;margin-bottom:12px">No comparison data available.</p>
        <a href="#/log" class="btn btn-primary" style="padding:6px 12px;font-size:0.8rem">Log Activity</a>
      </div>
    `;
    return;
  }

  if (!document.getElementById('comparisonChart')) {
    wrapper.innerHTML = '<canvas id="comparisonChart" role="img" aria-label="Weekly carbon comparison"></canvas>';
  }
  const activeCanvas = document.getElementById('comparisonChart');
  const labels = history.map(e => (e.date || '').slice(5));
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const muted = getCSSVar('--color-text-muted', '#718096');
  import('chart.js').then(({ default: Chart }) => {
    dashboardCharts.comparison = new Chart(activeCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Transport', data: history.map(e => e.transport || 0), backgroundColor: '#2d6a4fAA', borderRadius: 4 },
          { label: 'Food', data: history.map(e => e.food || 0), backgroundColor: '#d97706AA', borderRadius: 4 },
          { label: 'Electricity', data: history.map(e => e.electricity || 0), backgroundColor: '#2563ebAA', borderRadius: 4 },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { color: muted, font: { size: 10 }, boxWidth: 12, padding: 8 } } },
        scales: { x: { stacked: true, grid: { display: false }, ticks: { color: muted } }, y: { stacked: true, beginAtZero: true, grid: { color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }, ticks: { color: muted } } },
      },
    });
  });
}

let _unsubProfile;

onBeforeRouteChange(() => {
  if (_unsubProfile) { _unsubProfile(); _unsubProfile = null; }
});

_unsubProfile = subscribe('user_profile', () => {
  const hash = window.location.hash;
  if (!hash || hash === '#/' || hash === '#/dashboard') renderDashboard();
});

registerRoute('/dashboard', renderDashboard);
