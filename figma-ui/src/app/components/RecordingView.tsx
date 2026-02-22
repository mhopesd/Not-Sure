import { useState, useEffect, useRef, useCallback } from "react";
import {
  Mic,
  MicOff,
  Pause,
  Play,
  Square,
  Clock,
  FileText,
  Sparkles,
  Zap,
  Users,
  ChevronDown,
  Volume2,
  Radio,
  Flag,
  UserCheck,
  UserX,
  Pencil,
  Check,
  CheckCircle2,
  Lightbulb,
} from "lucide-react";
import { getApiUrl, getApiHeaders, getWebSocketUrl } from "../config/api";

const ICON_COL = "w-8 h-8 shrink-0 rounded-lg flex items-center justify-center";

interface TranscriptSegment {
  speaker: string;
  text: string;
  color: string;
  identified: boolean;
  timestamp: string;
}

interface LiveInsights {
  key_points: string[];
  topic: string;
  meeting_type?: string;
  confidence?: number;
  action_items?: { text: string; assignee: string | null }[];
  decisions?: string[];
  sentiment?: string;
  suggested_questions?: string[];
}

interface AudioDevice {
  id: string;
  name: string;
  type: string;
}

interface RecordingViewProps {
  onStop: () => void;
}

const SPEAKER_COLORS = ["#2774AE", "#6dd58c", "#FFD100", "#8b5cf6", "#f97316", "#ef4444", "#c084fc", "#22d3ee"];

