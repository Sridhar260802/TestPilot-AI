// src/hooks/useAuth.js
//
// Optional convenience hook so other parts of the app (e.g. a Navbar or
// a ProtectedRoute wrapper) can read auth state without importing
// authService directly everywhere. Not required by the Login/Signup
// pages themselves — purely a nice-to-have for the rest of your app.
//
// Example ProtectedRoute usage:
//
//   function ProtectedRoute({ children }) {
//     const { isAuthenticated } = useAuth();
//     return isAuthenticated ? children : <Navigate to="/login" replace />;
//   }

import { useCallback, useState } from "react";
import { getStoredUser, isAuthenticated as checkIsAuthenticated, logout as logoutService } from "../services/authService";

export function useAuth() {
  const [user, setUser] = useState(() => getStoredUser());

  const refresh = useCallback(() => {
    setUser(getStoredUser());
  }, []);

  const logout = useCallback(async () => {
    await logoutService();
    setUser(null);
  }, []);

  return {
    user,
    isAuthenticated: checkIsAuthenticated(),
    refresh,
    logout,
  };
}

export default useAuth;
