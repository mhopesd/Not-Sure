import { Outlet } from "react-router";
import { WindowFrame } from "./WindowFrame";
import { HelpButton } from "./HelpButton";
import { ErrorBoundary } from "./ErrorBoundary";

export function RootLayout() {
  return (
    <div className="w-full h-screen bg-[#0e0e10]">
      <WindowFrame>
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </WindowFrame>
      <HelpButton />
    </div>
  );
}