// src/services/googleAuth.js
//
// Wraps Google Identity Services (GIS) — the current official Google
// sign-in library — so components never talk to `window.google` directly.
// This keeps the Google-specific code isolated in one place.
//
// Docs: https://developers.google.com/identity/gsi/web/guides/overview

const GOOGLE_SCRIPT_SRC = "https://accounts.google.com/gsi/client";
const GOOGLE_CLIENT_ID = import.meta.env?.VITE_GOOGLE_CLIENT_ID;

let scriptLoadPromise = null;

/** Loads the GIS script once and caches the promise. */
function loadGoogleScript() {
  if (scriptLoadPromise) return scriptLoadPromise;

  scriptLoadPromise = new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve(window.google);
      return;
    }

    const script = document.createElement("script");
    script.src = GOOGLE_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve(window.google);
    script.onerror = () => reject(new Error("Failed to load Google Sign-In script"));
    document.head.appendChild(script);
  });

  return scriptLoadPromise;
}

/**
 * Renders the official Google "Sign in with Google" button into a DOM node.
 * @param {HTMLElement} container - element to render the button into
 * @param {(idToken: string) => void} onSuccess - called with the Google ID token
 * @param {(error: Error) => void} onError
 * @param {{ theme?: string, size?: string, text?: string, shape?: string }} [options]
 */
export async function renderGoogleButton(container, onSuccess, onError, options = {}) {
  if (!GOOGLE_CLIENT_ID) {
    onError(
      new Error(
        "Google Sign-In is not configured. Set VITE_GOOGLE_CLIENT_ID in your .env file.",
      ),
    );
    return;
  }

  try {
    const google = await loadGoogleScript();

    google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: (response) => {
        // response.credential is the Google ID token (a signed JWT).
        // We hand it to authService.googleLogin(), which sends it to
        // the backend for verification. We never decode/trust it here.
        if (response?.credential) {
          onSuccess(response.credential);
        } else {
          onError(new Error("Google did not return a credential."));
        }
      },
      ux_mode: "popup",
    });

    google.accounts.id.renderButton(container, {
      theme: options.theme || "outline",
      size: options.size || "large",
      text: options.text || "continue_with",
      shape: options.shape || "pill",
      width: options.width, // GIS ignores this if container is narrower
    });
  } catch (err) {
    onError(err instanceof Error ? err : new Error("Failed to initialize Google Sign-In"));
  }
}

/** Optional: prompts Google's One Tap UI. Call from a top-level layout if desired. */
export async function promptOneTap(onSuccess, onError) {
  if (!GOOGLE_CLIENT_ID) return;
  try {
    const google = await loadGoogleScript();
    google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: (response) => {
        if (response?.credential) onSuccess(response.credential);
      },
    });
    google.accounts.id.prompt();
  } catch (err) {
    onError?.(err instanceof Error ? err : new Error("Failed to prompt Google One Tap"));
  }
}

/** Revokes the current Google session (best-effort, client-side only). */
export function disableGoogleAutoSelect() {
  window.google?.accounts?.id?.disableAutoSelect?.();
}