export function RecordingView({ onStop }: RecordingViewProps) {
  const [status, setStatus] = useState<"idle" | "recording" | "paused" | "processing">("idle");
  const [elapsed, setElapsed] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [showTranscript, setShowTranscript] = useState(true);
  const [flagCount, setFlagCount] = useState(0);
  const [meetingTitle, setMeetingTitle] = useState("");
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [liveInsights, setLiveInsights] = useState<LiveInsights | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [devices, setDevices] = useState<AudioDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>("microphone");
  const [showDeviceMenu, setShowDeviceMenu] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [speakerLabels, setSpeakerLabels] = useState<Record<string, string>>({});
  const [editingSpeaker, setEditingSpeaker] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const durationIntervalRef = useRef<number | null>(null);
  const speakerColorMap = useRef<Record<string, string>>({});
  const speakerColorIdx = useRef(0);
  const elapsedRef = useRef(0);
  const onStopRef = useRef(onStop);

  const getSpeakerColor = (speaker: string) => {
    if (!speakerColorMap.current[speaker]) {
      speakerColorMap.current[speaker] = SPEAKER_COLORS[speakerColorIdx.current % SPEAKER_COLORS.length];
      speakerColorIdx.current++;
    }
    return speakerColorMap.current[speaker];
  };

  // Keep refs in sync
  useEffect(() => { elapsedRef.current = elapsed; }, [elapsed]);
  useEffect(() => { onStopRef.current = onStop; }, [onStop]);

  // Fetch available devices on mount
  useEffect(() => {
    async function fetchDevices() {
      try {
        const response = await fetch(getApiUrl("/api/devices"), { headers: getApiHeaders() });
        if (response.ok) {
          const data = await response.json();
          const devs: AudioDevice[] = [];
          if (data.microphone) devs.push({ id: "microphone", name: data.microphone.name || "Microphone", type: "microphone" });
          if (data.system_audio) devs.push({ id: "system_audio", name: data.system_audio.name || "System Audio", type: "system_audio" });
          if (data.hybrid) devs.push({ id: "hybrid", name: data.hybrid.name || "Hybrid", type: "hybrid" });
          setDevices(devs);
          if (devs.length > 0) setSelectedDevice(devs[0].id);
        }
      } catch (err) {
        console.error("Failed to fetch devices:", err);
      }
    }
    fetchDevices();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (durationIntervalRef.current) clearInterval(durationIntervalRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket(getWebSocketUrl());

      ws.onopen = () => console.log("WebSocket connected");

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          switch (message.type) {
            case "transcript_update":
              if (message.text) {
                const speaker = message.speaker || "Speaker";
                setSegments((prev) => [
                  ...prev,
                  {
                    speaker,
                    text: message.text,
                    color: getSpeakerColor(speaker),
                    identified: speaker !== "Speaker" && !speaker.startsWith("Speaker "),
                    timestamp: formatTime(elapsedRef.current),
                  },
                ]);
              }
              break;
            case "audio_level":
              setAudioLevel(message.value || 0);
              break;
            case "live_summary":
              if (message.data) setLiveInsights(message.data);
              break;
            case "status":
              if (message.status === "processing") setStatus("processing");
              else if (message.status === "complete") {
                setStatus("idle");
                onStopRef.current();
              }
              break;
          }
        } catch (err) {
          console.error("WS parse error:", err);
        }
      };

      ws.onerror = (error) => console.error("WebSocket error:", error);
      ws.onclose = () => console.log("WebSocket disconnected");

      wsRef.current = ws;
    } catch (err) {
      console.error("Failed to connect WebSocket:", err);
    }
  }, []);

  const startRecording = async () => {
    setError(null);
    try {
      connectWebSocket();

      const response = await fetch(getApiUrl("/api/recordings/start"), {
        method: "POST",
        headers: getApiHeaders(),
        body: JSON.stringify({
          device: selectedDevice,
          title: meetingTitle || undefined,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to start recording");
      }

      setStatus("recording");
      setElapsed(0);
      setSegments([]);
      setLiveInsights(null);

      durationIntervalRef.current = window.setInterval(() => {
        setElapsed((p) => p + 1);
      }, 1000);
    } catch (err: any) {
      setError(err.message || "Failed to start recording");
      setStatus("idle");
    }
  };

  const stopRecording = async () => {
    if (durationIntervalRef.current) clearInterval(durationIntervalRef.current);

    try {
      await fetch(getApiUrl("/api/recordings/stop"), {
        method: "POST",
        headers: getApiHeaders(),
      });
      setStatus("processing");
    } catch (err: any) {
      setError(err.message || "Failed to stop recording");
    }
  };

  // Derive detected speakers from segments
  const detectedSpeakers = (() => {
    const seen = new Map<string, { speaker: string; color: string; identified: boolean; count: number }>();
    segments.forEach((seg) => {
      const key = seg.speaker;
      if (seen.has(key)) {
        seen.get(key)!.count++;
      } else {
        seen.set(key, { speaker: key, color: seg.color, identified: seg.identified, count: 1 });
      }
    });
    return Array.from(seen.values());
  })();

  const identifiedCount = detectedSpeakers.filter((s) => s.identified).length;
  const unidentifiedCount = detectedSpeakers.filter((s) => !s.identified).length;
  const totalSpeakers = detectedSpeakers.length;

  const getSpeakerDisplayName = (original: string) => speakerLabels[original] || original;

  const startEditSpeaker = (speakerKey: string) => {
    setEditingSpeaker(speakerKey);
    setEditValue(speakerLabels[speakerKey] || "");
  };

  const confirmEditSpeaker = (speakerKey: string) => {
    if (editValue.trim()) {
      setSpeakerLabels((prev) => ({ ...prev, [speakerKey]: editValue.trim() }));
    }
    setEditingSpeaker(null);
    setEditValue("");
  };

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [segments]);

  // Waveform canvas
  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const isActive = status === "recording" && !isMuted;
    const barCount = 80;
    const barWidth = 3;
    const gap = (w - barCount * barWidth) / (barCount - 1);

    for (let i = 0; i < barCount; i++) {
      const x = i * (barWidth + gap);
      const realLevel = audioLevel || 0;
      const amplitude = isActive
        ? Math.sin(Date.now() / 200 + i * 0.3) * 0.3 * (0.5 + realLevel) +
          Math.sin(Date.now() / 400 + i * 0.7) * 0.2 +
          Math.random() * 0.1 * (0.3 + realLevel) +
          0.05 + realLevel * 0.3
        : 0.05 + Math.sin(i * 0.5) * 0.02;

      const barH = amplitude * h * 0.8;
      const y = (h - barH) / 2;

      const gradient = ctx.createLinearGradient(x, y, x, y + barH);
      if (isActive) {
        gradient.addColorStop(0, "rgba(39, 116, 174, 0.8)");
        gradient.addColorStop(0.5, "rgba(39, 116, 174, 0.5)");
        gradient.addColorStop(1, "rgba(39, 116, 174, 0.2)");
      } else {
        gradient.addColorStop(0, "rgba(255, 255, 255, 0.08)");
        gradient.addColorStop(1, "rgba(255, 255, 255, 0.03)");
      }

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.roundRect(x, y, barWidth, barH, 1.5);
      ctx.fill();
    }

    animationRef.current = requestAnimationFrame(drawWaveform);
  }, [status, isMuted, audioLevel]);

  useEffect(() => {
    animationRef.current = requestAnimationFrame(drawWaveform);
    return () => cancelAnimationFrame(animationRef.current);
  }, [drawWaveform]);

  const handleStop = () => {
    stopRecording();
  };

  // ── Idle state: show title input + start button ──
  if (status === "idle") {
    return (
      <div className="flex flex-col h-full items-center justify-center" style={{ background: "linear-gradient(180deg, #0f0f13 0%, #111116 100%)" }}>
        <div className="max-w-md w-full space-y-6 px-8">
          <div className="text-center">
            <h2 className="text-white/80 mb-1">Start Recording</h2>
            <p className="text-[12px] text-white/30">Record and transcribe your meeting in real-time</p>
          </div>

          <input
            type="text"
            value={meetingTitle}
            onChange={(e) => setMeetingTitle(e.target.value)}
            placeholder="Meeting title (optional)"
            className="w-full px-4 py-3 rounded-lg text-[13px] text-white/70 placeholder:text-white/20 outline-none"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}
          />

          {/* Device selector */}
          {devices.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setShowDeviceMenu(!showDeviceMenu)}
                className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-[11px] text-white/40 transition-colors"
                style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}
              >
                <Radio size={10} />
                {devices.find((d) => d.id === selectedDevice)?.name || "Select device"}
                <ChevronDown size={10} className="ml-auto" />
              </button>
              {showDeviceMenu && (
                <div className="absolute top-full left-0 right-0 mt-1 rounded-lg overflow-hidden z-10" style={{ background: "#1a1a1e", border: "1px solid rgba(255,255,255,0.06)" }}>
                  {devices.map((d) => (
                    <button
                      key={d.id}
                      onClick={() => { setSelectedDevice(d.id); setShowDeviceMenu(false); }}
                      className="w-full text-left px-3 py-2 text-[11px] text-white/50 hover:bg-white/[0.04] transition-colors"
                    >
                      {d.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          <button
            onClick={startRecording}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-white font-medium transition-all hover:brightness-110"
            style={{ background: "linear-gradient(135deg, #2774AE, #1a5a8e)", boxShadow: "0 4px 16px rgba(39,116,174,0.3)" }}
          >
            <Mic size={16} />
            Start Recording
          </button>

          {error && (
            <div className="p-3 rounded-lg text-[12px] text-red-400" style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.15)" }}>
              {error}
            </div>
          )}

          <button onClick={onStop} className="w-full text-center text-[11px] text-white/25 hover:text-white/40 transition-colors py-2">
            Cancel
          </button>
        </div>
      </div>
    );
  }

  // ── Processing state ──
  if (status === "processing") {
    return (
      <div className="flex flex-col h-full items-center justify-center" style={{ background: "linear-gradient(180deg, #0f0f13 0%, #111116 100%)" }}>
        <div className="text-center space-y-4">
          <div className="w-12 h-12 border-2 border-[#2774AE] border-t-transparent rounded-full animate-spin mx-auto" />
          <h2 className="text-white/80">Processing Recording</h2>
          <p className="text-[12px] text-white/30">Transcribing and generating summary...</p>
        </div>
      </div>
    );
  }

  // ── Recording / Paused state ──
  return (
    <div className="flex flex-col h-full" style={{ background: "linear-gradient(180deg, #0f0f13 0%, #111116 100%)" }}>
      {/* ─── Top Bar ─── */}
      <div
        className="flex items-center justify-between px-5 h-[40px] shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}
      >
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div
              className="w-2 h-2 rounded-full"
              style={{
                background: status === "recording" ? "#ef4444" : "#FFD100",
                boxShadow: status === "recording" ? "0 0 8px rgba(239,68,68,0.4)" : "none",
                animation: status === "recording" ? "pulse 1.5s ease-in-out infinite" : "none",
              }}
            />
            <span className="text-[11px]" style={{ color: status === "recording" ? "#ef4444" : "#FFD100" }}>
              {status === "recording" ? "Recording" : "Paused"}
            </span>
          </div>
          <span className="text-[10px] text-white/15">·</span>
          <span className="text-[13px] text-white/60 font-mono tabular-nums">{formatTime(elapsed)}</span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setFlagCount((p) => p + 1)}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors hover:bg-white/[0.04]"
            style={{ color: flagCount > 0 ? "#FFD100" : "rgba(255,255,255,0.25)" }}
          >
            <Flag size={10} />
            {flagCount > 0 && <span>{flagCount}</span>}
          </button>
          <button
            onClick={() => setShowTranscript(!showTranscript)}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] text-white/25 hover:text-white/45 transition-colors hover:bg-white/[0.04]"
          >
            <FileText size={10} />
            Transcript
          </button>
        </div>
      </div>

      {/* ─── Main Content ─── */}
      <div className="flex-1 flex min-h-0">
        {/* Center: Waveform + Controls */}
        <div className="flex-1 flex flex-col items-center justify-center px-8">
          <div className="text-center mb-6">
            <h2 className="text-white/80 mb-1">{meetingTitle || "New Meeting"}</h2>
            <div className="flex items-center justify-center gap-2 text-[10px] text-white/25">
              <span className="flex items-center gap-1">
                <Users size={9} /> {totalSpeakers} voice{totalSpeakers !== 1 ? "s" : ""} detected
                {unidentifiedCount > 0 && <span className="text-[#f97316]">({unidentifiedCount} unknown)</span>}
              </span>
              <span className="text-white/10">·</span>
              <span className="flex items-center gap-1"><Clock size={9} /> Started {formatTime(elapsed)} ago</span>
            </div>
          </div>

          {/* Live Insights */}
          {liveInsights && liveInsights.key_points && liveInsights.key_points.length > 0 && (
            <div className="w-full max-w-md mb-4 p-3 rounded-xl space-y-2" style={{ background: "rgba(39,116,174,0.06)", border: "1px solid rgba(39,116,174,0.12)" }}>
              <div className="flex items-center gap-1.5">
                <Sparkles size={10} className="text-[#FFD100]" />
                <span className="text-[10px] text-white/50">Live Insights</span>
                {liveInsights.topic && <span className="text-[9px] text-[#FFD100] bg-[#FFD100]/10 px-1.5 py-0.5 rounded">{liveInsights.topic}</span>}
              </div>
              <ul className="space-y-1">
                {liveInsights.key_points.slice(0, 3).map((point, idx) => (
                  <li key={idx} className="flex items-start gap-1.5 text-[10px] text-white/40">
                    <span className="text-[#FFD100] mt-0.5">•</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
              {liveInsights.action_items && liveInsights.action_items.length > 0 && (
                <div className="pt-1 border-t border-white/5">
                  <div className="flex items-center gap-1 mb-1">
                    <CheckCircle2 size={8} className="text-green-400" />
                    <span className="text-[8px] text-green-400 uppercase">Actions</span>
                  </div>
                  {liveInsights.action_items.slice(0, 2).map((item, idx) => (
                    <div key={idx} className="text-[9px] text-white/35 ml-3">☐ {item.text}</div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Waveform */}
          <div
            className="w-full max-w-md mb-8 rounded-xl p-4"
            style={{ background: "rgba(255,255,255,0.015)", border: "1px solid rgba(255,255,255,0.03)" }}
          >
            <canvas ref={canvasRef} width={400} height={80} className="w-full h-[80px]" />
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsMuted(!isMuted)}
              className="w-10 h-10 rounded-xl flex items-center justify-center transition-all"
              style={{
                background: isMuted ? "rgba(239,68,68,0.12)" : "rgba(255,255,255,0.04)",
                border: `1px solid ${isMuted ? "rgba(239,68,68,0.2)" : "rgba(255,255,255,0.06)"}`,
              }}
            >
              {isMuted ? <MicOff size={16} className="text-[#ef4444]" /> : <Mic size={16} className="text-white/40" />}
            </button>

            <button
              onClick={() => setStatus(status === "recording" ? "paused" : "recording")}
              className="w-10 h-10 rounded-xl flex items-center justify-center transition-all"
              style={{
                background: status === "recording" ? "rgba(255,209,0,0.12)" : "rgba(39,116,174,0.15)",
                border: `1px solid ${status === "recording" ? "rgba(255,209,0,0.2)" : "rgba(39,116,174,0.2)"}`,
              }}
            >
              {status === "recording" ? <Pause size={16} className="text-[#FFD100]" /> : <Play size={16} className="text-[#2774AE] ml-0.5" />}
            </button>

            <button
              onClick={handleStop}
              className="w-10 h-10 rounded-xl flex items-center justify-center transition-all hover:brightness-110"
              style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.2)" }}
            >
              <Square size={16} className="text-[#ef4444]" fill="#ef4444" />
            </button>

            <button
              className="w-10 h-10 rounded-xl flex items-center justify-center transition-all"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}
            >
              <Volume2 size={16} className="text-white/40" />
            </button>
          </div>

          {/* Input source */}
          <div className="flex items-center gap-2 mt-4">
            <button
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] text-white/25 hover:text-white/40 transition-colors"
              style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}
            >
              <Radio size={9} />
              {devices.find((d) => d.id === selectedDevice)?.name || "Microphone"}
              <ChevronDown size={9} />
            </button>
          </div>
        </div>

        {/* ─── Live Transcript Panel ─── */}
        {showTranscript && (
          <div
            className="w-[300px] shrink-0 flex flex-col"
            style={{ borderLeft: "1px solid rgba(255,255,255,0.04)", background: "rgba(255,255,255,0.01)" }}
          >
            <div className="flex items-center justify-between px-4 py-2.5 shrink-0" style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
              <div className="flex items-center gap-1.5">
                <FileText size={10} className="text-white/25" />
                <span className="text-[10px] text-white/30 uppercase tracking-wider">Live Transcript</span>
              </div>
              <div className="flex items-center gap-1">
                <div
                  className="w-1.5 h-1.5 rounded-full"
                  style={{
                    background: status === "recording" ? "#6dd58c" : "#FFD100",
                    animation: status === "recording" ? "pulse 2s ease-in-out infinite" : "none",
                  }}
                />
                <span className="text-[9px]" style={{ color: status === "recording" ? "#6dd58c" : "#FFD100" }}>
                  {status === "recording" ? "Live" : "Paused"}
                </span>
              </div>
            </div>

            {/* Speaker Detection Tracker */}
            {detectedSpeakers.length > 0 && (
              <div className="px-4 py-2.5 shrink-0" style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <Users size={9} className="text-white/25" />
                    <span className="text-[9px] text-white/30 uppercase tracking-wider">Speakers</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="flex items-center gap-0.5 text-[9px] text-[#6dd58c]">
                      <UserCheck size={8} /> {identifiedCount}
                    </span>
                    {unidentifiedCount > 0 && (
                      <span className="flex items-center gap-0.5 text-[9px] text-[#f97316]">
                        <UserX size={8} /> {unidentifiedCount}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  {detectedSpeakers.map((s) => {
                    const isRenamed = !!speakerLabels[s.speaker];
                    const isEditing = editingSpeaker === s.speaker;
                    const displayName = getSpeakerDisplayName(s.speaker);

                    return (
                      <div key={s.speaker} className="flex items-center gap-2 group/speaker">
                        <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0" style={{ background: `${s.color}20` }}>
                          <span className="text-[7px]" style={{ color: s.color }}>{displayName[0]}</span>
                        </div>

                        {isEditing ? (
                          <div className="flex items-center gap-1 flex-1 min-w-0">
                            <input
                              autoFocus
                              type="text"
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") confirmEditSpeaker(s.speaker);
                                if (e.key === "Escape") { setEditingSpeaker(null); setEditValue(""); }
                              }}
                              placeholder="Enter name…"
                              className="flex-1 min-w-0 text-[10px] text-white/70 px-1.5 py-0.5 rounded bg-white/[0.06] border border-white/[0.08] outline-none focus:border-[#2774AE]/40"
                            />
                            <button onClick={() => confirmEditSpeaker(s.speaker)} className="w-4 h-4 rounded flex items-center justify-center hover:bg-white/[0.06]">
                              <Check size={8} className="text-[#6dd58c]" />
                            </button>
                          </div>
                        ) : (
                          <>
                            <div className="flex-1 min-w-0">
                              <span className="text-[10px] truncate block" style={{ color: s.color }}>{displayName}</span>
                              <span className="text-[8px] text-white/15">{s.count} segment{s.count !== 1 ? "s" : ""}</span>
                            </div>
                            {!s.identified && !isRenamed && (
                              <button
                                onClick={() => startEditSpeaker(s.speaker)}
                                className="px-1.5 py-0.5 rounded flex items-center gap-0.5 text-[8px] text-[#f97316] hover:bg-[#f97316]/10 transition-colors opacity-0 group-hover/speaker:opacity-100"
                              >
                                <Pencil size={7} /> ID
                              </button>
                            )}
                            {(s.identified || isRenamed) && (
                              <div className="w-3 h-3 rounded-full flex items-center justify-center" style={{ background: "rgba(109,213,140,0.12)" }}>
                                <Check size={7} className="text-[#6dd58c]" />
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
              {segments.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-[11px] text-white/20">Waiting for speech...</p>
                </div>
              )}
              {segments.map((seg, i) => (
                <div key={i} className="group">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <div className="w-4 h-4 rounded-full flex items-center justify-center" style={{ background: `${seg.color}20` }}>
                      <span className="text-[6px]" style={{ color: seg.color }}>{getSpeakerDisplayName(seg.speaker)[0]}</span>
                    </div>
                    <span className="text-[10px]" style={{ color: seg.color }}>{getSpeakerDisplayName(seg.speaker)}</span>
                    {!seg.identified && !speakerLabels[seg.speaker] && (
                      <span className="text-[7px] px-1 py-px rounded" style={{ background: "rgba(249,115,22,0.1)", color: "#f97316" }}>?</span>
                    )}
                    <span className="text-[8px] text-white/10 font-mono ml-auto">{seg.timestamp}</span>
                  </div>
                  <p className="text-[11px] text-white/50 pl-[22px]">{seg.text}</p>
                </div>
              ))}

              {status === "recording" && (
                <div className="flex items-center gap-1.5 pl-[22px]">
                  <div className="flex gap-0.5">
                    <div className="w-1 h-1 rounded-full bg-white/20 animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="w-1 h-1 rounded-full bg-white/20 animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="w-1 h-1 rounded-full bg-white/20 animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                  <span className="text-[9px] text-white/15">Listening...</span>
                </div>
              )}
              <div ref={transcriptEndRef} />
            </div>

            {/* Transcript stats */}
            <div className="px-4 py-2.5 shrink-0 flex items-center gap-3" style={{ borderTop: "1px solid rgba(255,255,255,0.03)" }}>
              <span className="flex items-center gap-1 text-[9px] text-white/15"><FileText size={8} /> {segments.length} segments</span>
              <span className="flex items-center gap-1 text-[9px] text-white/15"><Users size={8} /> {totalSpeakers} voices</span>
              <span className="flex items-center gap-1 text-[9px] text-white/15"><Sparkles size={8} /> AI processing</span>
            </div>
          </div>
        )}
      </div>

      {/* ─── Bottom Status ─── */}
      <div
        className="flex items-center justify-between px-5 h-[32px] shrink-0"
        style={{ borderTop: "1px solid rgba(255,255,255,0.03)", background: "rgba(255,255,255,0.01)" }}
      >
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-[9px] text-white/15">
            <Radio size={8} className={status === "recording" ? "text-[#6dd58c]" : "text-white/15"} />
            {isMuted ? "Muted" : "Capturing audio"}
          </span>
          <span className="flex items-center gap-1 text-[9px] text-white/15">
            <Sparkles size={8} /> Whisper v3 · Real-time
          </span>
        </div>
        <span className="text-[9px] text-white/10">Auto-save enabled</span>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}

function formatTime(s: number) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
}
