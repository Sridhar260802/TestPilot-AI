// src/services/mobileTestService.js
//
// Matches the backend endpoints (FastAPI, prefix /mobile):
//   POST /mobile/test                       multipart file upload (Bearer token) -> analysis JSON
//   GET  /mobile/history                    (Bearer token)                       -> history list
//   GET  /mobile/history/{id}/download      (Bearer token)                       -> PDF blob
//
// Access is tiered by the user's plan (same plan the rest of the app uses):
//   basic    -> Android (.apk) only, basic checks
//   standard -> Android + iOS (.ipa), standard checks
//   premium  -> Android + iOS, full deep-security checks
//
// While payments aren't live yet, the backend has no real `current_user.plan`
// to resolve scan depth from - so runMobileTest() also sends whichever plan
// the user picked in the UI as `selected_plan`. The backend only honors this
// during the no-payment window; once Razorpay is live it's ignored and the
// user's actual paid plan is used instead.

const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || "http://localhost:8000";
const TOKEN_STORAGE_KEY = "auth_token";

function getToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function detectPlatform(fileName = "") {
  const lower = fileName.toLowerCase();
  if (lower.endsWith(".apk")) return "android";
  if (lower.endsWith(".ipa")) return "ios";
  return null;
}

/**
 * Uploads a .apk/.ipa file and runs the static analysis scan.
 * @param {File} file
 * @param {string|null} plan - which tier to scan at ('basic' | 'standard' | 'premium').
 *   Only used pre-payment (see file header); pass the user's actual plan
 *   once they've paid and it'll be ignored server-side anyway.
 * Returns the parsed analysis JSON (overview, issues, security_score, etc).
 */
export async function runMobileTest(file, plan = null) {
  const token = getToken();

  if (!file) {
    throw new Error("Please choose an .apk or .ipa file first.");
  }

  const formData = new FormData();
  formData.append("file", file);
  if (plan) {
    formData.append("selected_plan", plan);
  }

  const response = await fetch(`${API_BASE_URL}/mobile/test`, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  if (!response.ok) {
    let message = "Could not analyze this file. Please try again.";
    try {
      const data = await response.json();
      if (typeof data.detail === "string") message = data.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(message);
  }

  return response.json();
}

/** This user's own mobile app scan history, most recent first. */
export async function getMobileHistory(limit = 20) {
  const token = getToken();

  const response = await fetch(`${API_BASE_URL}/mobile/history?limit=${limit}`, {
    method: "GET",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    let message = "Could not load mobile test history.";
    try {
      const data = await response.json();
      if (typeof data.detail === "string") message = data.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(message);
  }

  return response.json();
}

/** Re-download the PDF for one past mobile scan. Returns a Blob. */
export async function downloadMobileReport(testId) {
  const token = getToken();

  const response = await fetch(`${API_BASE_URL}/mobile/history/${testId}/download`, {
    method: "GET",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    let message = "No saved report found for this scan.";
    try {
      const data = await response.json();
      if (typeof data.detail === "string") message = data.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(message);
  }

  return response.blob();
}