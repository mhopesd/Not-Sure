import { useEffect } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../hooks/useAuth";
import { DashboardLayout } from "./DashboardLayout";
import { Loader2 } from "lucide-react";

export function DashboardPage() {
  const navigate = useNavigate();
  const auth = useAuth();

  useEffect(() => {
    if (!auth.loading) {
      if (!auth.isLoggedIn) {
        navigate("/login");
      } else if (!auth.onboardingCompleted) {
        navigate("/onboarding");
      }
    }
  }, [auth.loading, auth.isLoggedIn, auth.onboardingCompleted, navigate]);

  if (auth.loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="text-white/30 animate-spin" />
      </div>
    );
  }

  return <DashboardLayout />;
}
