import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Mic,
  Square,
  Pause,
  Play,
  LayoutDashboard,
  Settings,
  ChevronDown,
  Circle,
} from "lucide-react";
import { AudioVisualizer } from "./AudioVisualizer";
import { LiveTranscript } from "./LiveTranscript";
import { RecentMeetings } from "./RecentMeetings";

type TrayState = "idle" | "recording" | "paused";

export function MenuBarTray() {
  const [isOpen, setIsOpen] = useState(true);
  const [trayState, setTrayState] = useState<TrayState>("idle");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Timer logic
  useEffect(() => {
    if (trayState !== "recording") return;
    const interval = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [trayState]);

  const formatTime = (totalSeconds: number) => {
    const hrs = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    if (hrs > 0) {
      return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    }
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const handleStartRecording = useCallback(() => {
    setTrayState("recording");
    setElapsedSeconds(0);
  }, []);

  const handleStopRecording = useCallback(() => {
    setTrayState("idle");
    setElapsedSeconds(0);
  }, []);

  const handlePause = useCallback(() => {
    setTrayState("paused");
  }, []);

  const handleResume = useCallback(() => {
    setTrayState("recording");
  }, []);

  return (
    <div className="relative">
      {/* Menu Bar Tray Icon */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-2 py-1 rounded-md hover:bg-white/10 transition-colors"
      >
        {/* NotSure Icon */}
        <div className="relative">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="6" stroke="white" strokeWidth="1.5" fill="none" opacity={0.9} />
            <circle cx="8" cy="8" r="2.5" fill="#2774AE" />
          </svg>
          {trayState === "recording" && (
            <motion.div
              className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-red-500"
              animate={{ scale: [1, 1.3, 1], opacity: [1, 0.7, 1] }}
              transition={{ duration: 1.2, repeat: Infinity }}
            />
          )}
          {trayState === "paused" && (
            <div className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-yellow-500" />
          )}
        </div>
        <span className="text-[12px] text-white/80">NotSure</span>
        <ChevronDown
          size={10}
          className={`text-white/50 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      {/* Tray Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.98 }}
            transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
            className="absolute right-0 top-[calc(100%+8px)] w-[340px] rounded-xl overflow-hidden"
            style={{
              background: "linear-gradient(180deg, rgba(22, 22, 26, 0.97) 0%, rgba(18, 18, 22, 0.99) 100%)",
              boxShadow:
                "0 24px 80px rgba(0,0,0,0.6), 0 0 1px rgba(255,255,255,0.1), inset 0 1px 0 rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.08)",
              backdropFilter: "blur(40px)",
            }}
          >
            {/* Tray Header */}
            <div className="px-4 pt-4 pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className="relative w-7 h-7 rounded-lg flex items-center justify-center"
                    style={{
                      background:
                        trayState === "recording"
                          ? "linear-gradient(135deg, #2774AE, #c0392b)"
                          : trayState === "paused"
                          ? "linear-gradient(135deg, #2774AE, #7f6b00)"
                          : "linear-gradient(135deg, #2774AE, #1a5a8e)",
                      boxShadow:
                        trayState === "recording"
                          ? "0 0 8px rgba(239,68,68,0.35)"
                          : trayState === "paused"
                          ? "0 0 6px rgba(234,179,8,0.25)"
                          : "0 0 6px rgba(39,116,174,0.2)",
                      transition: "background 0.4s ease, box-shadow 0.4s ease",
                    }}
                  >
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                      <circle
                        cx="8"
                        cy="8"
                        r="5.5"
                        stroke="white"
                        strokeWidth="1"
                        fill="none"
                        opacity={0.35}
                      />
                      <circle
                        cx="8"
                        cy="8"
                        r="4"
                        stroke="white"
                        strokeWidth="1.2"
                        fill="none"
                        opacity={0.8}
                      />
                      <circle
                        cx="8"
                        cy="8"
                        r="1.8"
                        fill={
                          trayState === "recording"
                            ? "#ef4444"
                            : trayState === "paused"
                            ? "#eab308"
                            : "white"
                        }
                        style={{ transition: "fill 0.3s ease" }}
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-[13px] text-white/95">NotSure</h3>
                    <span className="text-[10px] text-white/35">
                      {trayState === "idle"
                        ? "Ready to record"
                        : trayState === "recording"
                        ? "Recording in progress"
                        : "Recording paused"}
                    </span>
                  </div>
                </div>
                <button className="p-1.5 rounded-md hover:bg-white/[0.06] transition-colors">
                  <Settings size={13} className="text-white/40" />
                </button>
              </div>
            </div>

            <div className="h-px bg-white/[0.06] mx-3" />

            {/* Content Area */}
            <div className="px-4 py-3">
              <AnimatePresence mode="wait">
                {trayState === "idle" ? (
                  <motion.div
                    key="idle"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                  >
                    {/* Start Recording Button */}
                    <button
                      onClick={handleStartRecording}
                      className="w-full group relative overflow-hidden rounded-xl p-[1px] mb-4"
                    >
                      <div
                        className="absolute inset-0 rounded-xl opacity-80 group-hover:opacity-100 transition-opacity"
                        style={{
                          background:
                            "linear-gradient(135deg, #2774AE, #1a5a8e, #2774AE)",
                        }}
                      />
                      <div className="relative flex items-center justify-center gap-2.5 py-3.5 px-4 rounded-[11px] bg-gradient-to-b from-[#2774AE] to-[#1f6699] group-hover:from-[#2e80ba] group-hover:to-[#2774AE] transition-all">
                        <div className="w-8 h-8 rounded-full bg-white/15 flex items-center justify-center group-hover:bg-white/20 transition-colors">
                          <Mic size={16} className="text-white" />
                        </div>
                        <div className="text-left">
                          <div className="text-[13px] text-white">
                            Start Recording
                          </div>
                          <div className="text-[10px] text-white/50">
                            Microphone + System Audio
                          </div>
                        </div>
                        <div className="ml-auto">
                          <div className="text-[10px] text-white/30 bg-white/10 rounded px-1.5 py-0.5 font-mono">
                            ⌘R
                          </div>
                        </div>
                      </div>
                    </button>

                    {/* Recent Meetings */}
                    <RecentMeetings />
                  </motion.div>
                ) : (
                  <motion.div
                    key="recording"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="space-y-3"
                  >
                    {/* Recording Status */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {trayState === "recording" ? (
                          <motion.div
                            animate={{
                              scale: [1, 1.2, 1],
                              opacity: [1, 0.6, 1],
                            }}
                            transition={{ duration: 1.5, repeat: Infinity }}
                          >
                            <Circle
                              size={10}
                              fill="#ef4444"
                              className="text-red-500"
                            />
                          </motion.div>
                        ) : (
                          <Circle
                            size={10}
                            fill="#eab308"
                            className="text-yellow-500"
                          />
                        )}
                        <span className="text-[12px] text-white/70">
                          {trayState === "recording" ? "Recording" : "Paused"}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span
                          className="font-mono text-[18px] tracking-wider"
                          style={{
                            color:
                              trayState === "recording" ? "#FFD100" : "#eab308",
                          }}
                        >
                          {formatTime(elapsedSeconds)}
                        </span>
                      </div>
                    </div>

                    {/* Audio Visualizer */}
                    <div
                      className="rounded-lg p-3"
                      style={{ backgroundColor: "rgba(255,255,255,0.03)" }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] text-white/30 uppercase tracking-wider">
                          Audio Level
                        </span>
                        <div className="flex items-center gap-1">
                          <Mic size={9} className="text-[#2774AE]" />
                          <span className="text-[10px] text-[#2774AE]">
                            Active
                          </span>
                        </div>
                      </div>
                      <AudioVisualizer
                        isActive={trayState === "recording"}
                        barCount={32}
                        height={36}
                      />
                    </div>

                    {/* Recording Controls */}
                    <div className="flex items-center gap-2">
                      {trayState === "recording" ? (
                        <button
                          onClick={handlePause}
                          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] transition-colors"
                        >
                          <Pause size={14} className="text-white/70" />
                          <span className="text-[12px] text-white/70">
                            Pause
                          </span>
                        </button>
                      ) : (
                        <button
                          onClick={handleResume}
                          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] transition-colors"
                        >
                          <Play size={14} className="text-[#2774AE]" />
                          <span className="text-[12px] text-[#2774AE]">
                            Resume
                          </span>
                        </button>
                      )}
                      <button
                        onClick={handleStopRecording}
                        className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 transition-colors border border-red-500/20"
                      >
                        <Square size={12} fill="#ef4444" className="text-red-500" />
                        <span className="text-[12px] text-red-400">
                          Stop
                        </span>
                      </button>
                    </div>

                    {/* Live Transcript Section */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] text-white/30 uppercase tracking-wider">
                          Live Transcript
                        </span>
                        <div className="flex items-center gap-1">
                          <motion.div
                            className="w-1 h-1 rounded-full bg-green-500"
                            animate={{ opacity: [1, 0.3, 1] }}
                            transition={{ duration: 2, repeat: Infinity }}
                          />
                          <span className="text-[10px] text-green-500/70">
                            AI Active
                          </span>
                        </div>
                      </div>
                      <div
                        className="rounded-lg p-2.5"
                        style={{ backgroundColor: "rgba(255,255,255,0.03)" }}
                      >
                        <LiveTranscript
                          isActive={trayState === "recording"}
                          elapsedSeconds={elapsedSeconds}
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="h-px bg-white/[0.06] mx-3" />

            {/* Tray Footer */}
            <div className="px-4 py-2.5 flex items-center justify-between">
              <button className="flex items-center gap-2 py-1.5 px-2.5 rounded-lg hover:bg-white/[0.06] transition-colors">
                <LayoutDashboard size={13} className="text-white/40" />
                <span className="text-[12px] text-white/50 hover:text-white/70 transition-colors">
                  Open Dashboard
                </span>
              </button>
              <span className="text-[9px] text-white/20 font-mono">v1.2.0</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}