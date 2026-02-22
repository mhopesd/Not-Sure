import { useState, useEffect, useCallback } from "react";
import {
  Home,
  Mic,
  FileText,
  BookOpen,
  Settings,
  Search,
  Plus,
  Clock,
  Calendar,
  ChevronRight,
  Sparkles,
  Zap,
  BarChart3,
  Users,
} from "lucide-react";
import { MeetingsView } from "./MeetingsView";
import { MeetingDetailView } from "./MeetingDetailView";
import { JournalView } from "./JournalView";
import { SettingsView } from "./SettingsView";
import { RecordingView } from "./RecordingView";
import { getApiUrl, getApiHeaders } from "../config/api";

const NAV_ITEMS = [
  { id: "home", icon: Home, label: "Home" },
  { id: "meetings", icon: FileText, label: "Meetings" },
  { id: "journal", icon: BookOpen, label: "Journal" },
  { id: "settings", icon: Settings, label: "Settings" },
];

const ICON_COL = "w-8 h-8 shrink-0 rounded-lg flex items-center justify-center";

interface MeetingPreview {
  id: string;
  title: string;
  time: string;
  duration: string;
  tag: string;
  tagColor: string;
}

// Tag color mapping for meetings from the backend
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

function formatDurationStr(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins} min`;
  const hrs = Math.floor(mins / 60);
  const remainMins = mins % 60;
  return remainMins > 0 ? `${hrs}h ${remainMins}m` : `${hrs}h`;
}

function formatTimeStr(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
  } catch {
    return "";
  }
}

function formatDateLabel(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const meetingDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const diffDays = Math.floor((today.getTime() - meetingDay.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}

export interface BackendMeeting {
  id: string;
  title: string;
  date: string;
  speakers: string[];
  transcript: string;
  nextSteps: string;
  duration: number;
  tags?: string[];
  executive_summary?: string;
  highlights?: string[];
  tasks?: any[];
  diarized_transcript?: any[];
  speaker_info?: any[];
}

export function DashboardLayout() {
  const [activeView, setActiveView] = useState("home");
  const [selectedMeetingId, setSelectedMeetingId] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [meetings, setMeetings] = useState<BackendMeeting[]>([]);
  const [meetingsLoading, setMeetingsLoading] = useState(true);

  const fetchMeetings = useCallback(async () => {
    try {
      const response = await fetch(getApiUrl("/api/meetings"), { headers: getApiHeaders() });
      if (response.ok) {
        const data = await response.json();
        setMeetings(data.meetings || data || []);
      }
    } catch (err) {
      console.error("Failed to fetch meetings:", err);
    } finally {
      setMeetingsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMeetings();
  }, [fetchMeetings]);

  const handleSelectMeeting = (id: string) => {
    setSelectedMeetingId(id);
    setActiveView("meeting-detail");
  };

  const handleBackFromDetail = () => {
    setSelectedMeetingId(null);
    setActiveView("meetings");
  };

  const handleStartRecording = () => {
    setIsRecording(true);
  };

  const handleStopRecording = () => {
    setIsRecording(false);
    // Refresh meetings after recording stops
    fetchMeetings();
  };

  // Full-screen recording overlay
  if (isRecording) {
    return <RecordingView onStop={handleStopRecording} />;
  }

  // Meeting detail view (replaces main content)
  if (activeView === "meeting-detail" && selectedMeetingId) {
    return (
      <div className="flex h-full">
        {/* Sidebar stays visible */}
        <Sidebar
          activeView="meetings"
          setActiveView={(v) => { setActiveView(v); setSelectedMeetingId(null); }}
          onRecord={handleStartRecording}
          meetingCount={meetings.length}
        />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <MeetingDetailView meetingId={selectedMeetingId} onBack={handleBackFromDetail} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      <Sidebar activeView={activeView} setActiveView={setActiveView} onRecord={handleStartRecording} meetingCount={meetings.length} />

      {/* ─── Main Content ─── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <div
          className="h-[44px] flex items-center justify-between px-5 shrink-0"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
        >
          <div className="flex items-center gap-2">
            <h3 className="text-white/80">
              {NAV_ITEMS.find((n) => n.id === activeView)?.label}
            </h3>
            <span className="text-[10px] text-white/20">
              {new Date().toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" })}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <button className="p-1.5 rounded-md hover:bg-white/[0.04] transition-colors">
              <Plus size={14} className="text-white/30" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {activeView === "home" && <HomeView meetings={meetings} onSelectMeeting={handleSelectMeeting} />}
          {activeView === "meetings" && <MeetingsView meetings={meetings} onSelectMeeting={handleSelectMeeting} onRefresh={fetchMeetings} />}
          {activeView === "journal" && <JournalView />}
          {activeView === "settings" && <SettingsView />}
        </div>
      </div>
    </div>
  );
}

/* ─── Sidebar ─── */
function Sidebar({
  activeView,
  setActiveView,
  onRecord,
  meetingCount,
}: {
  activeView: string;
  setActiveView: (v: string) => void;
  onRecord: () => void;
  meetingCount: number;
}) {
  return (
    <div
      className="w-[200px] shrink-0 flex flex-col p-3 pb-2"
      style={{
        background: "rgba(255,255,255,0.015)",
        borderRight: "1px solid rgba(255,255,255,0.04)",
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-1.5 mb-4">
        <div className="w-6 h-6 rounded-md bg-gradient-to-br from-[#2774AE] to-[#1a5a8e] flex items-center justify-center">
          <svg width="11" height="11" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="5" stroke="white" strokeWidth="1.5" fill="none" />
            <circle cx="8" cy="8" r="2" fill="white" />
          </svg>
        </div>
        <span className="text-[12px] text-white/70">NotSure</span>
      </div>

      {/* Quick Record */}
      <button
        onClick={onRecord}
        className="flex items-center gap-2 px-2.5 py-2 rounded-lg mb-3 transition-all hover:brightness-110"
        style={{
          background: "linear-gradient(135deg, rgba(39,116,174,0.15), rgba(39,116,174,0.08))",
          border: "1px solid rgba(39,116,174,0.15)",
        }}
      >
        <div className="w-5 h-5 rounded-md bg-[#2774AE]/20 flex items-center justify-center">
          <Mic size={11} className="text-[#2774AE]" />
        </div>
        <span className="text-[11px] text-[#2774AE]">New Recording</span>
        <span className="ml-auto text-[9px] text-white/20 font-mono">⌘R</span>
      </button>

      {/* Search */}
      <div className="relative mb-3">
        <Search size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-white/20" />
        <input
          type="text"
          placeholder="Search..."
          className="w-full pl-7 pr-2.5 py-1.5 rounded-md text-[11px] text-white/60 placeholder:text-white/15 outline-none"
          style={{
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.04)",
          }}
        />
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-0.5">
        {NAV_ITEMS.map((item) => {
          const isActive = activeView === item.id || (activeView === "meeting-detail" && item.id === "meetings");
          return (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg transition-all text-left"
              style={{
                background: isActive ? "rgba(39,116,174,0.1)" : "transparent",
              }}
            >
              <item.icon
                size={14}
                style={{ color: isActive ? "#2774AE" : "rgba(255,255,255,0.3)" }}
              />
              <span
                className="text-[11px]"
                style={{ color: isActive ? "#2774AE" : "rgba(255,255,255,0.45)" }}
              >
                {item.label}
              </span>
              {item.id === "meetings" && (
                <span className="ml-auto text-[9px] text-white/20 bg-white/[0.04] px-1.5 py-[1px] rounded">
                  {meetingCount}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Sidebar Footer */}
      <div className="pt-2" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="flex items-center gap-2 px-1.5">
          <div className="w-5 h-5 rounded-full bg-gradient-to-br from-[#2774AE] to-[#1a5a8e] flex items-center justify-center">
            <span className="text-[8px] text-white">MH</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[10px] text-white/50 truncate">mhopesd</div>
          </div>
          <div className="w-1.5 h-1.5 rounded-full bg-[#6dd58c]" title="Online" />
        </div>
      </div>
    </div>
  );
}

/* ─── Home View ─── */
function HomeView({ meetings, onSelectMeeting }: { meetings: BackendMeeting[]; onSelectMeeting: (id: string) => void }) {
  // Convert backend meetings to preview format for the home view
  const recentPreviews: MeetingPreview[] = meetings.slice(0, 5).map((m) => {
    const firstTag = m.tags?.[0] || "meeting";
    return {
      id: m.id,
      title: m.title,
      time: `${formatDateLabel(m.date)}, ${formatTimeStr(m.date)}`,
      duration: formatDurationStr(m.duration),
      tag: firstTag,
      tagColor: TAG_COLORS[firstTag] || "#2774AE",
    };
  });

  // Compute stats from real data
  const totalMeetings = meetings.length;
  const totalDuration = meetings.reduce((sum, m) => sum + (m.duration || 0), 0);
  const totalHours = (totalDuration / 3600).toFixed(1);
  const totalActionItems = meetings.reduce((sum, m) => sum + (m.tasks?.length || 0), 0);
  const withSummary = meetings.filter((m) => m.executive_summary).length;

  // Greeting based on time of day
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="max-w-2xl space-y-5">
      {/* Greeting */}
      <div>
        <h2 className="text-white/90 mb-0.5">{greeting}</h2>
        <p className="text-[12px] text-white/30">You have {totalMeetings} meeting{totalMeetings !== 1 ? "s" : ""} recorded</p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-2">
        {[
          { label: "Meetings", value: String(totalMeetings), icon: <FileText size={12} />, color: "#2774AE" },
          { label: "Hours Recorded", value: `${totalHours}h`, icon: <Clock size={12} />, color: "#FFD100" },
          { label: "Action Items", value: String(totalActionItems), icon: <Zap size={12} />, color: "#6dd58c" },
          { label: "Summaries", value: String(withSummary), icon: <Sparkles size={12} />, color: "#8b5cf6" },
        ].map((s) => (
          <div
            key={s.label}
            className="p-3 rounded-lg"
            style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}
          >
            <div className="flex items-center justify-between mb-2">
              <div
                className="w-6 h-6 rounded-md flex items-center justify-center"
                style={{ background: `${s.color}12`, color: s.color }}
              >
                {s.icon}
              </div>
              <BarChart3 size={10} className="text-white/10" />
            </div>
            <div className="text-[18px] text-white/85" style={{ color: s.color }}>{s.value}</div>
            <div className="text-[9px] text-white/25 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Recent */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <Clock size={11} className="text-white/25" />
            <span className="text-[10px] text-white/30 uppercase tracking-wider">Recent Meetings</span>
          </div>
          <span className="text-[9px] text-[#2774AE] cursor-pointer" onClick={() => {}}>View all</span>
        </div>
        <div className="space-y-1">
          {recentPreviews.length > 0 ? (
            recentPreviews.map((m) => (
              <MeetingRow key={m.id} meeting={m} onClick={() => onSelectMeeting(m.id)} />
            ))
          ) : (
            <p className="text-[12px] text-white/25 py-4 text-center">No meetings recorded yet. Click "New Recording" to get started.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function MeetingRow({ meeting, onClick }: { meeting: MeetingPreview; onClick: () => void }) {
  return (
    <button onClick={onClick} className="w-full flex items-center gap-3 p-2.5 rounded-lg hover:bg-white/[0.03] transition-all group text-left">
      <div
        className={ICON_COL}
        style={{ background: "rgba(255,255,255,0.025)" }}
      >
        <FileText size={13} className="text-white/30 group-hover:text-white/50 transition-colors" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[12px] text-white/75 truncate">{meeting.title}</span>
          <span
            className="text-[8px] px-1.5 py-[1px] rounded-full shrink-0"
            style={{ background: `${meeting.tagColor}15`, color: meeting.tagColor }}
          >
            {meeting.tag}
          </span>
        </div>
        <div className="flex items-center gap-1.5 mt-0.5">
          <span className="text-[10px] text-white/25">{meeting.time}</span>
          <span className="text-[10px] text-white/15">·</span>
          <span className="text-[10px] text-white/25">{meeting.duration}</span>
        </div>
      </div>
      <ChevronRight size={12} className="text-white/10 group-hover:text-white/25 transition-colors shrink-0" />
    </button>
  );
}
