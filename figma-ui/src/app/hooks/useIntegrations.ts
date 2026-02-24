import { useState, useEffect, useCallback, useRef } from "react";
import { getApiUrl, getApiHeaders } from "../config/api";

/* ─── Types ─── */

export interface ProviderStatus {
  connected: boolean;
  has_credentials: boolean;
  email: string | null;
  display_name: string | null;
}

export interface IntegrationStatus {
  google: ProviderStatus;
  microsoft: ProviderStatus;
}

export interface UseIntegrationsReturn {
  status: IntegrationStatus | null;
  loading: boolean;
  connecting: string | null; // provider currently in OAuth flow
  error: string | null;
  connectGoogle: () => Promise<void>;
  connectMicrosoft: () => Promise<void>;
  disconnectGoogle: () => Promise<void>;
  disconnectMicrosoft: () => Promise<void>;
  refresh: () => Promise<void>;
}

const DEFAULT_STATUS: IntegrationStatus = {
  google: { connected: false, has_credentials: false, email: null, display_name: null },
  microsoft: { connected: false, has_credentials: false, email: null, display_name: null },
};

/* ─── Hook ─── */

export function useIntegrations(): UseIntegrationsReturn {
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const popupRef = useRef<Window | null>(null);

  /* Fetch status from backend */
  const refresh = useCallback(async () => {
    try {
      const res = await fetch(getApiUrl("/api/integrations/status"), {
        headers: getApiHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setStatus({
          google: data.google || DEFAULT_STATUS.google,
          microsoft: data.microsoft || DEFAULT_STATUS.microsoft,
        });
      } else {
        setStatus(DEFAULT_STATUS);
      }
    } catch {
      setStatus(DEFAULT_STATUS);
    } finally {
      setLoading(false);
    }
  }, []);

  /* Fetch on mount */
  useEffect(() => {
    refresh();
  }, [refresh]);

  /* Listen for OAuth postMessage from popup */
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      const { data } = event;
      if (!data || typeof data !== "object") return;

      if (data.type === "oauth_success") {
        setConnecting(null);
        setError(null);
        refresh();
        // Close popup if still open
        if (popupRef.current && !popupRef.current.closed) {
          popupRef.current.close();
        }
        popupRef.current = null;
      } else if (data.type === "oauth_error") {
        setConnecting(null);
        setError(`OAuth failed for ${data.provider || "unknown"}: ${data.error || "Unknown error"}`);
        if (popupRef.current && !popupRef.current.closed) {
          popupRef.current.close();
        }
        popupRef.current = null;
      }
    };

    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, [refresh]);

  /* Generic connect flow */
  const connect = useCallback(
    async (provider: "google" | "microsoft") => {
      setError(null);
      setConnecting(provider);

      try {
        const res = await fetch(getApiUrl(`/api/integrations/${provider}/auth`), {
          headers: getApiHeaders(),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          const detail = errData.detail || `Failed to get auth URL for ${provider}`;
          // If credentials aren't configured, give a helpful message
          if (res.status === 400 || res.status === 404) {
            setError(`OAuth credentials not configured for ${provider}. Add client ID & secret in the backend config.`);
          } else {
            setError(detail);
          }
          setConnecting(null);
          return;
        }

        const data = await res.json();
        const authUrl = data.auth_url;

        if (!authUrl) {
          setError(`No auth URL returned for ${provider}`);
          setConnecting(null);
          return;
        }

        // Open OAuth popup
        const popup = window.open(authUrl, "oauth_popup", "width=600,height=700,scrollbars=yes");

        if (!popup) {
          setError("Popup blocked. Please allow popups for this site and try again.");
          setConnecting(null);
          return;
        }

        popupRef.current = popup;

        // Poll to detect if user closed popup manually without completing OAuth
        const pollInterval = window.setInterval(() => {
          if (popup.closed) {
            window.clearInterval(pollInterval);
            // Give a small delay for postMessage to arrive first
            setTimeout(() => {
              setConnecting((current) => {
                if (current === provider) {
                  // Popup closed but no success message received — refresh status to check
                  refresh();
                  return null;
                }
                return current;
              });
            }, 500);
          }
        }, 1000);
      } catch (err: any) {
        setError(err.message || `Failed to connect ${provider}`);
        setConnecting(null);
      }
    },
    [refresh]
  );

  /* Generic disconnect flow */
  const disconnect = useCallback(
    async (provider: "google" | "microsoft") => {
      setError(null);
      try {
        const res = await fetch(getApiUrl(`/api/integrations/${provider}/disconnect`), {
          method: "DELETE",
          headers: getApiHeaders(),
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          setError(errData.detail || `Failed to disconnect ${provider}`);
        }
      } catch (err: any) {
        setError(err.message || `Failed to disconnect ${provider}`);
      }
      await refresh();
    },
    [refresh]
  );

  return {
    status,
    loading,
    connecting,
    error,
    connectGoogle: () => connect("google"),
    connectMicrosoft: () => connect("microsoft"),
    disconnectGoogle: () => disconnect("google"),
    disconnectMicrosoft: () => disconnect("microsoft"),
    refresh,
  };
}
