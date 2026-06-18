import { api, registerRoute, htmlEscape } from './main.js';
import { getState } from './store.js';

async function renderHome() {
  const app = document.getElementById('app');
  const authenticated = getState('is_authenticated') === true || !!localStorage.getItem('id_token');

  let lbHtml = '';
  try {
    const res = await api('/leaderboard/global');
    const entries = (res.data || []).slice(0, 5);
    if (entries.length > 0) {
      const MEDALS = ['🥇', '🥈', '🥉'];
      lbHtml = `
        <div class="podium-grid" aria-label="Top leaderboard users">
          ${entries.map((e, i) => `
            <div class="podium-item ${i === 0 ? 'podium-gold' : i === 1 ? 'podium-silver' : i === 2 ? 'podium-bronze' : ''}">
              <div class="podium-avatar" aria-hidden="true">${MEDALS[i] || `#${i + 1}`}</div>
              <div class="podium-meta">
                <div class="podium-name">${htmlEscape(e.name) || 'Anonymous'}</div>
                <div class="podium-level">Level ${Math.max(1, Math.floor((e.points || 0) / 1000) + 1)}</div>
                <div class="podium-points"><span class="podium-points-num">${e.points || 0}</span> <span class="podium-points-suf">pts</span></div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }
  } catch (_) { }

  app.innerHTML = `
    <div class="home-premium">
      <!-- HERO (FULL SCREEN) -->
      <section class="hp-hero" aria-label="EcoMentor AI hero">
        <div class="hp-hero-bg" aria-hidden="true">
          <div class="hp-hero-gradient" />
          <div class="hp-floating-leaves" />
          <div class="hp-soft-particles" />
          <div class="hp-eco-elements" />
        </div>

        <div class="hp-hero-inner">
          <div class="hp-hero-left">
            <div class="hp-kicker-wrap">
              <span class="hp-kicker">
                <span class="hp-kicker-dot" aria-hidden="true"></span>
                🌍 Sustainability • 🤖 AI Coaching • 🎯 Challenges • 🏆 Rewards
              </span>
            </div>

            <h1 class="hp-hero-title">
              Reduce Your Carbon Footprint.<br/>
              Earn Rewards.<br/>
              Create Real Impact.
            </h1>

            <p class="hp-hero-subtitle">
              Track your sustainability journey with AI-powered coaching, challenges, rewards,
              and measurable environmental impact.
            </p>

            <div class="hp-hero-ctas">
              <a
                href="${authenticated ? '#/dashboard' : '#/signup'}"
                class="hp-btn hp-btn-primary hp-ripple"
                data-loading="false"
              >
                <span class="hp-btn-emoji" aria-hidden="true">🚀</span>
                Start Your Eco Journey
                <span class="hp-btn-spinner" aria-hidden="true"></span>
              </a>

              <a href="#hp-demo" class="hp-btn hp-btn-secondary hp-ripple">
                <span class="hp-btn-emoji" aria-hidden="true">▶</span>
                Watch Demo
              </a>

              <a href="#hp-features" class="hp-btn hp-btn-tertiary hp-ripple">
                <span class="hp-btn-emoji" aria-hidden="true">🌱</span>
                Explore Features
              </a>
            </div>

            <div class="hp-hero-story" aria-label="Discover to Impact">
              <div class="hp-story-step">Discover</div>
              <div class="hp-story-arrow" aria-hidden="true">→</div>
              <div class="hp-story-step">Understand</div>
              <div class="hp-story-arrow" aria-hidden="true">→</div>
              <div class="hp-story-step">Participate</div>
              <div class="hp-story-arrow" aria-hidden="true">→</div>
              <div class="hp-story-step">Earn</div>
              <div class="hp-story-arrow" aria-hidden="true">→</div>
              <div class="hp-story-step">Compete</div>
              <div class="hp-story-arrow" aria-hidden="true">→</div>
              <div class="hp-story-step">Impact</div>
            </div>
          </div>

          <div class="hp-hero-right" aria-label="Interactive hero illustration">
            <div class="hp-hero-illustration">
              <div class="hp-hero-card hp-hero-card-1" data-tilt>
                <div class="hp-card-title">Carbon Score</div>
                <div class="hp-card-value">
                  <span class="hp-card-value-big">82</span><span class="hp-card-value-unit">/100</span>
                </div>
                <div class="hp-card-sub">Lower is better • trending up</div>
              </div>

              <div class="hp-hero-card hp-hero-card-2" data-tilt>
                <div class="hp-card-title">EcoPoints</div>
                <div class="hp-card-value">
                  <span class="hp-card-value-big">1,240</span><span class="hp-card-value-unit">pts</span>
                </div>
                <div class="hp-card-sub">Earn by habits + missions</div>
              </div>

              <div class="hp-hero-card hp-hero-card-3" data-tilt>
                <div class="hp-card-title">Active Challenges</div>
                <div class="hp-chip-row" role="list">
                  <span class="hp-chip" role="listitem">🚴 Bike to Work</span>
                  <span class="hp-chip" role="listitem">⚡ Save Electricity</span>
                </div>
                <div class="hp-card-sub">2 missions • 5 days left</div>
              </div>

              <div class="hp-hero-card hp-hero-card-4" data-tilt>
                <div class="hp-card-title">Weekly Impact</div>
                <div class="hp-impact-meter" aria-hidden="true">
                  <div class="hp-impact-fill" style="width:72%"></div>
                </div>
                <div class="hp-card-sub">🌳 Trees • ⚡ Energy • ♻ Waste</div>
              </div>

              <div class="hp-hero-glass" aria-hidden="true"></div>
            </div>

            <div class="hp-hero-demo" id="hp-demo" aria-label="AI coach preview">
              <div class="hp-ai-window">
                <div class="hp-ai-top">
                  <span class="hp-ai-badge" aria-hidden="true">🤖 AI Coach</span>
                  <span class="hp-ai-status">Live guidance</span>
                </div>

                <div class="hp-ai-chat">
                  <div class="hp-ai-bubble hp-ai-bubble-user" aria-label="User context">
                    My week's sustainability data
                  </div>
                  <div class="hp-ai-bubble hp-ai-bubble-bot" aria-label="AI coach response">
                    <span class="hp-typed" data-typed>
                      Your transportation emissions increased by 12% this week.
                    </span>
                    <div class="hp-ai-suggestion">Suggestion: Use public transportation twice this week.</div>
                    <div class="hp-ai-savings">Potential savings: <b>18 kg CO₂</b></div>
                    <div class="hp-ai-reward">Reward: <b>+120 EcoPoints</b></div>
                  </div>
                </div>

                <div class="hp-ai-typing" aria-hidden="true">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- HERO IMAGE CAROUSEL -->
      <section class="hp-carousel-wrap" aria-label="Nature story carousel">
        <div class="hp-section-header" style="margin-top:0;">
          <h2 class="hp-section-title">A sustainability story you can see</h2>
          <p class="hp-section-sub">Forest • Cities • Cycling • Planting • Clean Energy • Community</p>
        </div>

        <div class="hp-carousel" data-carousel>
          <div class="hp-carousel-track">
            <div class="hp-carousel-slide is-active" data-slide="0">
              <div class="hp-carousel-img" role="img" aria-label="Forest conservation" style="background-image: url('https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&h=600&fit=crop'); background-size: cover; background-position: center;"></div>
              <div class="hp-carousel-overlay"></div>
              <div class="hp-carousel-caption">🌲 Forest Conservation</div>
            </div>

            <div class="hp-carousel-slide" data-slide="1">
              <div class="hp-carousel-img" role="img" aria-label="Sustainable city" style="background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=1200&h=600&fit=crop'); background-size: cover; background-position: center;"></div>
              <div class="hp-carousel-overlay"></div>
              <div class="hp-carousel-caption">🏙️ Green Cities</div>
            </div>

            <div class="hp-carousel-slide" data-slide="2">
              <div class="hp-carousel-img" role="img" aria-label="Cycling lifestyle" style="background-image: url('https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&h=600&fit=crop'); background-size: cover; background-position: center;"></div>
              <div class="hp-carousel-overlay"></div>
              <div class="hp-carousel-caption">🚴 Active Transportation</div>
            </div>

            <div class="hp-carousel-slide" data-slide="3">
              <div class="hp-carousel-img" role="img" aria-label="Tree plantation" style="background-image: url('https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&h=600&fit=crop&q=80'); background-size: cover; background-position: center;"></div>
              <div class="hp-carousel-overlay"></div>
              <div class="hp-carousel-caption">🌱 Tree Planting</div>
            </div>

            <div class="hp-carousel-slide" data-slide="4">
              <div class="hp-carousel-img" role="img" aria-label="Clean energy" style="background-image: url('https://images.unsplash.com/photo-1509391366360-2e938aa1ef14?w=1200&h=600&fit=crop'); background-size: cover; background-position: center;"></div>
              <div class="hp-carousel-overlay"></div>
              <div class="hp-carousel-caption">⚡ Renewable Energy</div>
            </div>

            <div class="hp-carousel-slide" data-slide="5">
              <div class="hp-carousel-img" role="img" aria-label="Community sustainability events" style="background-image: url('https://images.unsplash.com/photo-1559027615-cd2628902d4a?w=1200&h=600&fit=crop'); background-size: cover; background-position: center;"></div>
              <div class="hp-carousel-overlay"></div>
              <div class="hp-carousel-caption">👥 Community Impact</div>
            </div>
          </div>

          <div class="hp-carousel-controls" aria-hidden="true">
            <button class="hp-carousel-prev" type="button" data-carousel-prev aria-label="Previous slide">‹</button>
            <button class="hp-carousel-next" type="button" data-carousel-next aria-label="Next slide">›</button>
          </div>

          <div class="hp-carousel-dots" role="tablist" aria-label="Carousel slide selector">
            ${Array.from({ length: 6 }).map((_, i) => `
              <button type="button" class="hp-dot ${i === 0 ? 'is-active' : ''}" data-dot="${i}" role="tab" aria-selected="${i === 0 ? 'true' : 'false'}" aria-label="Go to slide ${i + 1}"></button>
            `).join('')}
          </div>
        </div>
      </section>

      <!-- TRUST SECTION (COUNTERS) -->
      <section class="hp-trust" aria-label="Trust metrics">
        <div class="hp-grid-5">
          <div class="hp-counter hp-reveal" data-counter data-target="10000">
            <div class="hp-counter-emoji" aria-hidden="true">🌎</div>
            <div class="hp-counter-num"><span data-counter-value>0</span>+</div>
            <div class="hp-counter-label">Activities Logged</div>
          </div>
          <div class="hp-counter hp-reveal" data-counter data-target="5000">
            <div class="hp-counter-emoji" aria-hidden="true">🏆</div>
            <div class="hp-counter-num"><span data-counter-value>0</span>+</div>
            <div class="hp-counter-label">Challenges Completed</div>
          </div>
          <div class="hp-counter hp-reveal" data-counter data-target="2500">
            <div class="hp-counter-emoji" aria-hidden="true">🎁</div>
            <div class="hp-counter-num"><span data-counter-value>0</span>+</div>
            <div class="hp-counter-label">Rewards Redeemed</div>
          </div>
          <div class="hp-counter hp-reveal" data-counter data-target="2.5" data-suffix=" Tons CO₂ Reduced">
            <div class="hp-counter-emoji" aria-hidden="true">🌱</div>
            <div class="hp-counter-num"><span data-counter-value>0</span></div>
            <div class="hp-counter-label">CO₂ Reduced</div>
          </div>
          <div class="hp-counter hp-reveal" data-counter data-target="14000">
            <div class="hp-counter-emoji" aria-hidden="true">👥</div>
            <div class="hp-counter-num"><span data-counter-value>0</span>+</div>
            <div class="hp-counter-label">Growing Eco Community</div>
          </div>
        </div>
      </section>

      <!-- HOW IT WORKS (PREMIUM TIMELINE) -->
      <section class="hp-story-section" id="hp-features" aria-label="How EcoMentor works">
        <div class="hp-section-header">
          <h2 class="hp-section-title">Discover → Understand → Participate → Earn → Compete → Impact</h2>
          <p class="hp-section-sub">A premium loop that turns daily choices into measurable environmental progress.</p>
        </div>

        <div class="hp-timeline" role="list" aria-label="EcoMentor steps">
          ${[
      { n: 1, icon: '📊', title: 'Track Activities', desc: 'Monitor daily habits and carbon footprint.' },
      { n: 2, icon: '🤖', title: 'AI Analysis', desc: 'Receive personalized sustainability guidance.' },
      { n: 3, icon: '🎯', title: 'Complete Challenges', desc: 'Participate in engaging eco missions.' },
      { n: 4, icon: '🏆', title: 'Earn EcoPoints', desc: 'Gain rewards through positive actions.' },
      { n: 5, icon: '🎁', title: 'Redeem Swag', desc: 'Exchange points for merchandise and rewards.' },
      { n: 6, icon: '🌍', title: 'Create Impact', desc: 'Track measurable environmental improvements.' },
    ].map(s => `
            <div class="hp-timeline-card hp-reveal" role="listitem">
              <div class="hp-timeline-top">
                <span class="hp-timeline-icon" aria-hidden="true">${s.icon}</span>
                <span class="hp-timeline-num">Step ${s.n}</span>
              </div>
              <div class="hp-timeline-title">${s.title}</div>
              <div class="hp-timeline-desc">${s.desc}</div>
              <div class="hp-timeline-glow" aria-hidden="true"></div>
            </div>
          `).join('')}
        </div>
      </section>

      <!-- BENEFITS SECTION (ABOUT) -->
      <section class="hp-benefits" id="hp-about" aria-label="Benefits">
        <div class="hp-section-header">
          <h2 class="hp-section-title">Sustainability, but make it premium</h2>
          <p class="hp-section-sub">Save money, build habits, earn real rewards, and see your impact.</p>
        </div>

        <div class="hp-benefit-grid">
          ${[
      { title: 'Save Money', desc: 'Reduce energy consumption and waste.' },
      { title: 'Build Sustainable Habits', desc: 'Small actions create long-term impact.' },
      { title: 'Earn Real Rewards', desc: 'Redeem EcoPoints for eco-friendly merchandise.' },
      { title: 'Compete With Friends', desc: 'Leaderboards and achievements that motivate.' },
      { title: 'Get AI Coaching', desc: 'Personalized recommendations based on your data.' },
      { title: 'Measure Impact', desc: 'See your contribution to the planet.' },
    ].map(b => `
            <div class="hp-benefit-card hp-reveal">
              <div class="hp-benefit-accent" aria-hidden="true"></div>
              <div class="hp-benefit-title">${b.title}</div>
              <div class="hp-benefit-desc">${b.desc}</div>
            </div>
          `).join('')}
        </div>
      </section>

      <!-- CHALLENGES SECTION -->
      <section class="hp-challenges" id="hp-challenges" aria-label="Active Challenges preview">
        <div class="hp-section-header">
          <h2 class="hp-section-title">Engaging Eco Missions</h2>
          <p class="hp-section-sub">Participate in daily and weekly challenges to boost your EcoScore and build sustainable habits.</p>
        </div>

        <div class="hp-grid-5" style="display:flex; justify-content:center; gap:20px; flex-wrap:wrap; max-width:1200px; margin:0 auto;">
          ${[
            { title: 'No-Car Weekend', emoji: '🚴', points: 100, desc: 'Go car-free this weekend' },
            { title: 'Vegetarian Day', emoji: '🥗', points: 75, desc: 'Try a meat-free day' },
            { title: 'Energy Saver', emoji: '⚡', points: 60, desc: 'Reduce AC usage by 4 hours' }
          ].map(c => `
            <div class="hp-reveal" style="background:var(--color-surface); padding:24px; border-radius:var(--radius-lg); border:1px solid var(--color-border); width:100%; max-width:320px; text-align:center; box-shadow:var(--shadow-sm);">
              <div style="font-size:3rem; margin-bottom:16px;">${c.emoji}</div>
              <h3 style="font-size:1.1rem; font-weight:700; margin-bottom:8px; color:var(--color-text);">${c.title}</h3>
              <p style="font-size:0.9rem; color:var(--color-text-muted); margin-bottom:16px;">${c.desc}</p>
              <div style="font-weight:600; color:var(--color-primary); background:rgba(45,106,79,0.1); padding:6px 12px; border-radius:20px; display:inline-block;">+${c.points} pts</div>
            </div>
          `).join('')}
        </div>
      </section>

      <!-- REWARDS STORE PREVIEW -->
      <section class="hp-rewards" id="hp-rewards" aria-label="Rewards store preview">
        <div class="hp-section-header">
          <h2 class="hp-section-title">Turn EcoPoints Into Real Rewards</h2>
          <p class="hp-section-sub">Exclusive drops, eco-friendly swag, and digital badges—redeem in seconds.</p>
        </div>

        <div class="hp-reward-grid">
          ${[
      { emoji: '🌱', title: 'Tree Plantation Certificate', cost: '2,500', tag: 'Verified impact' },
      { emoji: '🎽', title: 'EcoMentor T-Shirt', cost: '5,000', tag: 'Limited edition' },
      { emoji: '💧', title: 'Sustainable Water Bottle', cost: '3,500', tag: 'Low-waste gear' },
      { emoji: '📒', title: 'Eco Notebook', cost: '1,800', tag: 'For your next mission' },
      { emoji: '⭐', title: 'Premium Membership', cost: '9,000', tag: 'Deeper insights' },
      { emoji: '🎖', title: 'Exclusive Digital Badges', cost: '1,200', tag: 'Collect & flex' },
    ].map(r => `
            <div class="hp-reward-card hp-reveal" data-reward-cost="${r.cost}">
              <div class="hp-reward-shine" aria-hidden="true"></div>
              <div class="hp-reward-emoji" aria-hidden="true">${r.emoji}</div>
              <div class="hp-reward-title">${r.title}</div>
              <div class="hp-reward-tag">${r.tag}</div>
              <div class="hp-reward-cost">
                <span class="hp-reward-cost-label">Cost</span>
                <span class="hp-reward-cost-num">${r.cost}</span>
                <span class="hp-reward-cost-unit">EcoPoints</span>
              </div>
              <button class="hp-btn hp-btn-card hp-btn-primary hp-reward-btn" type="button" data-redeem>
                Redeem
              </button>
            </div>
          `).join('')}
        </div>

        <div class="hp-rewards-cta">
          <a href="#/leaderboard" class="hp-btn hp-btn-secondary hp-ripple">Browse Rewards Store</a>
        </div>
      </section>

      <!-- LEADERBOARD & COMMUNITY SECTION -->
      <section class="hp-leaderboard" id="hp-community" aria-label="Top users leaderboard">
        <div class="hp-section-header">
          <h2 class="hp-section-title">Community & Top Eco Warriors</h2>
          <p class="hp-section-sub">Join the global community competing for sustainability leadership.</p>
        </div>

        <div class="hp-leaderboard-content">
          ${lbHtml || '<p class="hp-loading-text">Loading leaderboard...</p>'}
        </div>

        <div class="hp-leaderboard-cta">
          <a href="#/leaderboard" class="hp-btn hp-btn-secondary hp-ripple">View Full Leaderboard</a>
        </div>
      </section>

      <!-- FINAL CTA -->
      <section class="hp-final-cta" aria-label="Final call to action">
        <div class="hp-final-cta-inner">
          <h2 class="hp-final-cta-title">Ready To Build A Greener Future?</h2>
          <p class="hp-final-cta-subtitle">Join EcoMentor AI and transform your sustainability journey into measurable impact and exciting rewards.</p>
          <div class="hp-final-cta-buttons">
            <a href="${authenticated ? '#/dashboard' : '#/signup'}" class="hp-btn hp-btn-primary hp-ripple">
              <span class="hp-btn-emoji" aria-hidden="true">✨</span>
              Create Free Account
            </a>
            <a href="#/leaderboard" class="hp-btn hp-btn-secondary hp-ripple">
              <span class="hp-btn-emoji" aria-hidden="true">🌍</span>
              Explore Challenges
            </a>
          </div>
        </div>
      </section>
    </div>
  `;

  // Initialize interactive features
  initializeHomePremium();
}

