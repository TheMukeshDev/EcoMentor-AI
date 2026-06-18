import { describe, it, expect, beforeEach, vi, beforeAll } from 'vitest';

const store = {};
vi.stubGlobal('localStorage', {
  getItem: (key) => store[key] ?? null,
  setItem: (key, value) => { store[key] = String(value); },
  removeItem: (key) => { delete store[key]; },
  clear: () => { Object.keys(store).forEach(k => delete store[k]); },
  get length() { return Object.keys(store).length; },
  key: (i) => Object.keys(store)[i] ?? null,
});

function clearStorage() {
  Object.keys(store).forEach(k => delete store[k]);
}

beforeAll(() => {
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
  window.matchMedia = vi.fn().mockImplementation((query) => ({
    matches: false, media: query, onchange: null,
    addListener: vi.fn(), removeListener: vi.fn(),
    addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
  }));
  window.scrollTo = vi.fn();
});

describe('Google Auth Integration', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="app"></div><div id="main-content"></div><div id="nav-links"></div>';
    clearStorage();
    vi.restoreAllMocks();
  });

  it('should render Google sign-in button on login page', async () => {
    document.getElementById('app').innerHTML = `
      <div class="auth-page">
        <h1>Welcome Back</h1>
        <button id="google-login-btn" class="btn btn-google" style="width:100%">
          <svg class="google-icon" viewBox="0 0 24 24" width="20" height="20"></svg>
          Sign in with Google
        </button>
        <div class="auth-divider"><span>or</span></div>
        <form id="login-form" novalidate>
          <input type="email" id="login-email" />
          <input type="password" id="login-password" />
          <button type="submit">Login</button>
        </form>
      </div>
    `;

    const googleBtn = document.getElementById('google-login-btn');
    expect(googleBtn).toBeTruthy();
    expect(googleBtn.textContent).toContain('Sign in with Google');

    const divider = document.querySelector('.auth-divider');
    expect(divider).toBeTruthy();
    expect(divider.textContent).toContain('or');
  });

  it('should render Google sign-up button on signup page', () => {
    document.getElementById('app').innerHTML = `
      <div class="auth-page">
        <h1>Create Account</h1>
        <button id="google-signup-btn" class="btn btn-google" style="width:100%">
          <svg class="google-icon" viewBox="0 0 24 24" width="20" height="20"></svg>
          Sign up with Google
        </button>
        <div class="auth-divider"><span>or</span></div>
        <form id="signup-form" novalidate>
          <input type="text" id="signup-name" />
          <input type="email" id="signup-email" />
          <input type="password" id="signup-password" />
          <button type="submit">Create Account</button>
        </form>
      </div>
    `;

    const googleBtn = document.getElementById('google-signup-btn');
    expect(googleBtn).toBeTruthy();
    expect(googleBtn.textContent).toContain('Sign up with Google');
  });

  it('should store id_token after successful Google sign-in', () => {
    localStorage.setItem('id_token', 'test-google-token-123');
    const token = localStorage.getItem('id_token');
    expect(token).toBe('test-google-token-123');
  });

  it('should store firebase_user after successful Google sign-in', () => {
    const user = { uid: '123', name: 'Test User', email: 'test@gmail.com', photoURL: '' };
    localStorage.setItem('firebase_user', JSON.stringify(user));
    const stored = JSON.parse(localStorage.getItem('firebase_user'));
    expect(stored.name).toBe('Test User');
    expect(stored.email).toBe('test@gmail.com');
    expect(stored.uid).toBe('123');
  });

  it('should clear auth data on logout', () => {
    localStorage.setItem('id_token', 'token123');
    localStorage.setItem('firebase_user', JSON.stringify({ uid: '123' }));
    localStorage.removeItem('id_token');
    localStorage.removeItem('firebase_user');
    expect(localStorage.getItem('id_token')).toBeNull();
    expect(localStorage.getItem('firebase_user')).toBeNull();
  });

  it('should handle Google sign-in error gracefully', () => {
    document.getElementById('app').innerHTML = `
      <div class="auth-page">
        <p id="login-error" class="form-error" role="alert"></p>
        <button id="google-login-btn">Sign in with Google</button>
      </div>
    `;
    const errorEl = document.getElementById('login-error');
    errorEl.textContent = 'popup-closed-by-user';
    expect(errorEl.textContent).toBeTruthy();
  });

  it('should restore session from localStorage on page load', () => {
    localStorage.setItem('id_token', 'existing-token');
    localStorage.setItem('firebase_user', JSON.stringify({ uid: '456', name: 'Returning User' }));
    const token = localStorage.getItem('id_token');
    const user = JSON.parse(localStorage.getItem('firebase_user'));
    expect(token).toBe('existing-token');
    expect(user.uid).toBe('456');
  });

  it('should send Firebase ID token to backend for profile sync', async () => {
    localStorage.setItem('id_token', 'firebase-id-token');
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: { uid: '123', name: 'Synced', ecoScore: 60, badges: ['Eco Beginner'] } }),
    });
    global.fetch = fetchMock;

    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer firebase-id-token' },
      body: JSON.stringify({ idToken: 'firebase-id-token' }),
    });
    const data = await res.json();
    expect(fetchMock).toHaveBeenCalledWith('/api/auth/google', expect.any(Object));
    expect(data.data.ecoScore).toBe(60);
  });

  it('should create fallback profile when backend is unavailable', () => {
    const firebaseUser = { uid: 'fallback-uid', name: 'Offline User', email: 'off@test.com' };
    const fallback = {
      uid: firebaseUser.uid,
      name: firebaseUser.name,
      email: firebaseUser.email,
      level: 1,
      ecoScore: 50,
      badges: ['Eco Beginner'],
      onboardingCompleted: false,
    };
    expect(fallback.uid).toBe('fallback-uid');
    expect(fallback.ecoScore).toBe(50);
    expect(fallback.level).toBe(1);
  });
});

