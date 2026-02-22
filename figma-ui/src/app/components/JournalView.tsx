import { useState, useEffect } from "react";
import {
  BookOpen,
  Calendar,
  Clock,
  ChevronRight,
  Sparkles,
  Plus,
  Search,
  Edit3,
  MessageSquare,
  Lightbulb,
  TrendingUp,
  Heart,
  Zap,
  FileText,
  Loader2,
} from "lucide-react";
import { getApiUrl, getApiHeaders } from "../config/api";

const ICON_COL = "w-8 h-8 shrink-0 rounded-lg flex items-center justify-center";

interface JournalEntry {
  id: string;
  date: string;
  timestamp: string;
  entry: string;
  ai_suggestions: string;
  // UI-derived fields
  title: string;
  preview: string;
  mood: "productive" | "reflective" | "energized" | "neutral";
  tags: string[];
}

const MOOD_CONFIG = {
  productive: { icon: <Zap size={10} />, color: "#6dd58c", label: "Productive" },
  reflective: { icon: <Lightbulb size={10} />, color: "#8b5cf6", label: "Reflective" },
  energized: { icon: <TrendingUp size={10} />, color: "#FFD100", label: "Energized" },
  neutral: { icon: <Heart size={10} />, color: "#2774AE", label: "Neutral" },
};

const MOODS: Array<JournalEntry["mood"]> = ["productive", "reflective", "energized", "neutral"];

const AI_PROMPTS = [
  { icon: <Lightbulb size={11} />, text: "What patterns do you see across this week's meetings?" },
  { icon: <TrendingUp size={11} />, text: "What decisions had the most downstream impact?" },
  { icon: <Heart size={11} />, text: "Which conversations energized or drained you?" },
  { icon: <Zap size={11} />, text: "What action items keep recurring across meetings?" },
];

function deriveTitle(entry: string): string {
  const firstLine = entry.split("\n")[0].trim();
  if (firstLine.length <= 60) return firstLine || "Untitled Entry";
  return firstLine.substring(0, 57) + "...";
}

function derivePreview(entry: string): string {
  const lines = entry.split("\n").filter((l) => l.trim());
  const preview = lines.slice(0, 3).join(" ").trim();
  if (preview.length <= 150) return preview;
  return preview.substring(0, 147) + "...";
}

function formatEntryDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const entryDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const diffDays = Math.floor((today.getTime() - entryDay.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}

function backendToJournalEntry(raw: any, index: number): JournalEntry {
  return {
    id: raw.id,
    date: formatEntryDate(raw.timestamp || raw.date),
    timestamp: raw.timestamp || raw.date,
    entry: raw.entry,
    ai_suggestions: raw.ai_suggestions || "",
    title: deriveTitle(raw.entry),
    preview: derivePreview(raw.entry),
    mood: MOODS[index % MOODS.length],
    tags: [],
  };
}

export function JournalView() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [showNewEntry, setShowNewEntry] = useState(false);
  const [newEntryText, setNewEntryText] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // Load entries from backend
  useEffect(() => {
    fetchEntries();
  }, []);

  async function fetchEntries() {
    try {
      const res = await fetch(getApiUrl("/api/journal"), { headers: getApiHeaders() });
      if (res.ok) {
        const data = await res.json();
        const mapped = (data.entries || []).map(backendToJournalEntry);
        setEntries(mapped);
      }
    } catch (err) {
      console.error("Failed to load journal entries:", err);
    } finally {
      setIsLoading(false);
    }
  }

  async function createEntry() {
    if (!newEntryText.trim()) return;
    setIsSaving(true);
    try {
      const res = await fetch(getApiUrl("/api/journal"), {
        method: "POST",
        headers: getApiHeaders(),
        body: JSON.stringify({ entry: newEntryText.trim() }),
      });
      if (res.ok) {
        const data = await res.json();
        const newEntry = backendToJournalEntry(data.journalEntry, 0);
        setEntries((prev) => [newEntry, ...prev]);
        setNewEntryText("");
        setShowNewEntry(false);
        setSelectedEntry(newEntry.id);
      }
    } catch (err) {
      console.error("Failed to create journal entry:", err);
    } finally {
      setIsSaving(false);
    }
  }

  const activeEntry = entries.find((e) => e.id === selectedEntry);

  const filteredEntries = entries.filter(
    (e) =>
      !searchQuery ||
      e.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.preview.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-full -m-5">
      {/* Entry List */}
      <div
        className="w-[280px] shrink-0 flex flex-col"
        style={{ borderRight: "1px solid rgba(255,255,255,0.04)" }}
      >
        {/* Search */}
        <div className="p-3 pb-2">
          <div className="relative mb-2">
            <Search size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-white/20" />
            <input
              type="text"
              placeholder="Search journal..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-7 pr-2.5 py-1.5 rounded-md text-[11px] text-white/60 placeholder:text-white/15 outline-none"
              style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.04)" }}
            />
          </div>
          <button
            onClick={() => setShowNewEntry(true)}
            className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-[11px] transition-all hover:brightness-110"
            style={{
              background: "linear-gradient(135deg, rgba(255,209,0,0.1), rgba(255,209,0,0.05))",
              border: "1px solid rgba(255,209,0,0.12)",
              color: "#FFD100",
            }}
          >
            <Plus size={11} />
            New Entry
          </button>
        </div>

        {/* New Entry Inline Form */}
        {showNewEntry && (
          <div className="px-3 pb-2">
            <textarea
              autoFocus
              rows={4}
              value={newEntryText}
              onChange={(e) => setNewEntryText(e.target.value)}
              placeholder="Write your thoughts..."
              className="w-full p-2 rounded-md text-[11px] text-white/60 placeholder:text-white/15 outline-none resize-none"
              style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
            />
            <div className="flex gap-1.5 mt-1.5">
              <button
                onClick={createEntry}
                disabled={isSaving || !newEntryText.trim()}
                className="flex-1 flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-md text-[10px] transition-all disabled:opacity-30"
                style={{ background: "rgba(109,213,140,0.1)", color: "#6dd58c", border: "1px solid rgba(109,213,140,0.15)" }}
              >
                {isSaving ? <Loader2 size={10} className="animate-spin" /> : <Plus size={10} />}
                Save
              </button>
              <button
                onClick={() => { setShowNewEntry(false); setNewEntryText(""); }}
                className="px-2.5 py-1.5 rounded-md text-[10px] text-white/30 hover:text-white/50 transition-colors"
                style={{ background: "rgba(255,255,255,0.03)" }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Entries */}
        <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={16} className="animate-spin text-white/20" />
            </div>
          ) : filteredEntries.length === 0 ? (
            <div className="text-center py-8">
              <BookOpen size={16} className="text-white/15 mx-auto mb-2" />
              <p className="text-[10px] text-white/20">
                {searchQuery ? "No entries match your search" : "No journal entries yet"}
              </p>
            </div>
          ) : (
            filteredEntries.map((entry) => {
              const isActive = selectedEntry === entry.id;
              const moodCfg = MOOD_CONFIG[entry.mood];
              return (
                <button
                  key={entry.id}
                  onClick={() => setSelectedEntry(entry.id)}
                  className="w-full text-left p-2.5 rounded-lg transition-all"
                  style={{
                    background: isActive ? "rgba(39,116,174,0.08)" : "transparent",
                  }}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="text-[9px] text-white/20">{entry.date}</span>
                    <span
                      className="flex items-center gap-0.5 text-[8px] px-1.5 py-[1px] rounded-full ml-auto"
                      style={{ background: `${moodCfg.color}12`, color: moodCfg.color }}
                    >
                      {moodCfg.icon} {moodCfg.label}
                    </span>
                  </div>
                  <div className="text-[12px] text-white/70 mb-0.5 truncate">{entry.title}</div>
                  <div className="text-[10px] text-white/25 line-clamp-2">{entry.preview}</div>
                  {entry.ai_suggestions && (
                    <div className="flex items-center gap-0.5 mt-1.5">
                      <span className="flex items-center gap-0.5 text-[9px] text-[#8b5cf6]/40">
                        <Sparkles size={8} /> AI Insights
                      </span>
                    </div>
                  )}
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Entry Detail / Empty State */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {activeEntry ? (
          <EntryDetail entry={activeEntry} onUpdate={(updated) => {
            setEntries((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
          }} />
        ) : (
          <EmptyJournal />
        )}
      </div>
    </div>
  );
}

/* Entry Detail */
function EntryDetail({ entry, onUpdate }: { entry: JournalEntry; onUpdate: (e: JournalEntry) => void }) {
  const moodCfg = MOOD_CONFIG[entry.mood];
  const [isOptimizing, setIsOptimizing] = useState(false);

  async function optimizeEntry() {
    setIsOptimizing(true);
    try {
      const res = await fetch(getApiUrl(`/api/journal/${entry.id}/optimize`), {
        method: "PUT",
        headers: getApiHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        onUpdate({ ...entry, ai_suggestions: data.journalEntry?.suggestions || "" });
      }
    } catch (err) {
      console.error("Failed to optimize entry:", err);
    } finally {
      setIsOptimizing(false);
    }
  }

  return (
    <div className="flex-1 overflow-y-auto p-5">
      <div className="max-w-lg">
        {/* Date & mood */}
        <div className="flex items-center gap-2 mb-3">
          <span className="flex items-center gap-1 text-[10px] text-white/25">
            <Calendar size={9} /> {entry.date}
          </span>
          <span
            className="flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded-full"
            style={{ background: `${moodCfg.color}12`, color: moodCfg.color }}
          >
            {moodCfg.icon} {moodCfg.label}
          </span>
          <button className="ml-auto p-1.5 rounded-md hover:bg-white/[0.04] transition-colors">
            <Edit3 size={11} className="text-white/25" />
          </button>
        </div>

        <h2 className="text-white/85 mb-3">{entry.title}</h2>

        {/* Content */}
        <div className="text-[13px] text-white/50 mb-5 space-y-3">
          {entry.entry.split("\n").filter((l) => l.trim()).map((paragraph, i) => (
            <p key={i}>{paragraph}</p>
          ))}
        </div>

        {/* AI Insights */}
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <Sparkles size={10} className="text-[#8b5cf6]" />
            <span className="text-[10px] text-white/25 uppercase tracking-wider">AI Insights</span>
          </div>
          {entry.ai_suggestions ? (
            <div
              className="p-3 rounded-lg text-[11px] text-white/40"
              style={{ background: "rgba(139,92,246,0.04)", border: "1px solid rgba(139,92,246,0.08)" }}
            >
              {entry.ai_suggestions.split("\n").filter((l) => l.trim()).map((line, i) => (
                <p key={i} className="mb-1.5 last:mb-0">{line}</p>
              ))}
            </div>
          ) : (
            <button
              onClick={optimizeEntry}
              disabled={isOptimizing}
              className="flex items-center gap-2 p-3 rounded-lg text-[11px] transition-all hover:brightness-110 w-full text-left disabled:opacity-50"
              style={{ background: "rgba(139,92,246,0.04)", border: "1px solid rgba(139,92,246,0.08)", color: "#8b5cf6" }}
            >
              {isOptimizing ? (
                <>
                  <Loader2 size={11} className="animate-spin" />
                  Generating insights...
                </>
              ) : (
                <>
                  <Sparkles size={11} />
                  Generate AI insights for this entry
                </>
              )}
            </button>
          )}
        </div>

        {/* Tags */}
        {entry.tags.length > 0 && (
          <div className="mt-4 flex items-center gap-1.5">
            {entry.tags.map((tag) => (
              <span
                key={tag}
                className="text-[9px] px-2 py-0.5 rounded-md text-white/25"
                style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.04)" }}
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* Empty Journal State */
function EmptyJournal() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-8">
      <div className="max-w-sm text-center">
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4"
          style={{ background: "rgba(255,209,0,0.08)" }}
        >
          <BookOpen size={20} className="text-[#FFD100]" />
        </div>
        <h3 className="text-white/60 mb-1">Reflect on your meetings</h3>
        <p className="text-[12px] text-white/25 mb-5">
          Select an entry to read, or try an AI-powered prompt to start reflecting.
        </p>

        {/* AI prompts */}
        <div className="space-y-1.5 text-left">
          {AI_PROMPTS.map((prompt, i) => (
            <button
              key={i}
              className="w-full flex items-center gap-2.5 p-2.5 rounded-lg hover:bg-white/[0.03] transition-all text-left"
              style={{ background: "rgba(255,255,255,0.015)", border: "1px solid rgba(255,255,255,0.03)" }}
            >
              <div
                className="w-6 h-6 rounded-md flex items-center justify-center shrink-0"
                style={{ background: "rgba(139,92,246,0.1)", color: "#8b5cf6" }}
              >
                {prompt.icon}
              </div>
              <span className="text-[11px] text-white/40">{prompt.text}</span>
              <ChevronRight size={10} className="text-white/10 ml-auto shrink-0" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
