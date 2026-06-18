import { api, registerRoute, htmlEscape } from './main.js';

async function renderCoach() {
  const app = document.getElementById('app');
  app.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading coach...</span></div>';

  try {
    const [missionRes, personalityRes, tipsRes] = await Promise.all([
      api('/ai/daily-mission').catch(() => ({ data: null })),
      api('/ai/eco-personality').catch(() => ({ data: null })),
      api('/ai/recommendations', {
        method: 'POST',
        body: JSON.stringify({ score: 50, transport: 'walking', food: 'vegetarian', ac_usage: 'none' }),
      }).catch(() => ({ data: null })),
    ]);

    const mission = missionRes.data;
    const personality = personalityRes.data;
    const tips = tipsRes.data?.tips || [];

    app.innerHTML = `
      <div style="max-width:600px;margin:0 auto">
        <h1 style="margin-bottom:8px">AI Coach</h1>
        <p style="color:var(--color-text-secondary);margin-bottom:24px">
          ${personality ? htmlEscape(personality.personality) + ' &mdash; ' : ''}
          Personalized coaching and daily missions
        </p>

        ${mission ? `
          <div class="card" style="margin-bottom:24px">
            <div class="card-title">Today's Mission</div>
            <p style="margin:12px 0;font-size:1.1rem;line-height:1.5">${htmlEscape(mission.challenge)}</p>
            <span class="mission-reward">+${mission.reward || 0} pts</span>
          </div>
        ` : ''}

        <div class="card" style="margin-bottom:16px">
          <div class="card-title">AI Chat</div>
          <div id="chat-messages" class="chat-messages" role="log" aria-label="Chat conversation" aria-live="polite">
            <div class="chat-message assistant">
              <span class="chat-avatar" aria-hidden="true">&#129309;</span>
              <div class="chat-bubble">
                Hi! I'm your EcoMentor coach. Ask me anything about your carbon footprint, sustainability tips, or how to improve your score!
              </div>
            </div>
          </div>
          <div class="chat-input-row">
            <input type="text" id="chat-input" class="chat-input" placeholder="Ask your coach anything..." aria-label="Type your message" maxlength="2000">
            <button id="chat-send" class="btn btn-primary chat-send-btn" aria-label="Send message">Send</button>
          </div>
        </div>

        <div class="card" style="margin-bottom:16px">
          <div class="card-title">Eco Tips</div>
          ${tips.length > 0 ? tips.map((tip, i) => `
            <div class="tip-item" style="padding:8px 0;border-bottom:1px solid var(--color-border, #e2e8f0)">
              <span style="font-weight:600;color:var(--color-primary)">${i + 1}.</span>
              <span>${htmlEscape(tip)}</span>
            </div>
          `).join('') : `
            <p style="margin-top:8px;color:var(--color-text-secondary)">
              Log activities to get personalized tips!
            </p>
          `}
        </div>

        <div class="card" style="margin-bottom:16px">
          <div class="card-title">What-If Analyzer</div>
          <p style="color:var(--color-text-secondary);margin-bottom:12px">See how changing your habits affects your carbon footprint.</p>
          <div class="what-if-form">
            <div class="form-group">
              <label for="wi-transport">Change transport to:</label>
              <select id="wi-transport" class="form-select">
                <option value="walking">Walking</option>
                <option value="bicycle">Bicycle</option>
                <option value="bus">Bus</option>
                <option value="metro">Metro</option>
                <option value="car">Car</option>
                <option value="plane">Plane</option>
              </select>
            </div>
            <div class="form-group">
              <label for="wi-diet">Change diet to:</label>
              <select id="wi-diet" class="form-select">
                <option value="vegan">Vegan</option>
                <option value="vegetarian">Vegetarian</option>
                <option value="non_vegetarian">Non-vegetarian</option>
              </select>
            </div>
            <button id="wi-analyze" class="btn btn-secondary" style="width:100%">Analyze Impact</button>
            <div id="wi-result" class="what-if-result" style="display:none;margin-top:12px"></div>
          </div>
        </div>
      </div>
    `;

    setupChat();
    setupWhatIf();
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

function setupChat() {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send');
  const messages = document.getElementById('chat-messages');

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    appendMessage('user', text);
    appendMessage('assistant', 'Thinking...', true);

    try {
      const res = await api('/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ message: text }),
      });
      const thinkingEl = messages.querySelector('.thinking');
      if (thinkingEl) thinkingEl.remove();
      appendMessage('assistant', res.data?.response || 'I could not process that. Please try again.');
    } catch (err) {
      const thinkingEl = messages.querySelector('.thinking');
      if (thinkingEl) thinkingEl.remove();
      appendMessage('assistant', 'Sorry, I had trouble connecting. Please try again.');
    }

    messages.scrollTop = messages.scrollHeight;
  }

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  sendBtn.addEventListener('click', sendMessage);
}

function appendMessage(role, content, isThinking = false) {
  const messages = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-message ${role}${isThinking ? ' thinking' : ''}`;
  if (isThinking) {
    div.innerHTML = `<span class="chat-avatar" aria-hidden="true">&#129309;</span><div class="chat-bubble">${htmlEscape(content)}</div>`;
  } else {
    const avatar = role === 'assistant' ? '&#129309;' : '&#128100;';
    div.innerHTML = `<span class="chat-avatar" aria-hidden="true">${avatar}</span><div class="chat-bubble">${htmlEscape(content)}</div>`;
  }
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function setupWhatIf() {
  const btn = document.getElementById('wi-analyze');
  const result = document.getElementById('wi-result');

  btn.addEventListener('click', async () => {
    const transport = document.getElementById('wi-transport').value;
    const foodType = document.getElementById('wi-diet').value;

    btn.disabled = true;
    btn.textContent = 'Analyzing...';
    result.style.display = 'none';

    const scenario = `Switch to ${transport} transport and ${foodType} diet`;

    try {
      const res = await api('/ai/what-if', {
        method: 'POST',
        body: JSON.stringify({
          transport: 'car',
          distance: 10,
          food_type: 'non_vegetarian',
          ac_usage: '3-5',
          plastic_waste: 0.5,
          scenario_description: scenario,
        }),
      });
      const data = res.data || {};
      result.innerHTML = `
        <div class="what-if-result-inner" style="padding:12px;background:var(--color-surface-alt, #f7fafc);border-radius:8px">
          <p><strong>Impact:</strong> ${htmlEscape(data.estimated_impact || 'unknown')}</p>
          <p><strong>Carbon saved:</strong> ${data.carbon_saved || 0} kg CO&#8322;</p>
          <p><strong>Comparison:</strong> ${htmlEscape(data.comparison || 'N/A')}</p>
          <p><strong>Tip:</strong> ${htmlEscape(data.tip || 'Keep making sustainable choices!')}</p>
        </div>
      `;
      result.style.display = 'block';
    } catch (err) {
      result.innerHTML = `<p style="color:var(--color-error)">${htmlEscape(err.message)}</p>`;
      result.style.display = 'block';
    }

    btn.disabled = false;
    btn.textContent = 'Analyze Impact';
  });
}

export { appendMessage };
registerRoute('/coach', renderCoach);
