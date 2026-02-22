import { useState, useEffect } from "react";
import {
  Settings,
  Shield,
  Mic,
  Monitor,
  KeyRound,
  Sparkles,
  Plug,
  Calendar,
  CalendarDays,
  FileText,
  MessageSquare,
  Zap,
  Check,
  Eye,
  EyeOff,
  ExternalLink,
  Globe,
  Bell,
  Palette,
  HardDrive,
  Info,
  RotateCcw,
  Trash2,
  Loader2,
} from "lucide-react";
import { getApiUrl, getApiHeaders } from "../config/api";

const ICON_COL = "w-8 h-8 shrink-0 rounded-lg flex items-center justify-center";

interface SettingSection {
  id: string;
  icon: React.ReactNode;
  label: string;
  color: string;
}

const SECTIONS: SettingSection[] = [
  { id: "general", icon: <Settings size={13} />, label: "General", color: "#ffffff" },
  { id: "permissions", icon: <Shield size={13} />, label: "Permissions", color: "#2774AE" },
  { id: "ai", icon: <Sparkles size={13} />, label: "AI Config", color: "#FFD100" },
  { id: "integrations", icon: <Plug size={13} />, label: "Integrations", color: "#6dd58c" },
  { id: "notifications", icon: <Bell size={13} />, label: "Notifications", color: "#f97316" },
  { id: "storage", icon: <HardDrive size={13} />, label: "Storage", color: "#8b5cf6" },
  { id: "about", icon: <Info size={13} />, label: "About", color: "#ffffff" },
];

/* ─── Toggle Component ─── */
function Toggle({ enabled, onToggle }: { enabled: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      className="w-8 h-[18px] rounded-full transition-all relative shrink-0"
      style={{
        background: enabled ? "rgba(39,116,174,0.4)" : "rgba(255,255,255,0.08)",
        border: `1px solid ${enabled ? "rgba(39,116,174,0.3)" : "rgba(255,255,255,0.06)"}`,
      }}
    >
      <div
        className="w-3.5 h-3.5 rounded-full absolute top-[1px] transition-all"
        style={{
          background: enabled ? "#2774AE" : "rgba(255,255,255,0.3)",
          left: enabled ? "15px" : "1px",
        }}
      />
    </button>
  );
}

/* ─── Setting Row ─── */
function SettingRow({
  icon,
  iconBg,
  title,
  desc,
  right,
}: {
  icon: React.ReactNode;
  iconBg: string;
  title: string;
  desc: string;
  right: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-3 p-2.5 rounded-lg" style={{ background: "rgba(255,255,255,0.015)" }}>
      <div className={ICON_COL} style={{ background: iconBg }}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[12px] text-white/70">{title}</div>
        <div className="text-[10px] text-white/25">{desc}</div>
      </div>
      {right}
    </div>
  );
}

