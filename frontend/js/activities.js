import { api, toast, registerRoute, navigate } from './main.js';
import { clearCache } from './api-client.js';

const WIZARD_STEPS = [
  { id: 'transport', title: 'Travel', icon: '\uD83D\uDE8C' },
  { id: 'electricity', title: 'Electricity', icon: '\u26A1' },
  { id: 'food', title: 'Food', icon: '\uD83C\uDF31' },
  { id: 'waste', title: 'Waste', icon: '\uD83D\uDDF1' },
];

let wizardData = {};
let currentStep = 0;

function renderWizard() {
  wizardData = {};
  currentStep = 0;
  const app = document.getElementById('app');
  app.innerHTML = /* safe HTML - static wizard template */ `
    <div class="wizard-page">
      <h1>Log Activity</h1>
      <p>Tell us about your day — one step at a time</p>
      <div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" id="wizard-progress">
        ${WIZARD_STEPS.map((s, i) => `<div class="progress-step ${i === 0 ? 'active' : ''}" data-step="${i}"></div>`).join('')}
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:4px;margin-bottom:24px">
        ${WIZARD_STEPS.map(s => `<span class="progress-label" style="flex:1;text-align:center">${s.icon} ${s.title}</span>`).join('')}
      </div>
      <form id="wizard-form" novalidate>
        ${WIZARD_STEPS.map((s, i) => `
          <div class="wizard-step ${i === 0 ? 'active' : ''}" data-step="${i}">
            ${getStepContent(s)}
          </div>
        `).join('')}
        <div class="wizard-nav">
          <button type="button" class="btn btn-ghost" id="wizard-prev" hidden>Back</button>
          <button type="button" class="btn btn-primary" id="wizard-next">Next</button>
        </div>
      </form>
    </div>
  `;

  document.getElementById('wizard-next').addEventListener('click', onNext);
  document.getElementById('wizard-prev').addEventListener('click', onPrev);

  document.querySelectorAll('.option-group').forEach(group => {
    const buttons = group.querySelectorAll('.option-btn');
    buttons.forEach((btn, idx) => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => {
          b.classList.remove('selected');
          b.setAttribute('aria-checked', 'false');
        });
        btn.classList.add('selected');
        btn.setAttribute('aria-checked', 'true');
        const input = group.querySelector('input');
        if (input) {
          input.value = btn.dataset.value;
          input.dispatchEvent(new Event('input'));
        }
      });
      btn.addEventListener('keydown', (e) => {
        let targetIdx = -1;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
          e.preventDefault();
          targetIdx = (idx + 1) % buttons.length;
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
          e.preventDefault();
          targetIdx = (idx - 1 + buttons.length) % buttons.length;
        }
        if (targetIdx >= 0) {
          buttons[targetIdx].focus();
          buttons[targetIdx].click();
        }
      });
    });
  });
}

function getStepContent(step) {
  switch (step.id) {
    case 'transport':
      return `
        <h2 tabindex="-1">How did you travel today?</h2>
        <div class="form-group">
          <label for="transport-mode">Mode of transport</label>
          <div class="option-group" role="radiogroup" aria-label="Transport mode">
            ${[
              { value: 'walking', label: 'Walked', icon: '\uD83D\uDEB6' },
              { value: 'bicycle', label: 'Cycled', icon: '\uD83D\uDEB2' },
              { value: 'bus', label: 'Bus', icon: '\uD83D\uDE8C' },
              { value: 'metro', label: 'Metro', icon: '\uD83D\uDE87' },
              { value: 'car', label: 'Car', icon: '\uD83D\uDE97' },
              { value: 'plane', label: 'Plane', icon: '\u2708\uFE0F' },
            ].map((o, i) => `
              <button type="button" class="option-btn" data-value="${o.value}" role="radio" aria-checked="${i === 0}">
                ${o.icon} ${o.label}
              </button>
            `).join('')}
          </div>
          <input type="hidden" id="transport-mode" value="walking">
        </div>
        <div class="form-group">
          <label for="transport-distance">Distance (km)</label>
          <input type="number" id="transport-distance" min="0" step="0.1" value="0"
            aria-describedby="transport-distance-desc">
          <p id="transport-distance-desc" class="form-error" role="alert"></p>
        </div>
      `;
    case 'electricity':
      return `
        <h2 tabindex="-1">AC usage today?</h2>
        <div class="form-group">
          <label for="ac-usage">Hours used</label>
          <div class="option-group" role="radiogroup" aria-label="AC usage">
            ${[
              { value: 'none', label: 'None', icon: '\u274C' },
              { value: '1-2', label: '1-2 hours', icon: '\uD83D\uDD25' },
              { value: '3-5', label: '3-5 hours', icon: '\uD83D\uDD25\uD83D\uDD25' },
              { value: '6+', label: '6+ hours', icon: '\uD83E\uDDCA' },
            ].map((o, i) => `
              <button type="button" class="option-btn" data-value="${o.value}" role="radio" aria-checked="${i === 0}">
                ${o.icon} ${o.label}
              </button>
            `).join('')}
          </div>
          <input type="hidden" id="ac-usage" value="none">
        </div>
      `;
    case 'food':
      return `
        <h2 tabindex="-1">What did you eat today?</h2>
        <div class="form-group">
          <label for="food-type">Diet type</label>
          <div class="option-group" role="radiogroup" aria-label="Diet type">
            ${[
              { value: 'vegan', label: 'Vegan', icon: '\uD83C\uDF31' },
              { value: 'vegetarian', label: 'Vegetarian', icon: '\uD83E\uDD55' },
              { value: 'non_vegetarian', label: 'Non-veg', icon: '\uD83C\uDF54' },
            ].map(o => `
              <button type="button" class="option-btn" data-value="${o.value}" role="radio" aria-checked="${o.value === 'vegetarian'}">
                ${o.icon} ${o.label}
              </button>
            `).join('')}
          </div>
          <input type="hidden" id="food-type" value="vegetarian">
        </div>
      `;
    case 'waste':
      return `
        <h2 tabindex="-1">Plastic waste today?</h2>
        <div class="form-group">
          <label for="plastic-waste">Plastic waste (kg)</label>
          <input type="number" id="plastic-waste" min="0" step="0.1" value="0"
            aria-describedby="plastic-waste-desc" placeholder="e.g. 0.5">
          <p id="plastic-waste-desc" class="form-error" role="alert"></p>
        </div>
      `;
    default:
      return '';
  }
}

