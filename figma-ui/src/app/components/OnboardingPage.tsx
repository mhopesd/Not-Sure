import { useNavigate } from "react-router";
import { OnboardingWizard } from "./OnboardingWizard";

export function OnboardingPage() {
  const navigate = useNavigate();

  return (
    <OnboardingWizard onComplete={() => navigate("/dashboard")} />
  );
}
