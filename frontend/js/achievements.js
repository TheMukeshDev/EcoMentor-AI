import { api, registerRoute } from './main.js';

const ECO_TREE_LEVELS = [
  { name: 'Seed', icon: '\uD83C\uDF31', minPoints: 0 },
  { name: 'Sapling', icon: '\uD83C\uDF33', minPoints: 100 },
  { name: 'Tree', icon: '\uD83C\uDF32', minPoints: 500 },
  { name: 'Forest Guardian', icon: '\uD83C\uDF33', minPoints: 2000 },
];

const BADGES = [
  { name: 'Seedling', icon: '\uD83C\uDF31', minPoints: 0 },
  { name: 'Sprout', icon: '\uD83C\uDF3F', minPoints: 100 },
  { name: 'Leaf', icon: '\uD83C\uDF42', minPoints: 500 },
  { name: 'Globe', icon: '\uD83C\uDF0D', minPoints: 2000 },
];

async function renderAchievements() {
  const app = document.getElementById('app');
  app.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading achievements...</span></div>';

  try {
    const profileRes = await api('/auth/profile').catch(() => ({ data: {} }));
    const profile = profileRes.data || {};
    const points = profile.points || 0;

    const currentLevel = ECO_TREE_LEVELS.reduce((prev, curr) =>
      points >= curr.minPoints ? curr : prev
    , ECO_TREE_LEVELS[0]);

    const nextLevel = ECO_TREE_LEVELS.find(l => l.minPoints > points);
    const progress = nextLevel
      ? Math.round(((points - currentLevel.minPoints) / (nextLevel.minPoints - currentLevel.minPoints)) * 100)
      : 100;

    app.innerHTML = `
      <div class="achievements-page">
        <h1>Achievements</h1>
        <p>Track your eco journey</p>

        <div class="eco-tree" role="figure" aria-label="Eco tree: ${currentLevel.name}">
          <div class="tree-display">${currentLevel.icon}</div>
          <div class="tree-name">${currentLevel.name}</div>
          <div class="tree-level">${points} points</div>
          <div class="tree-progress">
            <div class="tree-bar" role="progressbar" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100" aria-label="Progress to next level">
              <div class="tree-bar-fill" style="width:${progress}%"></div>
            </div>
            <div class="tree-next">${nextLevel ? `${nextLevel.icon} ${nextLevel.name} — ${nextLevel.minPoints - points} points away` : 'Max level reached!'}</div>
          </div>
        </div>

        <h2 class="section-title" style="text-align:left">Badges</h2>
        <div class="badges-grid">
          ${BADGES.map(b => {
            const unlocked = points >= b.minPoints;
            return `
              <div class="badge-card ${unlocked ? 'unlocked' : 'locked'}" role="img" aria-label="${b.name} badge ${unlocked ? 'unlocked' : 'locked'}">
                <span class="badge-icon">${b.icon}</span>
                <h3>${b.name}</h3>
                <p>${b.minPoints > 0 ? `${b.minPoints} points` : 'Starting badge'}</p>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  } catch (err) {
    app.innerHTML = `
      <div class="error-state">
        <span class="empty-icon">&#9888;</span>
        <p>${err.message}</p>
        <button class="btn btn-primary" onclick="window.location.hash='#/achievements'">Retry</button>
      </div>
    `;
  }
}

registerRoute('/achievements', renderAchievements);
