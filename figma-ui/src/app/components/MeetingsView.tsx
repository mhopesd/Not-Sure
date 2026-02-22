import { useState, useEffect, useMemo } from "react";
import {
  Search,
  FileText,
  Clock,
  ChevronRight,
  Filter,
  Flag,
  Calendar,
  Users,
  Sparkles,
  Zap,
  Download,
} from "lucide-react";
import { getApiUrl, getApiHeaders } from "../config/api";
import type { BackendMeeting } from "./DashboardLayout";

const ICON_COL = "w-8 h-8 shrink-0 rounded-lg flex items-center justify-center";

export interface MeetingFull {
  id: string;
  title: string;
  date: string;
  time: string;
  duration: string;
  tag: string;
  tagColor: string;
  participants: number;
  actionItems: number;
  hasTranscript: boolean;
  hasSummary: boolean;
  flagged: boolean;
}

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

export function backendToMeetingFull(m: BackendMeeting): MeetingFull {
  const firstTag = m.tags?.[0] || "meeting";
  return {
    id: m.id,
    title: m.title,
    date: formatDateLabel(m.date),
    time: formatTimeStr(m.date),
    duration: formatDurationStr(m.duration),
    tag: firstTag,
    tagColor: TAG_COLORS[firstTag] || "#2774AE",
    participants: m.speakers?.length || 0,
    actionItems: m.tasks?.length || 0,
    hasTranscript: !!m.transcript,
    hasSummary: !!m.executive_summary,
    flagged: false,
  };
}

interface MeetingsViewProps {
  meetings: BackendMeeting[];
  onSelectMeeting: (id: string) => void;
  onRefresh?: () => void;
}

