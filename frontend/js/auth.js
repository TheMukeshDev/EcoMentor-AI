import { api, toast, registerRoute, navigate, fetchCsrfToken } from './main.js';

function renderLogin() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <div class="auth-page">
      <h1>Welcome Back</h1>
      <form id="login-form" novalidate>
        <div class="form-group">
          <label for="login-email">Email</label>
          <input type="email" id="login-email" required autocomplete="email"
            aria-describedby="login-email-error" placeholder="you@college.edu">
          <p id="login-email-error" class="form-error" role="alert"></p>
        </div>
        <div class="form-group">
          <label for="login-password">Password</label>
          <input type="password" id="login-password" required autocomplete="current-password"
            aria-describedby="login-password-error" placeholder="Enter your password">
          <p id="login-password-error" class="form-error" role="alert"></p>
        </div>
        <button type="submit" class="btn btn-primary" style="width:100%">Login</button>
        <p id="login-error" class="form-error" role="alert" style="text-align:center;margin-top:12px"></p>
      </form>
      <p class="form-footer">Don't have an account? <a href="#/signup">Sign up</a></p>
    </div>
  `;

  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    document.getElementById('login-error').textContent = '';
    document.getElementById('login-email-error').textContent = '';
    document.getElementById('login-password-error').textContent = '';
    document.getElementById('login-email').removeAttribute('aria-invalid');
    document.getElementById('login-password').removeAttribute('aria-invalid');

    if (!email) {
      document.getElementById('login-email-error').textContent = 'Email is required';
      document.getElementById('login-email').setAttribute('aria-invalid', 'true');
      return;
    }
    if (!password) {
      document.getElementById('login-password-error').textContent = 'Password is required';
      document.getElementById('login-password').setAttribute('aria-invalid', 'true');
      return;
    }

    try {
      const { data } = await api('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem('id_token', data.id_token);
      await fetchCsrfToken();
      toast('Login successful!', 'success');
      navigate('#/dashboard');
    } catch (err) {
      document.getElementById('login-error').textContent = err.message;
    }
  });
}

function renderSignup() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <div class="auth-page">
      <h1>Create Account</h1>
      <form id="signup-form" novalidate>
        <div class="form-group">
          <label for="signup-name">Full Name</label>
          <input type="text" id="signup-name" required autocomplete="name"
            aria-describedby="signup-name-error" placeholder="Your name">
          <p id="signup-name-error" class="form-error" role="alert"></p>
        </div>
        <div class="form-group">
          <label for="signup-email">Email</label>
          <input type="email" id="signup-email" required autocomplete="email"
            aria-describedby="signup-email-error" placeholder="you@college.edu">
          <p id="signup-email-error" class="form-error" role="alert"></p>
        </div>
        <div class="form-group">
          <label for="signup-password">Password</label>
          <input type="password" id="signup-password" required minlength="6" autocomplete="new-password"
            aria-describedby="signup-password-error" placeholder="At least 6 characters">
          <p id="signup-password-error" class="form-error" role="alert"></p>
        </div>
        <button type="submit" class="btn btn-primary" style="width:100%">Create Account</button>
        <p id="signup-error" class="form-error" role="alert" style="text-align:center;margin-top:12px"></p>
      </form>
      <p class="form-footer">Already have an account? <a href="#/login">Login</a></p>
    </div>
  `;

  document.getElementById('signup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('signup-name').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    document.getElementById('signup-error').textContent = '';
    ['name', 'email', 'password'].forEach(f => {
      document.getElementById(`signup-${f}-error`).textContent = '';
      document.getElementById(`signup-${f}`).removeAttribute('aria-invalid');
    });

    if (!name) {
      document.getElementById('signup-name-error').textContent = 'Name is required';
      document.getElementById('signup-name').setAttribute('aria-invalid', 'true');
      return;
    }
    if (!email) {
      document.getElementById('signup-email-error').textContent = 'Email is required';
      document.getElementById('signup-email').setAttribute('aria-invalid', 'true');
      return;
    }
    if (password.length < 6) {
      document.getElementById('signup-password-error').textContent = 'Password must be at least 6 characters';
      document.getElementById('signup-password').setAttribute('aria-invalid', 'true');
      return;
    }

    try {
      const { data } = await api('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
      });
      localStorage.setItem('id_token', data.id_token);
      await fetchCsrfToken();
      toast('Account created!', 'success');
      navigate('#/dashboard');
    } catch (err) {
      document.getElementById('signup-error').textContent = err.message;
    }
  });
}

registerRoute('/login', renderLogin);
registerRoute('/signup', renderSignup);
