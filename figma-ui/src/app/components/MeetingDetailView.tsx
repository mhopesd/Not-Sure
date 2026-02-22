import { useState, useEffect } from "react";
import {
  ArrowLeft,
  FileText,
  Clock,
  Users,
  Zap,
  Sparkles,
  Flag,
  Copy,
  Download,
  Share2,
  CheckCircle2,
  Circle,
  Play,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Calendar,
  MoreHorizontal,
} from "lucide-react";
import { getApiUrl, getApiHeaders } from "../config/api";

const ICON_COL = "w-8 h-8 shrink-0 rounded-lg flex items-center justify-center";

const TAG_COLORS: Record<string, string> = {
  internal: "#2774AE",
  client: "#FFD100",
  design: "#6dd58c",
  team: "#2774AE",
  strategy: "#8b5cf6",
  leadership: "#ef4444",
  "1:1": "#f97316",
  engineering: "#2774AE",
};

const SPEAKER_COLORS = ["#2774AE", "#6dd58c", "#FFD100", "#8b5cf6", "#f97316", "#ef4444"];

interface MeetingDetailViewProps {
  meetingId: string;
  onBack: () => void;
}

interface MeetingData {
  id: string;
  title: string;
  date: string;
  duration: number;
  speakers: string[];
  transcript: string;
  executive_summary?: string;
  highlights?: string[];
  tasks?: { text: string; assignee?: string; priority?: string; done?: boolean }[];
  diarized_transcript?: { speaker: string; text: string; start?: number; end?: number }[];
  speaker_info?: { name: string; role?: string; speaking_time?: string }[];
  tags?: string[];
}