export function MeetingsView({ meetings, onSelectMeeting, onRefresh }: MeetingsViewProps) {
  const [activeTab, setActiveTab] = useState("all");
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const allMeetings = useMemo(() => meetings.map(backendToMeetingFull), [meetings]);

  // Debounced search against backend
  useEffect(() => {
    if (!search || search.length < 2) {
      setSearchResults(null);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const response = await fetch(
          getApiUrl(`/api/meetings/search?q=${encodeURIComponent(search)}`),
          { headers: getApiHeaders() }
        );
        if (response.ok) {
          const data = await response.json();
          setSearchResults(data.results || []);
        }
      } catch (err) {
        console.error("Search failed:", err);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [search]);

  const filtered = allMeetings.filter((m) => {
    if (activeTab === "flagged" && !m.flagged) return false;
    if (activeTab === "week" && !["Today", "Yesterday"].includes(m.date)) return false;
    if (search && searchResults === null && !m.title.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const TABS = [
    { id: "all", label: "All", count: allMeetings.length },
    { id: "week", label: "This Week", count: allMeetings.filter((m) => ["Today", "Yesterday"].includes(m.date)).length },
    { id: "flagged", label: "Flagged", count: allMeetings.filter((m) => m.flagged).length },
  ];

  // Use search results or filtered meetings
  const displayMeetings = searchResults
    ? searchResults.map((r: any) => {
        const found = allMeetings.find((m) => m.id === r.meeting_id);
        return found || backendToMeetingFull({ id: r.meeting_id, title: r.title, date: r.date, speakers: [], transcript: "", nextSteps: "", duration: 0 });
      })
    : filtered;

  // Group by date
  const grouped: Record<string, MeetingFull[]> = {};
  displayMeetings.forEach((m) => {
    if (!grouped[m.date]) grouped[m.date] = [];
    grouped[m.date].push(m);
  });

  return (
    <div className="max-w-3xl space-y-4">
      {/* Search + Filter Bar */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
          <input
            type="text"
            placeholder="Search meetings..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-2 rounded-lg text-[12px] text-white/70 placeholder:text-white/20 outline-none"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.05)",
            }}
          />
          {isSearching && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3 border border-white/30 border-t-transparent rounded-full animate-spin" />
          )}
        </div>
        <button
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[11px] text-white/35 hover:text-white/50 transition-colors"
          style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}
        >
          <Filter size={11} />
          Filter
        </button>
        <button
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[11px] text-white/35 hover:text-white/50 transition-colors"
          style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}
        >
          <Download size={11} />
          Export
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1">
        {TABS.map((tab) => {
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
              {tab.id === "flagged" && <Flag size={10} />}
              {tab.label}
              <span
                className="text-[9px] px-1.5 py-[1px] rounded"
                style={{
                  background: isActive ? "rgba(39,116,174,0.15)" : "rgba(255,255,255,0.04)",
                  color: isActive ? "#2774AE" : "rgba(255,255,255,0.2)",
                }}
              >
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Meeting Groups */}
      {Object.entries(grouped).map(([date, dateMeetings]) => (
        <div key={date}>
          <div className="flex items-center gap-1.5 mb-1.5 px-1">
            <Calendar size={10} className="text-white/20" />
            <span className="text-[10px] text-white/25 uppercase tracking-wider">{date}</span>
            <div className="flex-1 h-px bg-white/[0.04]" />
          </div>
          <div className="space-y-0.5">
            {dateMeetings.map((m) => (
              <button
                key={m.id}
                onClick={() => onSelectMeeting(m.id)}
                className="w-full flex items-center gap-3 p-2.5 rounded-lg hover:bg-white/[0.03] transition-all group text-left"
              >
                <div className={ICON_COL} style={{ background: "rgba(255,255,255,0.025)" }}>
                  <FileText size={13} className="text-white/30 group-hover:text-white/50 transition-colors" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] text-white/75 truncate">{m.title}</span>
                    {m.flagged && <Flag size={9} className="text-[#FFD100] shrink-0" />}
                    <span
                      className="text-[8px] px-1.5 py-[1px] rounded-full shrink-0"
                      style={{ background: `${m.tagColor}15`, color: m.tagColor }}
                    >
                      {m.tag}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] text-white/25">{m.time}</span>
                    <span className="text-[10px] text-white/15">·</span>
                    <span className="text-[10px] text-white/25">{m.duration}</span>
                    {m.participants > 0 && (
                      <>
                        <span className="text-[10px] text-white/15">·</span>
                        <span className="flex items-center gap-0.5 text-[10px] text-white/20">
                          <Users size={8} /> {m.participants}
                        </span>
                      </>
                    )}
                    {m.actionItems > 0 && (
                      <>
                        <span className="text-[10px] text-white/15">·</span>
                        <span className="flex items-center gap-0.5 text-[10px] text-[#6dd58c]/50">
                          <Zap size={8} /> {m.actionItems}
                        </span>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  {m.hasSummary && (
                    <span className="w-5 h-5 rounded flex items-center justify-center" style={{ background: "rgba(139,92,246,0.08)" }}>
                      <Sparkles size={9} className="text-[#8b5cf6]/50" />
                    </span>
                  )}
                  {m.hasTranscript && (
                    <span className="w-5 h-5 rounded flex items-center justify-center" style={{ background: "rgba(39,116,174,0.08)" }}>
                      <FileText size={9} className="text-[#2774AE]/50" />
                    </span>
                  )}
                  <ChevronRight size={12} className="text-white/10 group-hover:text-white/25 transition-colors" />
                </div>
              </button>
            ))}
          </div>
        </div>
      ))}

      {displayMeetings.length === 0 && (
        <div className="text-center py-12">
          <Search size={20} className="text-white/15 mx-auto mb-2" />
          <p className="text-[12px] text-white/25">
            {search ? "No meetings match your search" : "No meetings recorded yet"}
          </p>
        </div>
      )}

      {/* Summary footer */}
      <div
        className="flex items-center justify-between px-3 py-2 rounded-lg"
        style={{ background: "rgba(255,255,255,0.015)", border: "1px solid rgba(255,255,255,0.03)" }}
      >
        <span className="text-[10px] text-white/20">
          {displayMeetings.length} meeting{displayMeetings.length !== 1 ? "s" : ""} · {displayMeetings.reduce((a, m) => a + m.actionItems, 0)} action items
        </span>
        <span className="text-[9px] text-white/15">Showing {activeTab === "all" ? "all time" : activeTab === "week" ? "this week" : "flagged only"}</span>
      </div>
    </div>
  );
}
