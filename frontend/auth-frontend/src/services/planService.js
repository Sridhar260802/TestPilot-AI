const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const TOKEN_STORAGE_KEY = "auth_token";

function getToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

async function generateReport(endpoint, url) {
  const token = getToken();

  if (!url || !url.trim()) {
    throw new Error("Please enter a website URL.");
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {}),
    },
    body: JSON.stringify({
      url: url.trim(),
    }),
  });

  if (!response.ok) {
    let errorMessage = "Failed to generate report.";

    try {
      const errorData = await response.json();

      if (typeof errorData.detail === "string") {
        errorMessage = errorData.detail;
      }
    } catch {
      // Response was not JSON
    }

    throw new Error(errorMessage);
  }

  // Backend returns PDF
  const blob = await response.blob();

  return blob;
}


// -----------------------------
// BASIC
// -----------------------------

export async function generateBasicReport(url) {
  return generateReport(
    "/plans/basic/report",
    url
  );
}


// -----------------------------
// STANDARD
// -----------------------------

export async function generateStandardReport(url) {
  return generateReport(
    "/plans/standard/report",
    url
  );
}


// -----------------------------
// PREMIUM
// -----------------------------

export async function generatePremiumReport(url) {
  return generateReport(
    "/plans/premium/report",
    url
  );
}