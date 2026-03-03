import { useEffect } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../hooks/useAuth";
import { OnboardingWizard } from "./OnboardingWizard";
import { getApiUrl, getApiHeaders } from "../config/api";
import { Loader2 } from "lucide-react";

export function OnboardingPage() {
  const navigate = useNavigate();
  const auth = useAuth();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!auth.loading && !auth.isLoggedIn) {
      navigate("/login");
    }
  }, [auth.loading, auth.isLoggedIn, navigate]);

  if (auth.loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="text-white/30 animate-spin" />
      </div>
    );
  }

  const handleComplete = async () => {
    try {
      await fetch(getApiUrl("/api/onboarding/complete"), {
        method: "POST",
        headers: getApiHeaders(),
      });
    } catch {
      // Non-critical — navigate anyway
    }
    navigate("/dashboard");
  };

  return <OnboardingWizard onComplete={handleComplete} />;
}
