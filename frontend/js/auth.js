import { api, toast, registerRoute, navigate, fetchCsrfToken } from './main.js';
import { signInWithGoogle } from './auth_service.js';

function renderLogin() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <div style="min-height: calc(100vh - 80px); display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--color-bg) 0%, var(--color-primary-bg) 100%); padding: 20px;">
      <div style="background: var(--color-surface); padding: 40px; border-radius: var(--radius-lg); box-shadow: var(--shadow-xl); width: 100%; max-width: 380px; border: 1px solid var(--color-border);">
        <div style="text-align: center; margin-bottom: 24px;">
          <h1 style="font-size: 1.8rem; font-weight: 800; color: var(--color-text); margin-bottom: 6px;">Welcome Back</h1>
          <p style="color: var(--color-text-muted); font-size: 0.95rem;">Sign in to your account</p>
        </div>

        <button id="google-login-btn" class="btn" style="width:100%; background: white; color: #333; border: 1px solid #ddd; padding: 11px; border-radius: var(--radius-sm); font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 18px; box-shadow: var(--shadow-sm); cursor: pointer; transition: var(--transition); font-size: 0.95rem;">
          <svg viewBox="0 0 24 24" width="18" height="18">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Google
        </button>

        <div style="display: flex; align-items: center; text-align: center; margin-bottom: 18px; color: var(--color-text-muted); font-size: 0.85rem;">
          <hr style="flex: 1; border: none; border-top: 1px solid var(--color-border);">
          <span style="padding: 0 12px;">or</span>
          <hr style="flex: 1; border: none; border-top: 1px solid var(--color-border);">
        </div>

        <form id="login-form" novalidate>
          <div class="form-group" style="margin-bottom: 16px;">
            <label for="login-email" style="display: block; margin-bottom: 6px; font-weight: 500; color: var(--color-text-secondary); font-size: 0.9rem;">Email</label>
            <input type="email" id="login-email" required autocomplete="email" style="width: 100%; padding: 10px 12px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: var(--color-surface); color: var(--color-text); font-size: 0.95rem; transition: var(--transition);" placeholder="your@email.com">
            <p id="login-email-error" class="form-error" role="alert" style="color: var(--color-error); font-size: 0.8rem; margin-top: 3px;"></p>
          </div>
          <div class="form-group" style="margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <label for="login-password" style="font-weight: 500; color: var(--color-text-secondary); font-size: 0.9rem;">Password</label>
              <a href="#" style="font-size: 0.8rem; color: var(--color-primary); text-decoration: none; font-weight: 500;">Forgot?</a>
            </div>
            <input type="password" id="login-password" required autocomplete="current-password" style="width: 100%; padding: 10px 12px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: var(--color-surface); color: var(--color-text); font-size: 0.95rem; transition: var(--transition);" placeholder="••••••••">
            <p id="login-password-error" class="form-error" role="alert" style="color: var(--color-error); font-size: 0.8rem; margin-top: 3px;"></p>
          </div>
          <button type="submit" class="btn btn-primary" style="width:100%; padding: 11px; font-size: 1rem; border-radius: var(--radius-sm); font-weight: 600; box-shadow: var(--shadow-md);">Sign In</button>
          <p id="login-error" class="form-error" role="alert" style="text-align:center;margin-top:12px;color:var(--color-error);font-weight:500;font-size:0.9rem;"></p>
        </form>
        <p style="text-align: center; margin-top: 20px; color: var(--color-text-muted); font-size: 0.9rem;">
          New here? <a href="#/signup" style="color: var(--color-primary); font-weight: 600; text-decoration: none;">Create account</a>
        </p>
      </div>
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
    <div style="min-height: calc(100vh - 80px); display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--color-bg) 0%, var(--color-primary-bg) 100%); padding: 20px;">
      <div style="background: var(--color-surface); padding: 40px; border-radius: var(--radius-lg); box-shadow: var(--shadow-xl); width: 100%; max-width: 380px; border: 1px solid var(--color-border);">
        <div style="text-align: center; margin-bottom: 24px;">
          <h1 style="font-size: 1.8rem; font-weight: 800; color: var(--color-text); margin-bottom: 6px;">Create Account</h1>
          <p style="color: var(--color-text-muted); font-size: 0.95rem;">Join EcoMentor today</p>
        </div>

        <button id="google-signup-btn" class="btn" style="width:100%; background: white; color: #333; border: 1px solid #ddd; padding: 11px; border-radius: var(--radius-sm); font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 18px; box-shadow: var(--shadow-sm); cursor: pointer; transition: var(--transition); font-size: 0.95rem;">
          <svg viewBox="0 0 24 24" width="18" height="18">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Google
        </button>

        <div style="display: flex; align-items: center; text-align: center; margin-bottom: 18px; color: var(--color-text-muted); font-size: 0.85rem;">
          <hr style="flex: 1; border: none; border-top: 1px solid var(--color-border);">
          <span style="padding: 0 12px;">or</span>
          <hr style="flex: 1; border: none; border-top: 1px solid var(--color-border);">
        </div>

        <form id="signup-form" novalidate>
          <div class="form-group" style="margin-bottom: 14px;">
            <label for="signup-name" style="display: block; margin-bottom: 6px; font-weight: 500; color: var(--color-text-secondary); font-size: 0.9rem;">Full Name</label>
            <input type="text" id="signup-name" required autocomplete="name" style="width: 100%; padding: 10px 12px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: var(--color-surface); color: var(--color-text); font-size: 0.95rem; transition: var(--transition);" placeholder="Your name">
            <p id="signup-name-error" class="form-error" role="alert" style="color: var(--color-error); font-size: 0.8rem; margin-top: 3px;"></p>
          </div>
          <div class="form-group" style="margin-bottom: 14px;">
            <label for="signup-email" style="display: block; margin-bottom: 6px; font-weight: 500; color: var(--color-text-secondary); font-size: 0.9rem;">Email</label>
            <input type="email" id="signup-email" required autocomplete="email" style="width: 100%; padding: 10px 12px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: var(--color-surface); color: var(--color-text); font-size: 0.95rem; transition: var(--transition);" placeholder="your@email.com">
            <p id="signup-email-error" class="form-error" role="alert" style="color: var(--color-error); font-size: 0.8rem; margin-top: 3px;"></p>
          </div>
          <div class="form-group" style="margin-bottom: 20px;">
            <label for="signup-password" style="display: block; margin-bottom: 6px; font-weight: 500; color: var(--color-text-secondary); font-size: 0.9rem;">Password</label>
            <input type="password" id="signup-password" required minlength="6" autocomplete="new-password" style="width: 100%; padding: 10px 12px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: var(--color-surface); color: var(--color-text); font-size: 0.95rem; transition: var(--transition);" placeholder="Min. 6 characters">
            <p id="signup-password-error" class="form-error" role="alert" style="color: var(--color-error); font-size: 0.8rem; margin-top: 3px;"></p>
          </div>
          <button type="submit" class="btn btn-primary" style="width:100%; padding: 11px; font-size: 1rem; border-radius: var(--radius-sm); font-weight: 600; box-shadow: var(--shadow-md);">Create Account</button>
          <p id="signup-error" class="form-error" role="alert" style="text-align:center;margin-top:12px;color:var(--color-error);font-weight:500;font-size:0.9rem;"></p>
        </form>
        <p style="text-align: center; margin-top: 20px; color: var(--color-text-muted); font-size: 0.9rem;">
          Already have account? <a href="#/login" style="color: var(--color-primary); font-weight: 600; text-decoration: none;">Sign in</a>
        </p>
      </div>
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
