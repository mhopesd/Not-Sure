import { useState, useEffect, useRef } from "react";

interface TranscriptLine {
  id: number;
  speaker: string;
  text: string;
  timestamp: string;
}

const MOCK_TRANSCRIPT: Omit<TranscriptLine, "id" | "timestamp">[] = [
  { speaker: "Speaker 1", text: "So if we look at the Q3 numbers, we're actually ahead of projections by about twelve percent." },
  { speaker: "Speaker 2", text: "That's great news. What's driving the increase?" },
  { speaker: "Speaker 1", text: "Mainly the enterprise tier. We onboarded fourteen new accounts last month alone." },
  { speaker: "Speaker 2", text: "Impressive. Let's make sure we document the onboarding flow improvements that contributed." },
  { speaker: "Speaker 1", text: "Agreed. I'll have the team put together a retrospective by Friday." },
  { speaker: "Speaker 3", text: "Can we also discuss the retention metrics? I noticed some churn in the mid-tier." },
  { speaker: "Speaker 2", text: "Good point. Let's add that as an action item for the next sync." },
  { speaker: "Speaker 1", text: "I'll pull the cohort analysis and share it before the meeting." },
  { speaker: "Speaker 3", text: "Perfect. Also, the design team wants feedback on the new dashboard mockups." },
  { speaker: "Speaker 2", text: "Let's schedule a dedicated review session for that. Maybe Thursday afternoon?" },
];

interface LiveTranscriptProps {
  isActive: boolean;
  elapsedSeconds: number;
}

export function LiveTranscript({ isActive, elapsedSeconds }: LiveTranscriptProps) {
  const [lines, setLines] = useState<TranscriptLine[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const lineIndexRef = useRef(0);

  useEffect(() => {
    if (!isActive) {
      setLines([]);
      lineIndexRef.current = 0;
      return;
    }

    const interval = setInterval(() => {
      const mockLine = MOCK_TRANSCRIPT[lineIndexRef.current % MOCK_TRANSCRIPT.length];
      const minutes = Math.floor(elapsedSeconds / 60);
      const seconds = elapsedSeconds % 60;
      const timestamp = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

      setLines((prev) => [
        ...prev.slice(-8),
        {
          id: Date.now(),
          speaker: mockLine.speaker,
          text: mockLine.text,
          timestamp,
        },
      ]);
      lineIndexRef.current++;
    }, 4000);

    return () => clearInterval(interval);
  }, [isActive, elapsedSeconds]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines]);

  if (!isActive || lines.length === 0) {
    return (
      <div className="flex items-center justify-center py-3 opacity-40">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-[#2774AE] animate-pulse" />
          <span className="text-[11px] text-white/50">Waiting for speech...</span>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={scrollRef}
      className="max-h-[120px] overflow-y-auto scrollbar-thin space-y-1.5 pr-1"
      style={{
        scrollbarWidth: "thin",
        scrollbarColor: "rgba(255,255,255,0.1) transparent",
      }}
    >
      {lines.map((line, idx) => (
        <div
          key={line.id}
          className="flex gap-2 transition-opacity duration-300"
          style={{ opacity: idx === lines.length - 1 ? 1 : 0.6 }}
        >
          <span className="text-[10px] text-white/30 font-mono shrink-0 pt-[2px]">
            {line.timestamp}
          </span>
          <div className="min-w-0">
            <span
              className="text-[10px] mr-1.5"
              style={{
                color:
                  line.speaker === "Speaker 1"
                    ? "#2774AE"
                    : line.speaker === "Speaker 2"
                    ? "#FFD100"
                    : "#6dd58c",
              }}
            >
              {line.speaker}
            </span>
            <span className="text-[11px] text-white/80">{line.text}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