function initializeHomePremium() {
  // Carousel functionality
  const carousel = document.querySelector('[data-carousel]');
  if (carousel) {
    let currentSlide = 0;
    const slides = carousel.querySelectorAll('[data-slide]');
    const dots = carousel.querySelectorAll('[data-dot]');
    const totalSlides = slides.length;
    let autoplayTimer;

    function goToSlide(index) {
      currentSlide = (index + totalSlides) % totalSlides;
      slides.forEach((slide, i) => {
        slide.classList.toggle('is-active', i === currentSlide);
      });
      dots.forEach((dot, i) => {
        dot.classList.toggle('is-active', i === currentSlide);
        dot.setAttribute('aria-selected', i === currentSlide ? 'true' : 'false');
      });
    }

    function nextSlide() {
      goToSlide(currentSlide + 1);
    }

    function startAutoplay() {
      autoplayTimer = setInterval(nextSlide, 4000);
    }

    function stopAutoplay() {
      clearInterval(autoplayTimer);
    }

    carousel.querySelector('[data-carousel-next]').addEventListener('click', () => {
      nextSlide();
      stopAutoplay();
      startAutoplay();
    });

    carousel.querySelector('[data-carousel-prev]').addEventListener('click', () => {
      goToSlide(currentSlide - 1);
      stopAutoplay();
      startAutoplay();
    });

    dots.forEach((dot, i) => {
      dot.addEventListener('click', () => {
        goToSlide(i);
        stopAutoplay();
        startAutoplay();
      });
    });

    carousel.addEventListener('mouseenter', stopAutoplay);
    carousel.addEventListener('mouseleave', startAutoplay);

    startAutoplay();
  }

  // Counter animation when in viewport
  const counters = document.querySelectorAll('[data-counter]');
  const observerOptions = { threshold: 0.5 };

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && !entry.target.hasAttribute('data-animated')) {
        const counter = entry.target;
        const target = parseFloat(counter.getAttribute('data-target'));
        const suffix = counter.getAttribute('data-suffix') || '+';
        const valueElement = counter.querySelector('[data-counter-value]');
        let current = 0;
        const increment = target / 30;

        const animate = () => {
          current += increment;
          if (current < target) {
            valueElement.textContent = Math.floor(current);
            requestAnimationFrame(animate);
          } else {
            valueElement.textContent = target.toString();
            counter.setAttribute('data-animated', 'true');
          }
        };

        animate();
      }
    });
  }, observerOptions);

  counters.forEach((counter) => counterObserver.observe(counter));

  // Scroll reveal animations
  const revealElements = document.querySelectorAll('[data-reveal]');
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-revealed');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  revealElements.forEach((el) => revealObserver.observe(el));

  // Simple tilt effect for hero cards
  const tiltCards = document.querySelectorAll('[data-tilt]');
  tiltCards.forEach((card) => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      card.style.transform = `perspective(1000px) rotateX(${y * 10}deg) rotateY(${x * 10}deg) scale(1.05)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
    });
  });

  // Ripple effect for buttons
  document.querySelectorAll('.hp-ripple').forEach((button) => {
    button.addEventListener('click', (e) => {
      const rect = button.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const ripple = document.createElement('span');
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';
      ripple.classList.add('hp-ripple-effect');
      button.appendChild(ripple);

      setTimeout(() => ripple.remove(), 600);
    });
  });

  // Typed effect for AI coach
  const typedElements = document.querySelectorAll('[data-typed]');
  typedElements.forEach((element) => {
    const text = element.textContent;
    element.textContent = '';
    let i = 0;

    const type = () => {
      if (i < text.length) {
        element.textContent += text[i];
        i++;
        setTimeout(type, 30);
      }
    };

    // Start typing when element is in viewport
    const typeObserver = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && i === 0) {
        type();
        typeObserver.unobserve(element);
      }
    });

    typeObserver.observe(element);
  });
}

registerRoute('/', renderHome);
