import { createBrowserRouter } from "react-router";
import { RootLayout } from "./components/RootLayout";
import { OnboardingPage } from "./components/OnboardingPage";
import { DashboardPage } from "./components/DashboardPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, Component: OnboardingPage },
      { path: "dashboard", Component: DashboardPage },
    ],
  },
]);
