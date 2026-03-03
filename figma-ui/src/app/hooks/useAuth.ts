import { useState, useEffect, useCallback, useRef } from "react";
import { getApiUrl, getApiHeaders } from "../config/api";

export interface AuthState {
  isLoggedIn: boolean;
  email: string;
  provider: string;
  onboardingCompleted: boolean;
  loading: boolean;
  error: string | null;
  login: (provider: "google" | "microsoft") => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

export function useAuth(): AuthState {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [email, setEmail] = useState("");
  const [provider, setProvider] = useState("");
  const [onboardingCompleted, setOnboardingCompleted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const popupRef = useRef<Window | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(getApiUrl("/api/auth/status"), {
        headers: getApiHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setIsLoggedIn(data.logged_in);
        setEmail(data.email || "");
        setProvider(data.provider || "");
        setOnboardingCompleted(data.onboarding_completed || false);
      }
    } catch {
      // Backend not reachable — stay in loading/logged-out state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Listen for OAuth postMessage from popup (reuses same pattern as useIntegrations)
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      const { data } = event;
      if (!data || typeof data !== "object") return;

      if (data.type === "oauth_success") {
        // OAuth completed — now call POST /api/auth/login
        const prov = data.provider as "google" | "microsoft";
        fetch(getApiUrl("/api/auth/login"), {
          method: "POST",
          headers: getApiHeaders(),
          body: JSON.stringify({ provider: prov }),
        })
          .then((res) => res.json())
          .then(() => refresh())
          .catch((err) => setError(err.message));

        if (popupRef.current && !popupRef.current.closed) {
          popupRef.current.close();
        }
        popupRef.current = null;
      } else if (data.type === "oauth_error") {
        setError(`Login failed: ${data.error || "Unknown error"}`);
        if (popupRef.current && !popupRef.current.closed) {
          popupRef.current.close();
        }
        popupRef.current = null;
      }
    };

    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, [refresh]);

  const login = useCallback(
    async (prov: "google" | "microsoft") => {
      setError(null);
      try {
        // Get the OAuth auth URL from the backend
        const res = await fetch(getApiUrl(`/api/integrations/${prov}/auth`), {
          headers: getApiHeaders(),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          setError(errData.detail || `Failed to get auth URL for ${prov}`);
          return;
        }

        const data = await res.json();
        const authUrl = data.auth_url;

        if (!authUrl) {
          setError(`No auth URL returned for ${prov}`);
          return;
        }

        // Open OAuth popup
        const popup = window.open(authUrl, "oauth_login", "width=600,height=700,scrollbars=yes");

        if (!popup) {
          setError("Popup blocked. Please allow popups and try again.");
          return;
        }

        popupRef.current = popup;

        // Poll for popup close
        const pollInterval = window.setInterval(() => {
          if (popup.closed) {
            window.clearInterval(pollInterval);
            setTimeout(() => refresh(), 500);
          }
        }, 1000);
      } catch (err: any) {
        setError(err.message || `Failed to login with ${prov}`);
      }
    },
    [refresh]
  );

  const logout = useCallback(async () => {
    try {
      await fetch(getApiUrl("/api/auth/logout"), {
        method: "POST",
        headers: getApiHeaders(),
      });
      setIsLoggedIn(false);
      setEmail("");
      setProvider("");
      setOnboardingCompleted(false);
    } catch (err: any) {
      setError(err.message || "Logout failed");
    }
  }, []);

  return {
    isLoggedIn,
    email,
    provider,
    onboardingCompleted,
    loading,
    error,
    login,
    logout,
    refresh,
  };
}
