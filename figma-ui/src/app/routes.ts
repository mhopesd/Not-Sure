import { createBrowserRouter } from "react-router";
import { RootLayout } from "./components/RootLayout";
import { LoginPage } from "./components/LoginPage";
import { OnboardingPage } from "./components/OnboardingPage";
import { DashboardPage } from "./components/DashboardPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, Component: LoginPage },
      { path: "login", Component: LoginPage },
      { path: "onboarding", Component: OnboardingPage },
      { path: "dashboard", Component: DashboardPage },
    ],
  },
]);
