/**
 * Firebase authentication service.
 *
 * Manages user sign-in state, token lifecycle, and profile
 * synchronization with the backend API.
 *
 * @module auth_service
 */

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

/** @type {Function|null} */
let onAuthChangeCallback = null;

/** @type {Function|null} */
let onAuthErrorCallback = null;

/**
 * Register a callback for authentication state changes.
 * @param {Function} callback - Called with (user, profile) on auth change.
 */
export function onAuthStateChange(callback) {
  onAuthChangeCallback = callback;
}

/**
 * Register a callback for authentication errors.
 * @param {Function} callback - Called with the error object.
 */
export function onAuthError(callback) {
  onAuthErrorCallback = callback;
}

/** @type {Function} */
let authReadyResolve;

/** Promise that resolves once Firebase auth state is first determined. */
export const authReady = new Promise(resolve => { authReadyResolve = resolve; });

/** @type {boolean} */
let authInitialized = false;

/**
 * Build a minimal fallback profile from Firebase user data.
 * @param {Object} firebaseUser - The Firebase user object.
 * @returns {Object} A fallback user profile.
 */
function buildFallbackProfile(firebaseUser) {
  return {
    uid: firebaseUser.uid,
    name: firebaseUser.displayName || firebaseUser.email?.split('@')[0] || 'User',
    email: firebaseUser.email,
    photoURL: firebaseUser.photoURL,
    level: 1,
    streak: 0,
    totalCarbonSaved: 0,
    ecoScore: 50,
    onboardingCompleted: false,
  };
}

/**
 * Serialize a Firebase user to a storable object.
 * @param {import('firebase/auth').User} user - Firebase user.
 * @returns {Object} Serializable user data.
 */
function serializeFirebaseUser(user) {
  return {
    uid: user.uid,
    name: user.displayName || user.email?.split('@')[0] || 'User',
    email: user.email,
    photoURL: user.photoURL,
  };
}

/**
 * Initialize the Firebase onAuthStateChanged listener.
 * Must be called once during app bootstrap.
 */
export function initAuthListener() {
  onAuthStateChanged(auth, async (user) => {
    if (user) {
      const token = await user.getIdToken(true);
      localStorage.setItem('id_token', token);
      localStorage.setItem('firebase_user', JSON.stringify(serializeFirebaseUser(user)));

      if (user.emailVerified === false && user.providerData.some(p => p.providerId === 'password')) {
        setState('email_verification_needed', true);
      } else {
        setState('email_verification_needed', false);
      }

      const profile = await syncUserProfile(token, user);
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
    if (!authInitialized) {
      authInitialized = true;
      setState('auth_initialized', true);
      authReadyResolve();
    }
  });
}

/**
 * Sync the user's profile with the backend API.
 * Falls back to a local profile if the API is unreachable.
 *
 * @param {string} token - Firebase ID token.
 * @param {import('firebase/auth').User} firebaseUser - Firebase user object.
 * @returns {Promise<Object>} The user profile.
 */
async function syncUserProfile(token, firebaseUser) {
  try {
    const apiBase = import.meta.env.VITE_API_URL || '/api';
    const response = await fetch(`${apiBase}/auth/google`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ idToken: token }),
    });
    if (response.ok) {
      const responseData = await response.json();
      return responseData.data || responseData.profile || responseData;
    }
    return buildFallbackProfile(firebaseUser);
  } catch (error) {
    console.warn('Profile sync failed, using fallback:', error);
    return buildFallbackProfile(firebaseUser);
  }
}

/**
 * Sign in with Google using a popup flow.
 * @returns {Promise<{user: Object, profile: Object}>} Auth result.
 * @throws {Error} If Google sign-in fails.
 */
export async function signInWithGoogle() {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;
    const token = await user.getIdToken(true);

    localStorage.setItem('id_token', token);
    localStorage.setItem('firebase_user', JSON.stringify(serializeFirebaseUser(user)));

    const profile = await syncUserProfile(token, user);
    setState('user_profile', profile);
    setState('is_authenticated', true);

    return { user, profile };
  } catch (error) {
    if (onAuthErrorCallback) onAuthErrorCallback(error);
    throw error;
  }
}

/**
 * Sign the current user out and clear all local state.
 */
export async function logout() {
  try {
    await signOut(auth);
  } catch (error) {
    console.warn('Sign-out error:', error);
  }
  localStorage.removeItem('id_token');
  localStorage.removeItem('firebase_user');
  setState('is_authenticated', false);
  setState('user_profile', null);
}

/**
 * Get the current Firebase ID token, refreshing if needed.
 * @returns {Promise<string|null>} The ID token or null.
 */
export async function getCurrentToken() {
  if (!auth.currentUser && getState('auth_initialized') !== true) {
    await authReady;
  }
  const user = auth.currentUser;
  if (user) {
    try {
      const token = await user.getIdToken(false);
      if (token) {
        localStorage.setItem('id_token', token);
        return token;
      }
    } catch (error) {
      console.warn('Failed to get ID token from Firebase user:', error);
    }
  }
  return localStorage.getItem('id_token') || null;
}

/**
 * Get the currently cached Firebase user data.
 * @returns {Object|null} The cached user object, or null.
 */
export function getCurrentUser() {
  const serializedUser = localStorage.getItem('firebase_user');
  if (!serializedUser) return null;
  try {
    return JSON.parse(serializedUser);
  } catch {
    return null;
  }
}
