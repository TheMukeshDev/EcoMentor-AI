import {
  auth,
  googleProvider,
} from './firebase.js';
import {
  signInWithPopup,
  signOut,
  onAuthStateChanged,
} from 'firebase/auth';
import { getState, setState } from './store.js';

let onAuthChangeCallback = null;
let onAuthErrorCallback = null;

export function onAuthStateChange(cb) {
  onAuthChangeCallback = cb;
}

export function onAuthError(cb) {
  onAuthErrorCallback = cb;
}

export function initAuthListener() {
  onAuthStateChanged(auth, async (user) => {
    if (user) {
      const token = await user.getIdToken(true);
      localStorage.setItem('id_token', token);
      localStorage.setItem('firebase_user', JSON.stringify({
        uid: user.uid,
        name: user.displayName || user.email?.split('@')[0] || 'User',
        email: user.email,
        photoURL: user.photoURL,
      }));

      if (user.emailVerified === false && user.providerData.some(p => p.providerId === 'password')) {
        setState('email_verification_needed', true);
      } else {
        setState('email_verification_needed', false);
      }

      const profile = await syncUserProfile(token);
      setState('user_profile', profile);
      setState('is_authenticated', true);

      if (onAuthChangeCallback) onAuthChangeCallback(user, profile);
    } else {
      localStorage.removeItem('id_token');
      localStorage.removeItem('firebase_user');
      setState('is_authenticated', false);
      setState('user_profile', null);
      if (onAuthChangeCallback) onAuthChangeCallback(null, null);
    }
  });
}

async function syncUserProfile(token) {
  try {
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ idToken: token }),
    });
    if (res.ok) {
      const data = await res.json();
      return data.data || data.profile || data;
    }
    const userData = JSON.parse(localStorage.getItem('firebase_user') || '{}');
    return {
      uid: userData.uid,
      name: userData.name,
      email: userData.email,
      photoURL: userData.photoURL,
      level: 1,
      streak: 0,
      totalCarbonSaved: 0,
      ecoScore: 50,
      onboardingCompleted: false,
    };
  } catch {
    const userData = JSON.parse(localStorage.getItem('firebase_user') || '{}');
    return {
      uid: userData.uid,
      name: userData.name,
      email: userData.email,
      photoURL: userData.photoURL,
      level: 1,
      streak: 0,
      totalCarbonSaved: 0,
      ecoScore: 50,
      onboardingCompleted: false,
    };
  }
}

export async function signInWithGoogle() {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;
    const token = await user.getIdToken(true);

    localStorage.setItem('id_token', token);
    localStorage.setItem('firebase_user', JSON.stringify({
      uid: user.uid,
      name: user.displayName || user.email?.split('@')[0] || 'User',
      email: user.email,
      photoURL: user.photoURL,
    }));

    const profile = await syncUserProfile(token);
    setState('user_profile', profile);
    setState('is_authenticated', true);

    return { user, profile };
  } catch (error) {
    if (onAuthErrorCallback) onAuthErrorCallback(error);
    throw error;
  }
}

export async function logout() {
  try {
    await signOut(auth);
  } catch {
  }
  localStorage.removeItem('id_token');
  localStorage.removeItem('firebase_user');
  setState('is_authenticated', false);
  setState('user_profile', null);
}

export async function getCurrentToken() {
  const user = auth.currentUser;
  if (user) {
    try {
      return await user.getIdToken(false);
    } catch {
      return null;
    }
  }
  const token = localStorage.getItem('id_token');
  return token || null;
}

export function getCurrentUser() {
  const data = localStorage.getItem('firebase_user');
  return data ? JSON.parse(data) : null;
}
