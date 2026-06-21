/**
 * Lightweight reactive state store.
 *
 * Provides a simple pub/sub mechanism for sharing state
 * between loosely-coupled frontend modules.
 *
 * @module store
 */

/** @type {Object<string, any>} Internal state map. */
const state = {};

/** @type {Object<string, Function[]>} Registered listener callbacks. */
const listeners = {};

/**
 * Retrieve a value from the store.
 * @param {string} key - The state key to read.
 * @returns {any} The stored value, or undefined.
 */
export function getState(key) {
  return state[key];
}

/**
 * Set a value in the store and notify all subscribers.
 * @param {string} key - The state key to update.
 * @param {any} value - The new value.
 */
export function setState(key, value) {
  state[key] = value;
  if (listeners[key]) {
    listeners[key].forEach(callback => callback(value));
  }
}

/**
 * Subscribe to changes on a specific state key.
 *
 * @param {string} key - The state key to watch.
 * @param {Function} callback - Called with the new value on change.
 * @returns {Function} An unsubscribe function.
 */
export function subscribe(key, callback) {
  if (!listeners[key]) listeners[key] = [];
  listeners[key].push(callback);
  return () => {
    listeners[key] = listeners[key].filter(registeredCallback => registeredCallback !== callback);
  };
}
