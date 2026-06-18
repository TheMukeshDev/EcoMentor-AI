import { api, registerRoute, htmlEscape } from './main.js';

const FEATURES = [
  { icon: '\uD83D\uDCC8', title: 'Track Footprint', desc: 'Log daily activities and see your carbon impact in real time.' },
  { icon: '\uD83E\uDD16', title: 'Smart Coach', desc: 'Personalized AI tips to help you reduce emissions.' },
  { icon: '\uD83C\uDFC6', title: 'Gamification', desc: 'Earn points, unlock badges, and compete on the leaderboard.' },
  { icon: '\uD83D\uDEE1\uFE0F', title: 'Challenges', desc: 'Daily missions to build sustainable habits.' },
  { icon: '\uD83D\uDCCA', title: 'AI Reports', desc: 'Weekly insights with AI-powered recommendations.' },
  { icon: '\uD83C\uDF0D', title: 'Community', desc: 'Compare progress and inspire others.' },
];

const STEPS = [
  { title: 'Log Activity', desc: 'Tell us about your travel, energy, food, and waste.' },
  { title: 'Get Score', desc: 'See your carbon footprint calculated instantly.' },
  { title: 'Track Progress', desc: 'Monitor your trends over days and weeks.' },
  { title: 'Level Up', desc: 'Unlock badges and climb the leaderboard.' },
];

async function renderHome() {
  const app = document.getElementById('app');

  let lbHtml = '';
  try {
    const res = await api('/leaderboard/global');
    const entries = (res.data || []).slice(0, 3);
    if (entries.length > 0) {
      const MEDALS = ['\uD83E\uDD47', '\uD83E\uDD48', '\uD83E\uDD49'];
      lbHtml = `
        <div class="section">
          <h2 class="section-title">Top Eco Leaders</h2>
          <div class="leaderboard-preview">
            ${entries.map((e, i) => `
              <div class="lb-row">
                <span class="lb-rank ${i < 3 ? `top-${i + 1}` : ''}">${MEDALS[i] || (i + 1)}</span>
                <span style="flex:1;font-weight:600">${htmlEscape(e.name) || 'Anonymous'}</span>
                <span class="lb-level" style="background:var(--color-primary-bg);color:var(--color-primary);padding:2px 10px;border-radius:12px;font-size:0.8rem">${htmlEscape(e.level) || 'Beginner'}</span>
                <span style="font-weight:700">${e.points || 0} pts</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }
  } catch (_) { }

  app.innerHTML = `
    <section class="hero">
      <h1>Your Personal <span>Eco Coach</span></h1>
      <p>Track, understand, and reduce your carbon footprint with AI-powered insights. Join the community making a difference.</p>
      <a href="#/signup" class="btn btn-primary">Get Started Free</a>
    </section>

    <section class="section">
      <h2 class="section-title">Why EcoMentor?</h2>
      <div class="features-grid">
        ${FEATURES.map(f => `
          <div class="feature-card">
            <span class="feature-icon" aria-hidden="true">${f.icon}</span>
            <h3>${f.title}</h3>
            <p>${f.desc}</p>
          </div>
        `).join('')}
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">How It Works</h2>
      <div class="steps">
        ${STEPS.map(s => `
          <div class="step">
            <h3>${s.title}</h3>
            <p>${s.desc}</p>
          </div>
        `).join('')}
      </div>
    </section>

    ${lbHtml}

    <section class="cta-section">
      <h2>Ready to Make a Difference?</h2>
      <p>Join thousands of users tracking their carbon footprint.</p>
      <a href="#/signup" class="btn btn-primary">Create Free Account</a>
    </section>
  `;
}

registerRoute('/', renderHome);