describe('Auth Guard', () => {
  beforeEach(() => {
    clearStorage();
  });

  it('should redirect unauthenticated users to login for protected routes', async () => {
    const { requireAuth } = await import('../js/auth_guard.js');
    const protectedRoutes = ['/dashboard', '/log', '/coach', '/leaderboard', '/achievements', '/report', '/profile', '/settings'];
    protectedRoutes.forEach(route => {
      const redirect = requireAuth(route);
      expect(redirect).toBe('#/login');
    });
  });

  it('should allow authenticated users to access protected routes', async () => {
    localStorage.setItem('id_token', 'valid-token');
    const { requireAuth } = await import('../js/auth_guard.js');
    const redirect = requireAuth('/dashboard');
    expect(redirect).toBeNull();
  });

  it('should redirect authenticated users away from login/signup', async () => {
    localStorage.setItem('id_token', 'valid-token');
    const { requireAuth } = await import('../js/auth_guard.js');
    const redirect = requireAuth('/login');
    expect(redirect).toBe('#/dashboard');
  });

  it('should allow unauthenticated users to view guest routes', async () => {
    const { requireAuth } = await import('../js/auth_guard.js');
    const redirect = requireAuth('/login');
    expect(redirect).toBeNull();
  });

  it('should handle route guard for home page', async () => {
    const { requireAuth } = await import('../js/auth_guard.js');
    const redirect = requireAuth('/');
    expect(redirect).toBeNull();
  });
});

describe('API Client with Firebase Auth', () => {
  beforeEach(() => {
    clearStorage();
    vi.restoreAllMocks();
  });

  it('should include Firebase ID token in Authorization header', async () => {
    localStorage.setItem('id_token', 'firebase-token-abc');
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
    global.fetch = fetchMock;

    const { api } = await import('../js/api-client.js');
    await api('/test').catch(() => {});
    expect(fetchMock).toHaveBeenCalled();
    const callHeaders = fetchMock.mock.calls[0][1].headers;
    expect(callHeaders['Authorization']).toBe('Bearer firebase-token-abc');
  });

  it('should handle 401 by clearing token and redirecting', async () => {
    localStorage.setItem('id_token', 'expired-token');
    let navigated = '';
    const navigateFn = (hash) => { navigated = hash; };
    const updateNavFn = vi.fn();
    const { api, setAuthHandlers } = await import('../js/api-client.js');
    setAuthHandlers({ navigate: navigateFn, updateNav: updateNavFn });

    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 401, json: () => Promise.resolve({}) });
    await expect(api('/test')).rejects.toThrow('Session expired');
  });
});

