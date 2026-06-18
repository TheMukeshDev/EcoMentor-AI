import { api, toast, registerRoute, navigate, fetchCsrfToken } from './main.js';
import { signInWithGoogle } from './auth_service.js';

function renderLogin() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <div class="auth-page">
      <h1>Welcome Back</h1>

      <button id="google-login-btn" class="btn btn-google" style="width:100%">
        <svg class="google-icon" viewBox="0 0 24 24" width="20" height="20">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        Sign in with Google
      </button>

      <div class="auth-divider"><span>or</span></div>

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

  document.getElementById('google-login-btn').addEventListener('click', async () => {
    try {
      await signInWithGoogle();
      await fetchCsrfToken();
      toast('Signed in with Google!', 'success');
      navigate('#/dashboard');
    } catch (err) {
      if (err.code !== 'auth/popup-closed-by-user') {
        document.getElementById('login-error').textContent = err.message || 'Google sign-in failed';
      }
    }
  });

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

      <button id="google-signup-btn" class="btn btn-google" style="width:100%">
        <svg class="google-icon" viewBox="0 0 24 24" width="20" height="20">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        Sign up with Google
      </button>

      <div class="auth-divider"><span>or</span></div>

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

  document.getElementById('google-signup-btn').addEventListener('click', async () => {
    try {
      await signInWithGoogle();
      await fetchCsrfToken();
      toast('Account created with Google!', 'success');
      navigate('#/dashboard');
    } catch (err) {
      if (err.code !== 'auth/popup-closed-by-user') {
        document.getElementById('signup-error').textContent = err.message || 'Google sign-up failed';
      }
    }
  });

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