export function SettingsView() {
  const [activeSection, setActiveSection] = useState("general");

  // General
  const [launchOnStartup, setLaunchOnStartup] = useState(true);
  const [menuBarIcon, setMenuBarIcon] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [language, setLanguage] = useState("en");

  // Permissions
  const [micEnabled, setMicEnabled] = useState(true);
  const [sysAudioEnabled, setSysAudioEnabled] = useState(true);
  const [screenEnabled, setScreenEnabled] = useState(false);

  // AI - wired to backend
  const [aiProvider, setAiProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [autoTranscribe, setAutoTranscribe] = useState(true);
  const [autoSummarize, setAutoSummarize] = useState(true);
  const [isConfigured, setIsConfigured] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  // Integrations
  const [gcalConnected, setGcalConnected] = useState(false);
  const [outlookConnected, setOutlookConnected] = useState(false);
  const [notionConnected, setNotionConnected] = useState(false);
  const [slackConnected, setSlackConnected] = useState(false);
  const [linearConnected, setLinearConnected] = useState(false);

  // Notifications
  const [meetingReminders, setMeetingReminders] = useState(true);
  const [transcriptReady, setTranscriptReady] = useState(true);
  const [actionDue, setActionDue] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);

  // Load settings from backend
  useEffect(() => {
    async function loadSettings() {
      try {
        const response = await fetch(getApiUrl("/api/settings"), { headers: getApiHeaders() });
        if (response.ok) {
          const data = await response.json();
          setIsConfigured(data.has_gemini_key || false);
          if (data.llm_provider) {
            setAiProvider(data.llm_provider === "gemini" ? "google" : data.llm_provider);
          }
        }
      } catch (err) {
        console.error("Failed to load settings:", err);
      }
    }
    loadSettings();
  }, []);

  const handleSaveApiKey = async () => {
    if (!apiKey.trim()) {
      setSaveMessage("Please enter an API key");
      return;
    }
    setIsSaving(true);
    setSaveMessage("");

    try {
      const response = await fetch(getApiUrl("/api/settings"), {
        method: "PUT",
        headers: getApiHeaders(),
        body: JSON.stringify({
          gemini_api_key: aiProvider === "google" ? apiKey : undefined,
          llm_provider: aiProvider === "google" ? "gemini" : aiProvider,
        }),
      });

      if (response.ok) {
        setIsConfigured(true);
        setSaveMessage("API key saved successfully!");
        setApiKey("");
        setTimeout(() => setSaveMessage(""), 3000);
      } else {
        const error = await response.json();
        setSaveMessage(`Error: ${error.detail || "Failed to save API key"}`);
      }
    } catch (err) {
      setSaveMessage("Network error: Is the API server running?");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex h-full -m-5">
      {/* ─── Section List ─── */}
      <div className="w-[200px] shrink-0 p-3" style={{ borderRight: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="space-y-0.5">
          {SECTIONS.map((s) => {
            const isActive = activeSection === s.id;
            return (
              <button
                key={s.id}
                onClick={() => setActiveSection(s.id)}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg transition-all text-left"
                style={{ background: isActive ? "rgba(39,116,174,0.1)" : "transparent" }}
              >
                <div
                  className="w-6 h-6 rounded-md flex items-center justify-center shrink-0"
                  style={{
                    background: `${s.color}${isActive ? "18" : "08"}`,
                    color: isActive ? s.color : "rgba(255,255,255,0.25)",
                  }}
                >
                  {s.icon}
                </div>
                <span className="text-[11px]" style={{ color: isActive ? "rgba(255,255,255,0.7)" : "rgba(255,255,255,0.35)" }}>
                  {s.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ─── Content ─── */}
      <div className="flex-1 overflow-y-auto p-5">
        <div className="max-w-lg">
          {activeSection === "general" && (
            <GeneralSection
              launchOnStartup={launchOnStartup} setLaunchOnStartup={setLaunchOnStartup}
              menuBarIcon={menuBarIcon} setMenuBarIcon={setMenuBarIcon}
              darkMode={darkMode} setDarkMode={setDarkMode}
              language={language} setLanguage={setLanguage}
            />
          )}
          {activeSection === "permissions" && (
            <PermissionsSection
              mic={micEnabled} setMic={setMicEnabled}
              sysAudio={sysAudioEnabled} setSysAudio={setSysAudioEnabled}
              screen={screenEnabled} setScreen={setScreenEnabled}
            />
          )}
          {activeSection === "ai" && (
            <AISection
              provider={aiProvider} setProvider={setAiProvider}
              apiKey={apiKey} setApiKey={setApiKey}
              showKey={showKey} setShowKey={setShowKey}
              autoTranscribe={autoTranscribe} setAutoTranscribe={setAutoTranscribe}
              autoSummarize={autoSummarize} setAutoSummarize={setAutoSummarize}
              isConfigured={isConfigured}
              isSaving={isSaving}
              saveMessage={saveMessage}
              onSave={handleSaveApiKey}
            />
          )}
          {activeSection === "integrations" && (
            <IntegrationsSection
              gcal={gcalConnected} setGcal={setGcalConnected}
              outlook={outlookConnected} setOutlook={setOutlookConnected}
              notion={notionConnected} setNotion={setNotionConnected}
              slack={slackConnected} setSlack={setSlackConnected}
              linear={linearConnected} setLinear={setLinearConnected}
            />
          )}
          {activeSection === "notifications" && (
            <NotificationsSection
              meetingReminders={meetingReminders} setMeetingReminders={setMeetingReminders}
              transcriptReady={transcriptReady} setTranscriptReady={setTranscriptReady}
              actionDue={actionDue} setActionDue={setActionDue}
              soundEnabled={soundEnabled} setSoundEnabled={setSoundEnabled}
            />
          )}
          {activeSection === "storage" && <StorageSection />}
          {activeSection === "about" && <AboutSection />}
        </div>
      </div>
    </div>
  );
}

/* ═══ General ═══ */
function GeneralSection({ launchOnStartup, setLaunchOnStartup, menuBarIcon, setMenuBarIcon, darkMode, setDarkMode, language, setLanguage }: any) {
  return (
    <div className="space-y-4">
      <SectionHeader icon={<Settings size={14} />} title="General" desc="App behavior and appearance" color="rgba(255,255,255,0.15)" />
      <div className="space-y-1.5">
        <SettingRow icon={<RotateCcw size={13} className="text-white/40" />} iconBg="rgba(255,255,255,0.04)" title="Launch on startup" desc="Start NotSure when your Mac boots" right={<Toggle enabled={launchOnStartup} onToggle={() => setLaunchOnStartup(!launchOnStartup)} />} />
        <SettingRow icon={<Monitor size={13} className="text-white/40" />} iconBg="rgba(255,255,255,0.04)" title="Show in menu bar" desc="Display NotSure icon in the menu bar" right={<Toggle enabled={menuBarIcon} onToggle={() => setMenuBarIcon(!menuBarIcon)} />} />
        <SettingRow icon={<Palette size={13} className="text-white/40" />} iconBg="rgba(255,255,255,0.04)" title="Dark mode" desc="Use dark theme (recommended)" right={<Toggle enabled={darkMode} onToggle={() => setDarkMode(!darkMode)} />} />
        <SettingRow icon={<Globe size={13} className="text-white/40" />} iconBg="rgba(255,255,255,0.04)" title="Language" desc="Interface and transcription language" right={
          <select value={language} onChange={(e) => setLanguage(e.target.value)} className="text-[10px] text-white/50 bg-white/[0.04] border border-white/[0.06] rounded px-2 py-1 outline-none">
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="ja">Japanese</option>
          </select>
        } />
      </div>
    </div>
  );
}

/* ═══ Permissions ═══ */
function PermissionsSection({ mic, setMic, sysAudio, setSysAudio, screen, setScreen }: any) {
  return (
    <div className="space-y-4">
      <SectionHeader icon={<Shield size={14} />} title="Permissions" desc="System access for recording" color="rgba(39,116,174,0.15)" />
      <div className="space-y-1.5">
        <SettingRow icon={<Mic size={13} className={mic ? "text-[#6dd58c]" : "text-white/30"} />} iconBg={mic ? "rgba(109,213,140,0.1)" : "rgba(255,255,255,0.04)"} title="Microphone" desc="Capture your voice during meetings" right={<span className="flex items-center gap-1 text-[10px]" style={{ color: mic ? "#6dd58c" : "rgba(255,255,255,0.25)" }}>{mic ? <><Check size={10} /> Granted</> : "Denied"}</span>} />
        <SettingRow icon={<Monitor size={13} className={sysAudio ? "text-[#6dd58c]" : "text-white/30"} />} iconBg={sysAudio ? "rgba(109,213,140,0.1)" : "rgba(255,255,255,0.04)"} title="System Audio" desc="Capture audio from other participants" right={<span className="flex items-center gap-1 text-[10px]" style={{ color: sysAudio ? "#6dd58c" : "rgba(255,255,255,0.25)" }}>{sysAudio ? <><Check size={10} /> Granted</> : "Denied"}</span>} />
        <SettingRow icon={<Monitor size={13} className={screen ? "text-[#6dd58c]" : "text-white/30"} />} iconBg={screen ? "rgba(109,213,140,0.1)" : "rgba(255,255,255,0.04)"} title="Screen Recording" desc="Optional — capture shared screens" right={<Toggle enabled={screen} onToggle={() => setScreen(!screen)} />} />
      </div>
      <p className="text-[9px] text-white/15 flex items-center gap-1"><Shield size={8} /> Open System Preferences to manage permissions</p>
    </div>
  );
}

/* ═══ AI Config ═══ */
function AISection({ provider, setProvider, apiKey, setApiKey, showKey, setShowKey, autoTranscribe, setAutoTranscribe, autoSummarize, setAutoSummarize, isConfigured, isSaving, saveMessage, onSave }: any) {
  return (
    <div className="space-y-4">
      <SectionHeader icon={<Sparkles size={14} />} title="AI Configuration" desc="Transcription and summarization settings" color="rgba(255,209,0,0.12)" />

      {/* Status indicator */}
      {isConfigured && (
        <div className="flex items-center gap-1.5 p-2 rounded-lg" style={{ background: "rgba(109,213,140,0.06)", border: "1px solid rgba(109,213,140,0.1)" }}>
          <Check size={10} className="text-[#6dd58c]" />
          <span className="text-[10px] text-[#6dd58c]">API key configured</span>
        </div>
      )}

      {/* Provider */}
      <div>
        <span className="text-[10px] text-white/25 uppercase tracking-wider mb-1.5 block">Provider</span>
        <div className="space-y-1">
          {[
            { id: "google", label: "Google (Gemini)", desc: "Gemini 2.0 Flash", color: "#4285f4" },
            { id: "openai", label: "OpenAI", desc: "GPT-4o / Whisper", color: "#10a37f" },
            { id: "anthropic", label: "Anthropic", desc: "Claude 3.5 Sonnet", color: "#d97706" },
            { id: "local", label: "Local Models", desc: "Whisper.cpp + Ollama", color: "#8b5cf6" },
          ].map((p) => {
            const isActive = provider === p.id;
            return (
              <button key={p.id} onClick={() => setProvider(p.id)} className="w-full flex items-center gap-2.5 p-2.5 rounded-lg transition-all text-left" style={{ background: isActive ? `${p.color}10` : "rgba(255,255,255,0.015)", border: `1px solid ${isActive ? `${p.color}20` : "rgba(255,255,255,0.03)"}` }}>
                <div className="w-6 h-6 rounded-md flex items-center justify-center" style={{ background: `${p.color}18`, color: p.color }}><Zap size={11} /></div>
                <div className="flex-1">
                  <span className="text-[11px] text-white/70">{p.label}</span>
                  <div className="text-[9px] text-white/20">{p.desc}</div>
                </div>
                <div className="w-3.5 h-3.5 rounded-full border-2 flex items-center justify-center" style={{ borderColor: isActive ? p.color : "rgba(255,255,255,0.1)" }}>
                  {isActive && <div className="w-1.5 h-1.5 rounded-full" style={{ background: p.color }} />}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* API Key */}
      {provider !== "local" && (
        <div>
          <label className="text-[10px] text-white/25 flex items-center gap-1 mb-1.5"><KeyRound size={9} /> API Key</label>
          <div className="relative mb-2">
            <input type={showKey ? "text" : "password"} value={apiKey} onChange={(e) => setApiKey(e.target.value)} className="w-full px-3 py-2 rounded-lg text-[11px] text-white/60 placeholder:text-white/15 outline-none font-mono pr-10" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }} placeholder={provider === "google" ? "AIza..." : provider === "openai" ? "sk-..." : "sk-ant-..."} />
            <button onClick={() => setShowKey(!showKey)} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-white/20">
              {showKey ? <EyeOff size={12} /> : <Eye size={12} />}
            </button>
          </div>
          <button onClick={onSave} disabled={isSaving || !apiKey.trim()} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] transition-all disabled:opacity-40" style={{ background: "rgba(39,116,174,0.15)", border: "1px solid rgba(39,116,174,0.2)", color: "#2774AE" }}>
            {isSaving && <Loader2 size={10} className="animate-spin" />}
            Save API Key
          </button>
          {saveMessage && (
            <p className={`text-[10px] mt-1.5 ${saveMessage.includes("Error") || saveMessage.includes("Network") ? "text-red-400" : "text-[#6dd58c]"}`}>
              {saveMessage}
            </p>
          )}
        </div>
      )}

      {/* Auto features */}
      <div>
        <span className="text-[10px] text-white/25 uppercase tracking-wider mb-1.5 block">Automation</span>
        <div className="space-y-1.5">
          <SettingRow icon={<FileText size={13} className="text-[#2774AE]" />} iconBg="rgba(39,116,174,0.1)" title="Auto-transcribe" desc="Transcribe recordings automatically" right={<Toggle enabled={autoTranscribe} onToggle={() => setAutoTranscribe(!autoTranscribe)} />} />
          <SettingRow icon={<Sparkles size={13} className="text-[#FFD100]" />} iconBg="rgba(255,209,0,0.1)" title="Auto-summarize" desc="Generate AI summary after each meeting" right={<Toggle enabled={autoSummarize} onToggle={() => setAutoSummarize(!autoSummarize)} />} />
        </div>
      </div>
    </div>
  );
}

/* ═══ Integrations ═══ */
function IntegrationsSection({ gcal, setGcal, outlook, setOutlook, notion, setNotion, slack, setSlack, linear, setLinear }: any) {
  const items = [
    { label: "Google Calendar", desc: "Auto-detect meetings", icon: <Calendar size={13} />, color: "#3b82f6", connected: gcal, toggle: () => setGcal(!gcal) },
    { label: "Outlook Calendar", desc: "Sync from Microsoft 365", icon: <CalendarDays size={13} />, color: "#0078d4", connected: outlook, toggle: () => setOutlook(!outlook) },
    { label: "Notion", desc: "Export summaries as pages", icon: <FileText size={13} />, color: "#ffffff", connected: notion, toggle: () => setNotion(!notion) },
    { label: "Slack", desc: "Post to channels", icon: <MessageSquare size={13} />, color: "#e01e5a", connected: slack, toggle: () => setSlack(!slack) },
    { label: "Linear", desc: "Create issues from actions", icon: <Zap size={13} />, color: "#5e6ad2", connected: linear, toggle: () => setLinear(!linear) },
  ];
  const connectedCount = items.filter((i) => i.connected).length;

  return (
    <div className="space-y-4">
      <SectionHeader icon={<Plug size={14} />} title="Integrations" desc={`${connectedCount} connected`} color="rgba(109,213,140,0.12)" />
      <div className="space-y-1.5">
        {items.map((item) => (
          <SettingRow key={item.label} icon={<span style={{ color: item.color }}>{item.icon}</span>} iconBg={`${item.color}12`} title={item.label} desc={item.desc} right={
            <button onClick={item.toggle} className="flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] transition-all" style={{ background: item.connected ? `${item.color}15` : "rgba(255,255,255,0.03)", color: item.connected ? item.color : "rgba(255,255,255,0.3)", border: `1px solid ${item.connected ? `${item.color}25` : "rgba(255,255,255,0.05)"}` }}>
              {item.connected ? <><Check size={9} /> Connected</> : <><Plug size={9} /> Connect</>}
            </button>
          } />
        ))}
      </div>
    </div>
  );
}

/* ═══ Notifications ═══ */
function NotificationsSection({ meetingReminders, setMeetingReminders, transcriptReady, setTranscriptReady, actionDue, setActionDue, soundEnabled, setSoundEnabled }: any) {
  return (
    <div className="space-y-4">
      <SectionHeader icon={<Bell size={14} />} title="Notifications" desc="How NotSure alerts you" color="rgba(249,115,22,0.12)" />
      <div className="space-y-1.5">
        <SettingRow icon={<Calendar size={13} className="text-[#3b82f6]" />} iconBg="rgba(59,130,246,0.1)" title="Meeting reminders" desc="Notify before scheduled meetings" right={<Toggle enabled={meetingReminders} onToggle={() => setMeetingReminders(!meetingReminders)} />} />
        <SettingRow icon={<FileText size={13} className="text-[#2774AE]" />} iconBg="rgba(39,116,174,0.1)" title="Transcript ready" desc="Notify when transcription completes" right={<Toggle enabled={transcriptReady} onToggle={() => setTranscriptReady(!transcriptReady)} />} />
        <SettingRow icon={<Zap size={13} className="text-[#FFD100]" />} iconBg="rgba(255,209,0,0.1)" title="Action item due" desc="Remind you of upcoming deadlines" right={<Toggle enabled={actionDue} onToggle={() => setActionDue(!actionDue)} />} />
        <SettingRow icon={<Bell size={13} className="text-[#f97316]" />} iconBg="rgba(249,115,22,0.1)" title="Notification sounds" desc="Play sounds for notifications" right={<Toggle enabled={soundEnabled} onToggle={() => setSoundEnabled(!soundEnabled)} />} />
      </div>
    </div>
  );
}

/* ═══ Storage ═══ */
function StorageSection() {
  const storageItems = [
    { label: "Recordings", size: "—", color: "#2774AE", pct: 0 },
    { label: "Transcripts", size: "—", color: "#FFD100", pct: 0 },
    { label: "Summaries", size: "—", color: "#6dd58c", pct: 0 },
    { label: "Cache", size: "—", color: "#8b5cf6", pct: 0 },
  ];

  return (
    <div className="space-y-4">
      <SectionHeader icon={<HardDrive size={14} />} title="Storage" desc="Local storage usage" color="rgba(139,92,246,0.12)" />
      <div>
        <div className="h-2 rounded-full bg-white/[0.04] overflow-hidden flex">
          {storageItems.map((item) => (
            <div key={item.label} className="h-full" style={{ width: `${item.pct}%`, background: item.color, opacity: 0.7 }} />
          ))}
        </div>
        <div className="flex items-center gap-3 mt-2">
          {storageItems.map((item) => (
            <div key={item.label} className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: item.color }} />
              <span className="text-[9px] text-white/25">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="space-y-1.5">
        <SettingRow icon={<Trash2 size={13} className="text-white/30" />} iconBg="rgba(255,255,255,0.04)" title="Clear cache" desc="Remove temporary files" right={<button className="text-[10px] text-white/30 hover:text-white/50 px-2 py-1 rounded-md transition-colors" style={{ background: "rgba(255,255,255,0.03)" }}>Clear</button>} />
        <SettingRow icon={<HardDrive size={13} className="text-white/30" />} iconBg="rgba(255,255,255,0.04)" title="Storage location" desc="~/Documents/Audio Recordings" right={<button className="text-[10px] text-white/30 hover:text-white/50 px-2 py-1 rounded-md transition-colors" style={{ background: "rgba(255,255,255,0.03)" }}>Change</button>} />
      </div>
    </div>
  );
}

/* ═══ About ═══ */
function AboutSection() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#2774AE] to-[#1a5a8e] flex items-center justify-center" style={{ boxShadow: "0 4px 16px rgba(39,116,174,0.2)" }}>
          <svg width="22" height="22" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5" stroke="white" strokeWidth="1.2" fill="none" /><circle cx="8" cy="8" r="2" fill="white" /></svg>
        </div>
        <div>
          <div className="text-white/80">NotSure</div>
          <div className="text-[11px] text-white/30">Version 0.1.0 (Beta)</div>
        </div>
      </div>
      <div className="space-y-1.5">
        {[
          { label: "Developer", value: "mhopesd" },
          { label: "License", value: "MIT" },
          { label: "Runtime", value: "Electron 28 + React 18" },
        ].map((item) => (
          <div key={item.label} className="flex items-center justify-between p-2.5 rounded-lg" style={{ background: "rgba(255,255,255,0.015)" }}>
            <span className="text-[11px] text-white/40">{item.label}</span>
            <span className="text-[11px] text-white/55 font-mono">{item.value}</span>
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <a href="#" className="flex items-center gap-1 text-[10px] text-[#2774AE] hover:text-[#3a8fd4] transition-colors">GitHub <ExternalLink size={8} /></a>
        <span className="text-white/10">·</span>
        <a href="#" className="text-[10px] text-white/25 hover:text-white/40 transition-colors">Documentation</a>
        <span className="text-white/10">·</span>
        <a href="#" className="text-[10px] text-white/25 hover:text-white/40 transition-colors">Report Issue</a>
      </div>
      <p className="text-[9px] text-white/15">Built with care. All recordings and data stay on your device.</p>
    </div>
  );
}

/* ─── Section Header ─── */
function SectionHeader({ icon, title, desc, color }: { icon: React.ReactNode; title: string; desc: string; color: string }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className={ICON_COL} style={{ background: color }}><span className="text-white/60">{icon}</span></div>
      <div>
        <h3 className="text-white/80">{title}</h3>
        <p className="text-[10px] text-white/25">{desc}</p>
      </div>
    </div>
  );
}
