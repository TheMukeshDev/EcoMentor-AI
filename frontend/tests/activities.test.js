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

beforeAll(() => {
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
  window.matchMedia = vi.fn().mockImplementation((query) => ({
    matches: false, media: query, onchange: null,
    addListener: vi.fn(), removeListener: vi.fn(),
    addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
  }));
});

function clearStorage() {
  Object.keys(store).forEach(k => delete store[k]);
}

describe('wizard', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="app"></div>';
    clearStorage();
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
  });

  it('renders wizard with 4 steps', async () => {
    await import('../js/activities.js');
    const { navigate } = await import('../js/main.js');

    navigate('#/log');
    await new Promise(r => setTimeout(r, 20));

    expect(document.querySelector('.wizard-page')).toBeTruthy();
    expect(document.querySelectorAll('.wizard-step').length).toBe(4);
    expect(document.getElementById('wizard-next')).toBeTruthy();
    expect(document.getElementById('wizard-prev')).toBeTruthy();
  });

  it('renders transport fields on first step', async () => {
    await import('../js/activities.js');
    const { navigate } = await import('../js/main.js');

    navigate('#/log');
    await new Promise(r => setTimeout(r, 20));

    const firstStep = document.querySelector('.wizard-step.active');
    expect(firstStep).toBeTruthy();
    expect(firstStep.innerHTML).toContain('transport');
    expect(document.getElementById('transport-mode')).toBeTruthy();
    expect(document.getElementById('transport-distance')).toBeTruthy();
  });

  it('navigates to next step on clicking Next', async () => {
    await import('../js/activities.js');
    const { navigate } = await import('../js/main.js');

    navigate('#/log');
    await new Promise(r => setTimeout(r, 20));

    document.getElementById('wizard-next').click();
    await new Promise(r => setTimeout(r, 10));

    // Step 1 (index 1) should now be active (electricity)
    const activeSteps = document.querySelectorAll('.wizard-step.active');
    expect(activeSteps.length).toBe(1);
    expect(activeSteps[0].dataset.step).toBe('1');
  });

  it('shows error for negative distance', async () => {
    await import('../js/activities.js');
    const { navigate } = await import('../js/main.js');

    navigate('#/log');
    await new Promise(r => setTimeout(r, 20));

    document.getElementById('transport-distance').value = '-5';
    document.getElementById('wizard-next').click();
    await new Promise(r => setTimeout(r, 10));

    expect(document.getElementById('transport-distance-desc').textContent)
      .toBe('Distance must be 0 or more');
  });

  it('shows error for negative plastic waste on waste step', async () => {
    await import('../js/activities.js');
    const { navigate } = await import('../js/main.js');

    navigate('#/log');
    await new Promise(r => setTimeout(r, 20));

    // Navigate through steps to reach waste (step 3)
    for (let i = 0; i < 3; i++) {
      document.getElementById('wizard-next').click();
      await new Promise(r => setTimeout(r, 10));
    }

    document.getElementById('plastic-waste').value = '-1';
    document.getElementById('wizard-next').click();
    await new Promise(r => setTimeout(r, 10));

    expect(document.getElementById('plastic-waste-desc').textContent)
      .toBe('Waste must be 0 or more');
  });

  it('submits activity on final step', async () => {
    await import('../js/activities.js');
    const { navigate } = await import('../js/main.js');

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });
    global.fetch = mockFetch;

    navigate('#/log');
    await new Promise(r => setTimeout(r, 20));

    // Navigate through all steps
    for (let i = 0; i < 3; i++) {
      document.getElementById('wizard-next').click();
      await new Promise(r => setTimeout(r, 10));
    }

    // On 4th step, Next becomes Submit
    document.getElementById('wizard-next').click();
    await new Promise(r => setTimeout(r, 30));

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/activities',
      expect.objectContaining({ method: 'POST' })
    );
  });
});
