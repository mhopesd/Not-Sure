import { useState } from "react";
import { Minus, Square, X } from "lucide-react";

interface WindowFrameProps {
  children: React.ReactNode;
  title?: string;
}

export function WindowFrame({ children, title = "NotSure" }: WindowFrameProps) {
  const [isMaximized, setIsMaximized] = useState(true);

  return (
    <div
      className={`flex flex-col bg-[#111114] overflow-hidden ${
        isMaximized
          ? "w-full h-screen rounded-none"
          : "w-[960px] h-[640px] rounded-xl mx-auto mt-8"
      }`}
      style={{
        boxShadow: isMaximized
          ? "none"
          : "0 40px 120px rgba(0,0,0,0.8), 0 0 1px rgba(255,255,255,0.1)",
        border: isMaximized ? "none" : "1px solid rgba(255,255,255,0.06)",
      }}
    >
      {/* Title Bar */}
      <div
        className="h-[38px] flex items-center px-3 shrink-0 select-none"
        style={{
          background: "rgba(24, 24, 28, 0.95)",
          borderBottom: "1px solid rgba(255,255,255,0.04)",
        }}
      >
        {/* Traffic Lights */}
        <div className="flex items-center gap-[7px] group">
          <button className="w-3 h-3 rounded-full bg-[#ff5f57] flex items-center justify-center hover:brightness-110 transition-all">
            <X size={7} className="text-[#4a0002] opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
          <button className="w-3 h-3 rounded-full bg-[#febc2e] flex items-center justify-center hover:brightness-110 transition-all">
            <Minus size={7} className="text-[#5a3e00] opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
          <button
            onClick={() => setIsMaximized(!isMaximized)}
            className="w-3 h-3 rounded-full bg-[#28c840] flex items-center justify-center hover:brightness-110 transition-all"
          >
            <Square size={5} className="text-[#0a4a12] opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
        </div>

        {/* Window Title */}
        <div className="flex-1 flex items-center justify-center gap-2">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" className="opacity-40">
            <circle cx="8" cy="8" r="5" stroke="white" strokeWidth="1.5" fill="none" />
            <circle cx="8" cy="8" r="2" fill="white" />
          </svg>
          <span className="text-[12px] text-white/35">{title}</span>
        </div>

        {/* Spacer for centering */}
        <div className="w-[52px]" />
      </div>

      {/* Window Content */}
      <div className="flex-1 overflow-hidden">
        {children}
      </div>
    </div>
  );
}