function formatDurationStr(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins} min`;
  const hrs = Math.floor(mins / 60);
  const remainMins = mins % 60;
  return remainMins > 0 ? `${hrs}h ${remainMins}m` : `${hrs}h`;
}

function formatDateLabel(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}

function formatTimeStr(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
  } catch {
    return "";
  }
}

export function MeetingDetailView({ meetingId, onBack }: MeetingDetailViewProps) {
  const [activeTab, setActiveTab] = useState<"transcript" | "summary" | "actions">("summary");
  const [meeting, setMeeting] = useState<MeetingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionStates, setActionStates] = useState<Record<string, boolean>>({});
  const [expandedTranscript, setExpandedTranscript] = useState(true);

  useEffect(() => {
    async function fetchMeeting() {
      setLoading(true);
      try {
        const response = await fetch(getApiUrl(`/api/meetings/${meetingId}`), { headers: getApiHeaders() });
        if (response.ok) {
          const data = await response.json();
          setMeeting(data);
          // Initialize action states
          const states: Record<string, boolean> = {};
          (data.tasks || []).forEach((t: any, i: number) => {
            states[`a${i}`] = t.done || false;
          });
          setActionStates(states);
        }
      } catch (err) {
        console.error("Failed to fetch meeting:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchMeeting();
  }, [meetingId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-[#2774AE] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!meeting) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-white/30 text-[12px]">Meeting not found</p>
        <button onClick={onBack} className="mt-2 text-[#2774AE] text-[11px]">Go back</button>
      </div>
    );
  }

  const firstTag = meeting.tags?.[0] || "meeting";
  const tagColor = TAG_COLORS[firstTag] || "#2774AE";
  const tasks = meeting.tasks || [];
  const doneCount = Object.values(actionStates).filter(Boolean).length;

  const toggleAction = (id: string) => {
    setActionStates((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Build transcript segments from diarized or plain transcript
  const transcriptSegments = meeting.diarized_transcript && meeting.diarized_transcript.length > 0
    ? meeting.diarized_transcript.map((seg, i) => ({
        ts: seg.start ? `${Math.floor(seg.start / 60)}:${String(Math.floor(seg.start % 60)).padStart(2, "0")}` : `${i}:00`,
        speaker: seg.speaker || "Speaker",
        text: seg.text,
        color: SPEAKER_COLORS[i % SPEAKER_COLORS.length],
      }))
    : meeting.transcript
    ? meeting.transcript.split("\n").filter(Boolean).map((line, i) => ({
        ts: `${i}:00`,
        speaker: "Speaker",
        text: line,
        color: SPEAKER_COLORS[0],
      }))
    : [];

  // Participants from speaker_info or speakers array
  const participants = meeting.speaker_info && meeting.speaker_info.length > 0
    ? meeting.speaker_info.map((s, i) => ({
        name: s.name,
        role: s.role || "",
        color: SPEAKER_COLORS[i % SPEAKER_COLORS.length],
        speaking: s.speaking_time || "",
      }))
    : meeting.speakers?.map((name, i) => ({
        name,
        role: "",
        color: SPEAKER_COLORS[i % SPEAKER_COLORS.length],
        speaking: "",
      })) || [];

  const tabs = [
    { id: "summary" as const, label: "Summary", icon: <Sparkles size={11} /> },
    { id: "transcript" as const, label: "Transcript", icon: <FileText size={11} /> },
    { id: "actions" as const, label: "Actions", icon: <Zap size={11} />, count: tasks.length },
  ];

  return (
    <div className="flex h-full">
      {/* ─── Main content ─── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <div className="px-5 pt-4 pb-3 shrink-0">
          <button
            onClick={onBack}
            className="flex items-center gap-1 text-[11px] text-white/30 hover:text-white/50 transition-colors mb-3"
          >
            <ArrowLeft size={12} />
            All Meetings
          </button>

          <div className="flex items-start gap-3">
            <div className={ICON_COL} style={{ background: `${tagColor}12` }}>
              <FileText size={14} style={{ color: tagColor }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <h2 className="text-white/90 truncate">{meeting.title}</h2>
                <span
                  className="text-[8px] px-1.5 py-[1px] rounded-full shrink-0"
                  style={{ background: `${tagColor}15`, color: tagColor }}
                >
                  {firstTag}
                </span>
              </div>
              <div className="flex items-center gap-2 text-[10px] text-white/30">
                <span className="flex items-center gap-1"><Calendar size={9} /> {formatDateLabel(meeting.date)}, {formatTimeStr(meeting.date)}</span>
                <span className="text-white/15">·</span>
                <span className="flex items-center gap-1"><Clock size={9} /> {formatDurationStr(meeting.duration)}</span>
                <span className="text-white/15">·</span>
                <span className="flex items-center gap-1"><Users size={9} /> {participants.length}</span>
              </div>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button className="p-1.5 rounded-md hover:bg-white/[0.04] transition-colors"><Copy size={12} className="text-white/25" /></button>
              <button className="p-1.5 rounded-md hover:bg-white/[0.04] transition-colors"><Share2 size={12} className="text-white/25" /></button>
              <button className="p-1.5 rounded-md hover:bg-white/[0.04] transition-colors"><Download size={12} className="text-white/25" /></button>
              <button className="p-1.5 rounded-md hover:bg-white/[0.04] transition-colors"><MoreHorizontal size={12} className="text-white/25" /></button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="px-5 flex items-center gap-1 shrink-0 mb-0.5">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] transition-all"
                style={{
                  background: isActive ? "rgba(39,116,174,0.1)" : "transparent",
                  color: isActive ? "#2774AE" : "rgba(255,255,255,0.35)",
                }}
              >
                {tab.icon}
                {tab.label}
                {tab.count !== undefined && (
                  <span className="text-[9px] px-1 py-[1px] rounded" style={{ background: isActive ? "rgba(39,116,174,0.15)" : "rgba(255,255,255,0.04)" }}>
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto px-5 py-3">
          {activeTab === "summary" && <SummaryTab meeting={meeting} />}
          {activeTab === "transcript" && <TranscriptTab segments={transcriptSegments} expanded={expandedTranscript} setExpanded={setExpandedTranscript} />}
          {activeTab === "actions" && <ActionsTab tasks={tasks} actionStates={actionStates} onToggle={toggleAction} doneCount={doneCount} />}
        </div>
      </div>

      {/* ─── Right sidebar: Participants ─── */}
      {participants.length > 0 && (
        <div
          className="w-[200px] shrink-0 p-4 overflow-y-auto"
          style={{ borderLeft: "1px solid rgba(255,255,255,0.04)", background: "rgba(255,255,255,0.01)" }}
        >
          <div className="flex items-center gap-1.5 mb-3">
            <Users size={10} className="text-white/25" />
            <span className="text-[10px] text-white/30 uppercase tracking-wider">Participants</span>
          </div>
          <div className="space-y-2">
            {participants.map((p) => (
              <div key={p.name} className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0" style={{ background: `${p.color}20` }}>
                  <span className="text-[8px]" style={{ color: p.color }}>
                    {p.name.split(" ").map((n) => n[0]).join("")}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[11px] text-white/60 truncate">{p.name}</div>
                  {p.role && <div className="text-[9px] text-white/20">{p.role}</div>}
                </div>
              </div>
            ))}
          </div>

          {/* Speaking time */}
          {participants.some((p) => p.speaking) && (
            <div className="mt-4 pt-3" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
              <div className="flex items-center gap-1.5 mb-2">
                <MessageSquare size={10} className="text-white/20" />
                <span className="text-[10px] text-white/25 uppercase tracking-wider">Talk Time</span>
              </div>
              <div className="space-y-1.5">
                {participants.filter((p) => p.speaking).map((p) => {
                  const mins = parseFloat(p.speaking.replace(":", ".")) || 0;
                  const maxMins = Math.max(...participants.map((pp) => parseFloat(pp.speaking.replace(":", ".")) || 0), 1);
                  return (
                    <div key={p.name}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-[9px] text-white/35">{p.name.split(" ")[0]}</span>
                        <span className="text-[9px] text-white/20 font-mono">{p.speaking}</span>
                      </div>
                      <div className="h-1 rounded-full bg-white/[0.04] overflow-hidden">
                        <div className="h-full rounded-full transition-all" style={{ width: `${(mins / maxMins) * 100}%`, background: p.color, opacity: 0.6 }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Summary Tab ─── */
function SummaryTab({ meeting }: { meeting: MeetingData }) {
  const summary = meeting.executive_summary;
  const highlights = meeting.highlights || [];

  if (!summary && highlights.length === 0) {
    return (
      <div className="text-center py-12 max-w-xl">
        <Sparkles size={20} className="text-white/15 mx-auto mb-2" />
        <p className="text-[12px] text-white/25">No AI summary available for this meeting</p>
        <p className="text-[10px] text-white/15 mt-1">Summary is generated automatically after recording stops</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-w-xl">
      {summary && (
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <Sparkles size={10} className="text-[#8b5cf6]" />
            <span className="text-[10px] text-white/30 uppercase tracking-wider">AI Summary</span>
          </div>
          <div
            className="p-3 rounded-lg text-[12px] text-white/60"
            style={{ background: "rgba(139,92,246,0.04)", border: "1px solid rgba(139,92,246,0.08)" }}
          >
            {summary}
          </div>
        </div>
      )}

      {highlights.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <CheckCircle2 size={10} className="text-[#2774AE]" />
            <span className="text-[10px] text-white/30 uppercase tracking-wider">Key Highlights</span>
          </div>
          <div className="space-y-1">
            {highlights.map((h, i) => (
              <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-lg" style={{ background: "rgba(255,255,255,0.02)" }}>
                <div className="w-5 h-5 rounded flex items-center justify-center shrink-0 mt-0.5" style={{ background: "rgba(39,116,174,0.1)" }}>
                  <CheckCircle2 size={10} className="text-[#2774AE]" />
                </div>
                <span className="text-[12px] text-white/55">{h}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Transcript Tab ─── */
function TranscriptTab({ segments, expanded, setExpanded }: { segments: any[]; expanded: boolean; setExpanded: (v: boolean) => void }) {
  if (segments.length === 0) {
    return (
      <div className="text-center py-12 max-w-xl">
        <FileText size={20} className="text-white/15 mx-auto mb-2" />
        <p className="text-[12px] text-white/25">No transcript available</p>
      </div>
    );
  }

  const displayedSegments = expanded ? segments : segments.slice(0, 5);

  return (
    <div className="max-w-xl">
      <div className="space-y-0.5">
        {displayedSegments.map((seg, i) => (
          <div key={i} className="flex gap-3 p-2.5 rounded-lg hover:bg-white/[0.02] transition-colors group">
            <span className="text-[9px] text-white/15 font-mono w-7 shrink-0 pt-0.5 text-right">{seg.ts}</span>
            <div className="flex-1 min-w-0">
              <span className="text-[10px] mr-1.5" style={{ color: seg.color }}>{seg.speaker}</span>
              <span className="text-[12px] text-white/55">{seg.text}</span>
            </div>
            <button className="opacity-0 group-hover:opacity-100 transition-opacity p-1">
              <Copy size={10} className="text-white/15" />
            </button>
          </div>
        ))}
      </div>
      {segments.length > 5 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 mt-2 px-3 py-1.5 text-[10px] text-white/25 hover:text-white/40 transition-colors"
        >
          {expanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
          {expanded ? "Collapse" : `Show ${segments.length - 5} more segments`}
        </button>
      )}
    </div>
  );
}

/* ─── Actions Tab ─── */
function ActionsTab({
  tasks,
  actionStates,
  onToggle,
  doneCount,
}: {
  tasks: any[];
  actionStates: Record<string, boolean>;
  onToggle: (id: string) => void;
  doneCount: number;
}) {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-12 max-w-xl">
        <Zap size={20} className="text-white/15 mx-auto mb-2" />
        <p className="text-[12px] text-white/25">No action items for this meeting</p>
      </div>
    );
  }

  const priorityColors: Record<string, string> = { high: "#ef4444", medium: "#FFD100", low: "#6dd58c" };

  return (
    <div className="max-w-xl">
      <div className="flex items-center gap-2 mb-3">
        <div className="flex-1 h-1.5 rounded-full bg-white/[0.04] overflow-hidden">
          <div className="h-full rounded-full bg-[#6dd58c] transition-all" style={{ width: `${tasks.length > 0 ? (doneCount / tasks.length) * 100 : 0}%` }} />
        </div>
        <span className="text-[10px] text-white/25 shrink-0">{doneCount}/{tasks.length} done</span>
      </div>

      <div className="space-y-1">
        {tasks.map((item, idx) => {
          const id = `a${idx}`;
          const isDone = actionStates[id] || false;
          const priority = item.priority || "medium";
          return (
            <button
              key={id}
              onClick={() => onToggle(id)}
              className="w-full flex items-start gap-2.5 p-2.5 rounded-lg hover:bg-white/[0.02] transition-all text-left group"
            >
              <div className="mt-0.5 shrink-0">
                {isDone ? (
                  <CheckCircle2 size={14} className="text-[#6dd58c]" />
                ) : (
                  <Circle size={14} className="text-white/15 group-hover:text-white/30 transition-colors" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <span
                  className="text-[12px] transition-colors"
                  style={{
                    color: isDone ? "rgba(255,255,255,0.25)" : "rgba(255,255,255,0.6)",
                    textDecoration: isDone ? "line-through" : "none",
                  }}
                >
                  {item.text}
                </span>
                <div className="flex items-center gap-2 mt-0.5">
                  {item.assignee && <span className="text-[9px] text-white/20">{item.assignee}</span>}
                  <span
                    className="text-[8px] px-1.5 py-[0.5px] rounded-full"
                    style={{ background: `${priorityColors[priority] || "#FFD100"}12`, color: priorityColors[priority] || "#FFD100" }}
                  >
                    {priority}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