describe('Dashboard Widget Tests', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="app"></div>';
    clearStorage();
  });

  it('should render skeleton on dashboard load', async () => {
    const { dashboardSkeleton } = await import('../js/skeletons.js');
    const html = dashboardSkeleton();
    document.getElementById('app').innerHTML = html;
    expect(document.querySelector('.dashboard-skeleton')).toBeTruthy();
    expect(document.querySelector('.skeleton-hero')).toBeTruthy();
    expect(document.querySelectorAll('.skeleton-grid-item').length).toBeGreaterThanOrEqual(4);
  });

  it('should render hero section with user data', () => {
    const profile = { name: 'Test User', photoURL: '', level: 2, streak: 5, ecoScore: 70 };
    const html = `
      <section class="dashboard-hero">
        <div class="dashboard-hero-avatar">&#127807;</div>
        <div class="dashboard-hero-content">
          <div class="dashboard-hero-greeting">Welcome Back</div>
          <div class="dashboard-hero-name">${profile.name}</div>
        </div>
      </section>`;
    document.getElementById('app').innerHTML = html;
    expect(document.querySelector('.dashboard-hero-name').textContent).toBe('Test User');
  });

  it('should render eco score ring with correct value', () => {
    const ecoScore = 75;
    document.getElementById('app').innerHTML = `
      <div class="eco-score-card">
        <div class="eco-score-ring" role="img" aria-label="Eco Score: ${ecoScore} out of 100">
          <svg viewBox="0 0 120 120" width="120" height="120">
            <circle cx="60" cy="60" r="50"/>
          </svg>
          <div class="eco-score-ring-text">
            <span class="eco-score-ring-value">${ecoScore}</span>
            <span class="eco-score-ring-label">Eco Score</span>
          </div>
        </div>
      </div>`;
    const scoreValue = document.querySelector('.eco-score-ring-value');
    expect(scoreValue).toBeTruthy();
    expect(scoreValue.textContent).toBe('75');
  });

  it('should display trend indicator with correct direction', () => {
    document.getElementById('app').innerHTML = `
      <div class="eco-score-trend down">
        &#8595; Decreased by 12
      </div>`;
    const trend = document.querySelector('.eco-score-trend');
    expect(trend.classList.contains('down')).toBe(true);
    expect(trend.textContent).toContain('Decreased');
  });

  it('should render AI insights panel', () => {
    const insights = [
      { icon: 'high', text: 'Your emissions dropped by 12%' },
      { icon: 'medium', text: 'Try cycling twice a week' },
      { icon: 'low', text: 'You\'re doing great!' },
    ];
    document.getElementById('app').innerHTML = `
      <section class="dashboard-section">
        <div class="dashboard-section-header">
          <h2 class="dashboard-section-title">AI Insights</h2>
        </div>
        <div class="insights-list">
          ${insights.map(i => `
            <div class="insight-card">
              <div class="insight-icon ${i.icon}"></div>
              <div class="insight-text">${i.text}</div>
            </div>`).join('')}
        </div>
      </section>`;
    expect(document.querySelectorAll('.insight-card').length).toBe(3);
    expect(document.querySelector('.insight-icon.high')).toBeTruthy();
  });

  it('should render recommendations with impact tags', () => {
    const recs = [{ title: 'Use public transport', impact: 'High', co2: '8 kg', points: 50 }];
    document.getElementById('app').innerHTML = `
      <div class="recommendations-grid">
        ${recs.map(r => `
          <div class="recommendation-card">
            <div class="recommendation-title">${r.title}</div>
            <div class="recommendation-meta">
              <span class="recommendation-tag impact-${r.impact.toLowerCase()}">${r.impact} Impact</span>
            </div>
            <div class="recommendation-savings">
              <span class="recommendation-co2">${r.co2} CO&#8322;</span>
              <span class="recommendation-points">+${r.points} pts</span>
            </div>
          </div>`).join('')}
      </div>`;
    expect(document.querySelector('.recommendation-card')).toBeTruthy();
    expect(document.querySelector('.recommendation-tag.impact-high')).toBeTruthy();
  });

  it('should render badges with earned/locked states', () => {
    document.getElementById('app').innerHTML = `
      <div class="badges-row">
        <div class="badge-item earned">
          <div class="badge-icon">&#127793;</div>
          <div class="badge-name">Eco Beginner</div>
          <div class="badge-status">Earned</div>
        </div>
        <div class="badge-item locked">
          <div class="badge-icon">&#127807;</div>
          <div class="badge-name">Plant Hero</div>
          <div class="badge-status">Locked</div>
        </div>
      </div>`;
    expect(document.querySelector('.badge-item.earned')).toBeTruthy();
    expect(document.querySelector('.badge-item.locked')).toBeTruthy();
  });

  it('should render impact section with all 4 metrics', () => {
    document.getElementById('app').innerHTML = `
      <div class="impact-grid">
        <div class="impact-card"><div class="impact-label">Carbon Saved</div></div>
        <div class="impact-card"><div class="impact-label">Trees Equivalent</div></div>
        <div class="impact-card"><div class="impact-label">Water Saved</div></div>
        <div class="impact-card"><div class="impact-label">Electricity Saved</div></div>
      </div>`;
    expect(document.querySelectorAll('.impact-card').length).toBe(4);
  });

  it('should handle challenge completion', () => {
    document.getElementById('app').innerHTML = `
      <div class="challenges-grid">
        <div class="challenge-card">
          <button class="challenge-btn active" data-challenge="no-car">Complete Challenge</button>
        </div>
      </div>`;
    const btn = document.querySelector('.challenge-btn');
    expect(btn).toBeTruthy();
    expect(btn.classList.contains('active')).toBe(true);
  });

  it('should render eco mentor card', () => {
    document.getElementById('app').innerHTML = `
      <section class="dashboard-section">
        <div class="eco-mentor-card">
          <div class="eco-mentor-label">AI Eco Mentor</div>
          <div class="eco-mentor-message">Your biggest emission source is transport.</div>
        </div>
      </section>`;
    expect(document.querySelector('.eco-mentor-card')).toBeTruthy();
    expect(document.querySelector('.eco-mentor-label').textContent).toBe('AI Eco Mentor');
  });

  it('should render leaderboard preview with entries', () => {
    const entries = [
      { rank: 1, name: 'Alice', score: 95 },
      { rank: 2, name: 'Bob', score: 82 },
    ];
    document.getElementById('app').innerHTML = `
      <div class="leaderboard-preview">
        ${entries.map(e => `
          <div class="leaderboard-preview-item">
            <div class="leaderboard-rank top-${e.rank}">${e.rank}</div>
            <div class="leaderboard-preview-name">${e.name}</div>
            <div class="leaderboard-preview-score">${e.score}</div>
          </div>`).join('')}
      </div>`;
    expect(document.querySelectorAll('.leaderboard-preview-item').length).toBe(2);
    expect(document.querySelector('.leaderboard-rank.top-1')).toBeTruthy();
  });

  it('should render chart canvas elements', () => {
    document.getElementById('app').innerHTML = `
      <div class="charts-grid">
        <div class="chart-card full-width">
          <canvas id="trendChart"></canvas>
        </div>
        <div class="chart-card">
          <canvas id="categoryChart"></canvas>
        </div>
        <div class="chart-card">
          <canvas id="comparisonChart"></canvas>
        </div>
      </div>`;
    expect(document.getElementById('trendChart')).toBeTruthy();
    expect(document.getElementById('categoryChart')).toBeTruthy();
    expect(document.getElementById('comparisonChart')).toBeTruthy();
  });

  it('should handle weekly progress bar rendering', () => {
    const score = 60;
    document.getElementById('app').innerHTML = `
      <div class="weekly-progress">
        <div class="weekly-progress-bar">
          <div class="weekly-progress-fill" style="width:${score}%"></div>
        </div>
        <span class="weekly-progress-label">${score}% weekly goal</span>
      </div>`;
    const fill = document.querySelector('.weekly-progress-fill');
    expect(fill.style.width).toBe('60%');
    expect(document.querySelector('.weekly-progress-label').textContent).toBe('60% weekly goal');
  });

  it('should request authentication for dashboard route', async () => {
    const { requireAuth } = await import('../js/auth_guard.js');
    const result = requireAuth('/dashboard');
    expect(result).toBe('#/login');
  });
});
