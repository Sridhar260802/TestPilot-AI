// src/components/auth/GoogleSignInButton.jsx
// Renders Google's official "Continue with Google" button and forwards
// the resulting ID token to authService.googleLogin(). Used on both
// Login and Signup screens — the behavior is identical either way,
// Google handles new-account vs existing-account under the hood.

import { useEffect, useRef, useState } from "react";
import { renderGoogleButton } from "../../services/googleAuth";
import { googleLogin, AuthError } from "../../services/authService";

export default function GoogleSignInButton({ onSuccess, onError, disabled }) {
  const containerRef = useRef(null);
  const [configError, setConfigError] = useState("");
  const [exchanging, setExchanging] = useState(false);

  useEffect(() => {
    if (!containerRef.current || disabled) return;

    let cancelled = false;

    renderGoogleButton(
      containerRef.current,
      async (idToken) => {
        if (cancelled) return;
        setExchanging(true);
        try {
          const data = await googleLogin({ idToken });
          onSuccess?.(data);
        } catch (err) {
          const message =
            err instanceof AuthError
              ? err.message
              : "Google sign-in failed. Please try again.";
          onError?.(message);
        } finally {
          if (!cancelled) setExchanging(false);
        }
      },
      (err) => {
        if (!cancelled) setConfigError(err.message);
      },
      { width: 320 },
    );

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [disabled]);

  if (configError) {
    return (
      <p className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800">
        {configError}
      </p>
    );
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        ref={containerRef}
        className={disabled ? "pointer-events-none opacity-50" : ""}
        aria-label="Continue with Google"
      />
      {exchanging && <p className="text-xs text-slate-500">Signing in with Google…</p>}
    </div>
  );
}