function onNext() {
  const step = WIZARD_STEPS[currentStep];
  if (!validateStep(step)) return;

  if (currentStep < WIZARD_STEPS.length - 1) {
    currentStep++;
    showStep(currentStep);
  } else {
    submitActivity();
  }
}

function onPrev() {
  if (currentStep > 0) {
    currentStep--;
    showStep(currentStep);
  }
}

function validateStep(step) {
  let valid = true;
  if (step.id === 'transport') {
    const dist = parseFloat(document.getElementById('transport-distance').value);
    if (dist < 0) {
      document.getElementById('transport-distance-desc').textContent = 'Distance must be 0 or more';
      document.getElementById('transport-distance').setAttribute('aria-invalid', 'true');
      valid = false;
    } else {
      document.getElementById('transport-distance-desc').textContent = '';
      document.getElementById('transport-distance').removeAttribute('aria-invalid');
    }
  }
  if (step.id === 'waste') {
    const waste = parseFloat(document.getElementById('plastic-waste').value);
    if (waste < 0) {
      document.getElementById('plastic-waste-desc').textContent = 'Waste must be 0 or more';
      document.getElementById('plastic-waste').setAttribute('aria-invalid', 'true');
      valid = false;
    } else {
      document.getElementById('plastic-waste-desc').textContent = '';
      document.getElementById('plastic-waste').removeAttribute('aria-invalid');
    }
  }
  return valid;
}

function showStep(index) {
  document.querySelectorAll('.wizard-step').forEach(el => el.classList.remove('active'));
  const stepEl = document.querySelector(`.wizard-step[data-step="${index}"]`);
  stepEl.classList.add('active');
  const heading = stepEl.querySelector('h2');
  if (heading) heading.focus();

  document.querySelectorAll('.progress-step').forEach((el, i) => {
    el.classList.toggle('active', i <= index);
  });

  const progress = document.getElementById('wizard-progress');
  const pct = Math.round(((index + 1) / WIZARD_STEPS.length) * 100);
  if (progress) progress.setAttribute('aria-valuenow', pct);

  const nextBtn = document.getElementById('wizard-next');
  nextBtn.textContent = index === WIZARD_STEPS.length - 1 ? 'Submit' : 'Next';

  const prevBtn = document.getElementById('wizard-prev');
  if (index === 0) {
    prevBtn.hidden = true;
  } else {
    prevBtn.hidden = false;
  }
}

async function submitActivity() {
  const nextBtn = document.getElementById('wizard-next');
  nextBtn.disabled = true;
  nextBtn.textContent = 'Saving...';

  wizardData = {
    transport: document.getElementById('transport-mode')?.value || 'walking',
    distance: parseFloat(document.getElementById('transport-distance')?.value) || 0,
    ac_usage: document.getElementById('ac-usage')?.value || 'none',
    food_type: document.getElementById('food-type')?.value || 'vegetarian',
    plastic_waste: parseFloat(document.getElementById('plastic-waste')?.value) || 0,
  };

  try {
    await api('/activities', {
      method: 'POST',
      body: JSON.stringify(wizardData),
    });
    clearCache();
    toast('Activity logged! +10 points', 'success');
    navigate('#/dashboard');
  } catch (err) {
    toast(err.message, 'error');
    nextBtn.disabled = false;
    nextBtn.textContent = 'Submit';
  }
}

registerRoute('/log', renderWizard);
