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

describe('coach module', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="app"></div>';
    clearStorage();
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
    window.location.hash = '';
    localStorage.setItem('id_token', 'test-token');
  });

  it('renders coach page with mission, tips and chat', async () => {
    global.fetch = vi.fn().mockImplementation((url) => {
      if (url === '/api/ai/daily-mission') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: { challenge: 'Walk 10k steps', reward: 50 } }) });
      }
      if (url === '/api/ai/eco-personality') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: { personality: 'Green Guardian' } }) });
      }
      if (url === '/api/ai/recommendations') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: { tips: ['Use public transport', 'Reduce meat consumption'] } }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    await import('../js/coach.js');
    const { navigate } = await import('../js/main.js');
    navigate('#/coach');
    await new Promise(r => setTimeout(r, 30));

    expect(document.querySelector('h1').textContent).toBe('AI Coach');
    expect(document.querySelector('.mission-reward')).toBeTruthy();
    expect(document.querySelector('.tip-item')).toBeTruthy();
    expect(document.getElementById('chat-messages')).toBeTruthy();
    expect(document.getElementById('chat-input')).toBeTruthy();
    expect(document.querySelector('.what-if-form')).toBeTruthy();
  });

  it('renders coach page when APIs fail', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

    await import('../js/coach.js');
    const { navigate } = await import('../js/main.js');
    navigate('#/coach');
    await new Promise(r => setTimeout(r, 30));

    expect(document.querySelector('h1')).toBeTruthy();
    expect(document.getElementById('chat-messages')).toBeTruthy();
  });

  it('sends chat message and shows user + assistant bubbles', async () => {
    global.fetch = vi.fn().mockImplementation((url, opts) => {
      if (opts && url === '/api/ai/chat') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: { response: 'Great question!' } }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: {} }) });
    });

    await import('../js/coach.js');
    const { navigate } = await import('../js/main.js');
    navigate('#/coach');
    await new Promise(r => setTimeout(r, 30));

    const input = document.getElementById('chat-input');
    input.value = 'How can I reduce my footprint?';
    document.getElementById('chat-send').click();
    await new Promise(r => setTimeout(r, 30));

    const messages = document.querySelectorAll('.chat-message');
    expect(messages.length).toBeGreaterThanOrEqual(2);
    const lastUser = document.querySelector('.chat-message.user .chat-bubble');
    expect(lastUser).toBeTruthy();
    expect(lastUser.textContent).toBe('How can I reduce my footprint?');
  });

  it('sends chat on Enter key', async () => {
    global.fetch = vi.fn().mockImplementation((url, opts) => {
      if (opts && url === '/api/ai/chat') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: { response: 'OK' } }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: {} }) });
    });

    await import('../js/coach.js');
    const { navigate } = await import('../js/main.js');
    navigate('#/coach');
    await new Promise(r => setTimeout(r, 30));

    const input = document.getElementById('chat-input');
    input.value = 'Hello coach';
    const event = new KeyboardEvent('keydown', { key: 'Enter', shiftKey: false });
    input.dispatchEvent(event);
    await new Promise(r => setTimeout(r, 30));

    const userBubble = document.querySelector('.chat-message.user .chat-bubble');
    expect(userBubble).toBeTruthy();
    expect(userBubble.textContent).toBe('Hello coach');
  });

  it('handles chat API error gracefully', async () => {
    global.fetch = vi.fn().mockImplementation((url, opts) => {
      if (opts && url === '/api/ai/chat') {
        return Promise.reject(new Error('API error'));
      }
      if (url === '/api/ai/daily-mission' || url === '/api/ai/eco-personality' || url === '/api/ai/recommendations') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: {} }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    await import('../js/coach.js');
    const { navigate } = await import('../js/main.js');
    navigate('#/coach');
    await new Promise(r => setTimeout(r, 30));

    document.getElementById('chat-input').value = 'Test';
    document.getElementById('chat-send').click();
    await new Promise(r => setTimeout(r, 30));

    const bubbles = document.querySelectorAll('.chat-message.assistant .chat-bubble');
    const lastBubble = bubbles[bubbles.length - 1];
    expect(lastBubble.textContent).toBe('Sorry, I had trouble connecting. Please try again.');
  });

  it('appends message with correct DOM structure', async () => {
    document.body.innerHTML = '<div id="app"><div id="chat-messages" class="chat-messages"></div></div>';
    const mod = await import('../js/coach.js');

    mod.appendMessage('user', 'Hello');

    const msg = document.querySelector('.chat-message');
    expect(msg).toBeTruthy();
    expect(msg.classList.contains('user')).toBe(true);
    expect(msg.querySelector('.chat-bubble').textContent).toBe('Hello');
    expect(msg.querySelector('.chat-avatar')).toBeTruthy();

    mod.appendMessage('assistant', 'Hi there!');
    const msgs = document.querySelectorAll('.chat-message');
    expect(msgs.length).toBe(2);
    expect(msgs[1].classList.contains('assistant')).toBe(true);
  });

  it('shows thinking indicator while waiting for response', async () => {
    let resolveChat;
    global.fetch = vi.fn().mockImplementation((url, opts) => {
      if (opts && url === '/api/ai/chat') {
        return new Promise(resolve => { resolveChat = resolve; });
      }
      if (url === '/api/ai/daily-mission' || url === '/api/ai/eco-personality' || url === '/api/ai/recommendations') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: {} }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    await import('../js/coach.js');
    const { navigate } = await import('../js/main.js');
    navigate('#/coach');
    await new Promise(r => setTimeout(r, 30));

    document.getElementById('chat-input').value = 'Wait';
    document.getElementById('chat-send').click();
    await new Promise(r => setTimeout(r, 10));

    const thinking = document.querySelector('.thinking');
    expect(thinking).toBeTruthy();
    expect(thinking.querySelector('.chat-bubble').textContent).toBe('Thinking...');

    resolveChat({ ok: true, json: () => Promise.resolve({ data: { response: 'Done' } }) });
    await new Promise(r => setTimeout(r, 10));
    expect(document.querySelector('.thinking')).toBeNull();
  });

  it('what-if analyzer sends request and shows result', async () => {
    global.fetch = vi.fn().mockImplementation((url, opts) => {
      if (opts && url === '/api/ai/what-if') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({
          data: { estimated_impact: 'high', carbon_saved: 15, comparison: 'Better', tip: 'Great choice' }
        }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: {} }) });
    });

    await import('../js/coach.js');
    const { navigate } = await import('../js/main.js');
    navigate('#/coach');
    await new Promise(r => setTimeout(r, 30));

    document.getElementById('wi-analyze').click();
    await new Promise(r => setTimeout(r, 30));

    const result = document.getElementById('wi-result');
    expect(result.style.display).toBe('block');
    expect(result.textContent).toContain('high');
    expect(result.textContent).toContain('15');
  });

  it('what-if analyzer shows error on failure', async () => {
    global.fetch = vi.fn().mockImplementation((url, opts) => {
      if (opts && url === '/api/ai/what-if') {
        return Promise.reject(new Error('Analysis failed'));
      }
      if (url === '/api/ai/daily-mission' || url === '/api/ai/eco-personality' || url === '/api/ai/recommendations') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: {} }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    await import('../js/coach.js');
    const { navigate } = await import('../js/main.js');
    navigate('#/coach');
    await new Promise(r => setTimeout(r, 30));

    document.getElementById('wi-analyze').click();
    await new Promise(r => setTimeout(r, 30));

    const result = document.getElementById('wi-result');
    expect(result.textContent).toContain('Analysis failed');
  });
});
