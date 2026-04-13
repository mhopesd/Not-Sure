import { createBrowserRouter, redirect } from "react-router";
import { RootLayout } from "./components/RootLayout";
import { DashboardPage } from "./components/DashboardPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, loader: () => redirect("/dashboard") },
      { path: "dashboard", Component: DashboardPage },
    ],
  },
]);
