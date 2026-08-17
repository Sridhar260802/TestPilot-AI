// src/services/authService.js
//
// Matches the actual backend endpoints (FastAPI, prefix /users and /plans):
//   POST /users/signup        { username, email, password }  -> user (no token)
//   POST /users/login         { email, password }             -> { access_token, token_type }
//   POST /users/google        { token }                        -> user + access_token
//   GET  /users/me            (Bearer token)                   -> { message, user }
//   PUT  /users/plan          { plan } (Bearer token)           -> user
//
// The backend has no /forgot-password endpoint yet — requestPasswordReset()
// will fail with a real network/404 error until one is added.

const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || "http://localhost:8000";

const TOKEN_STORAGE_KEY = "auth_token";
const USER_STORAGE_KEY = "auth_user";

export class AuthError extends Error {
  constructor(message, field, status) {
    super(message);
    this.name = "AuthError";
    this.field = field;
    this.status = status;
  }
}

async function apiRequest(path, { method = "POST", body, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new AuthError("Could not reach the server. Please check your connection and try again.");
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // no JSON body
  }

  if (!response.ok) {
    // This backend returns FastAPI's default { detail: "..." } shape,
    // not { error: { message, field } } — normalize it here so the UI
    // components only ever have to handle one error shape.
    const message =
      (typeof data?.detail === "string" && data.detail) ||
      data?.error?.message ||
      "Something went wrong. Please try again.";
    const field = data?.error?.field;
    throw new AuthError(message, field, response.status);
  }

  return data;
}

function persistSession(user, token) {
  if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
  if (user) localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
}

export function getToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function isAuthenticated() {
  return Boolean(getToken());
}

/**
 * Create a new account, then immediately log in (the signup endpoint
 * doesn't return a token itself, only the login endpoint does).
 */
export async function signup({ username, email, password }) {
  await apiRequest("/users/signup", { body: { username, email, password } });
  return login({ email, password });
}

export async function login({ email, password }) {
  const data = await apiRequest("/users/login", { body: { email, password } });
  persistSession(null, data.access_token);
  const user = await getCurrentUser();
  return { user, token: data.access_token };
}

/**
 * Exchange a Google ID token for a session. The backend verifies the
 * token with Google server-side before creating/finding the user.
 */
export async function googleLogin({ idToken }) {
  const data = await apiRequest("/users/google", { body: { token: idToken } });
  const user = {
    id: data.id,
    username: data.username,
    email: data.email,
    plan: data.plan,
    auth_provider: data.auth_provider,
    picture: data.picture,
  };
  persistSession(user, data.access_token);
  return { user, token: data.access_token };
}

export async function getCurrentUser() {
  const data = await apiRequest("/users/me", { method: "GET", auth: true });
  const user = data.user;
  persistSession(user, null);
  return user;
}

/**
 * Upgrade/downgrade the current user's plan. Call this after a
 * successful payment.
 */
export async function updatePlan(plan) {
  const user = await apiRequest("/users/plan", { method: "PUT", auth: true, body: { plan } });
  persistSession(user, null);
  return user;
}

/**
 * NOT YET IMPLEMENTED on the backend — there's no /users/forgot-password
 * route in the current backend. This will fail with a real 404 until
 * one is added there.
 */
export async function requestPasswordReset({ email }) {
  return apiRequest("/users/forgot-password", { body: { email } });
}

export async function logout() {
  // No server-side session to invalidate (stateless JWT) — just clear
  // the local copy.
  clearSession();
}

const authService = {
  signup,
  login,
  googleLogin,
  getCurrentUser,
  updatePlan,
  requestPasswordReset,
  logout,
  getToken,
  getStoredUser,
  isAuthenticated,
};

export default authService;
