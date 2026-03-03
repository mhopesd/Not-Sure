import { useEffect } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../hooks/useAuth";
import { Loader2 } from "lucide-react";

const imgCanvas =
  "data:image/svg+xml," +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#1a1a2e"/><text x="32" y="40" text-anchor="middle" font-size="28" fill="#FFD100" font-family="sans-serif">?</text></svg>'
  );

export function LoginPage() {
  const navigate = useNavigate();
  const auth = useAuth();

  // If already logged in, redirect
  useEffect(() => {
    if (!auth.loading && auth.isLoggedIn) {
      navigate(auth.onboardingCompleted ? "/dashboard" : "/onboarding");
    }
  }, [auth.loading, auth.isLoggedIn, auth.onboardingCompleted, navigate]);

  if (auth.loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="text-white/30 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center h-full">
      <div className="flex flex-col items-center max-w-sm w-full px-8">
        {/* Logo */}
        <div className="w-14 h-14 rounded-2xl overflow-hidden mb-4">
          <img src={imgCanvas} alt="NotSure" className="w-full h-full" />
        </div>

        <h1 className="text-white/90 text-lg font-medium mb-1">Welcome to NotSure</h1>
        <p className="text-white/40 text-[12px] text-center mb-8">
          AI-powered meeting assistant. Sign in to get started.
        </p>

        {/* Sign-in buttons */}
        <div className="w-full space-y-3">
          <button
            onClick={() => auth.login("google")}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl text-[13px] font-medium transition-all hover:brightness-110"
            style={{
              background: "rgba(66,133,244,0.12)",
              color: "#8ab4f8",
              border: "1px solid rgba(66,133,244,0.2)",
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Sign in with Google
          </button>

          <button
            onClick={() => auth.login("microsoft")}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl text-[13px] font-medium transition-all hover:brightness-110"
            style={{
              background: "rgba(0,120,212,0.12)",
              color: "#60b0f4",
              border: "1px solid rgba(0,120,212,0.2)",
            }}
          >
            <svg width="16" height="16" viewBox="0 0 21 21" fill="none">
              <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
              <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
              <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
              <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
            </svg>
            Sign in with Microsoft
          </button>
        </div>

        {auth.error && (
          <p className="mt-4 text-[11px] text-red-400/80 text-center">{auth.error}</p>
        )}

        <p className="mt-8 text-[10px] text-white/20 text-center leading-relaxed">
          Audio is processed locally on your device.<br />
          Your data never leaves your machine without consent.
        </p>
      </div>
    </div>
  );
}
