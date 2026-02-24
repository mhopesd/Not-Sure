import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useIntegrations } from "../hooks/useIntegrations";
// NotSure logo placeholder (Figma asset removed for standalone builds)
const imgCanvas = "data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#1a1a2e"/><text x="32" y="40" text-anchor="middle" font-size="28" fill="#FFD100" font-family="sans-serif">?</text></svg>');
import {
  Mic,
  Monitor,
  KeyRound,
  Calendar,
  CalendarDays,
  MessageSquare,
  FileText,
  ChevronRight,
  ChevronLeft,
  Check,
  Shield,
  Sparkles,
  Zap,
  ArrowRight,
  Eye,
  EyeOff,
  ExternalLink,
  Plug,
  Rocket,
  Loader2,
} from "lucide-react";

const TOTAL_STEPS = 5;

/* ─── Shared icon column width for alignment ─── */
const ICON_COL = "w-8 h-8 shrink-0 rounded-lg flex items-center justify-center";

/* ─── Permission item ─── */
interface PermItemProps {
  icon: React.ReactNode;
  title: string;
  desc: string;
  granted: boolean;
  onGrant: () => void;
}

function PermItem({ icon, title, desc, granted, onGrant }: PermItemProps) {
  return (
    <div
      className="flex items-center gap-3 p-3 rounded-lg transition-colors"
      style={{ background: "rgba(255,255,255,0.025)" }}
    >
      <div
        className={ICON_COL}
        style={{
          background: granted
            ? "rgba(109,213,140,0.12)"
            : "rgba(39,116,174,0.12)",
        }}
      >
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[12px] text-white/85">{title}</div>
        <div className="text-[10px] text-white/35">{desc}</div>
      </div>
      <button
        onClick={onGrant}
        className="px-3 py-1.5 rounded-md text-[11px] transition-all"
        style={{
          background: granted ? "rgba(109,213,140,0.12)" : "rgba(39,116,174,0.15)",
          color: granted ? "#6dd58c" : "#2774AE",
          border: `1px solid ${granted ? "rgba(109,213,140,0.2)" : "rgba(39,116,174,0.2)"}`,
        }}
      >
        {granted ? (
          <span className="flex items-center gap-1">
            <Check size={10} /> Granted
          </span>
        ) : (
          "Allow"
        )}
      </button>
    </div>
  );
}

/* ─── Integration card ─── */
interface IntegrationProps {
  icon: React.ReactNode;
  name: string;
  desc: string;
  color: string;
  connected: boolean;
  onToggle: () => void;
  comingSoon?: boolean;
  isConnecting?: boolean;
}

function IntegrationCard({ icon, name, desc, color, connected, onToggle, comingSoon, isConnecting }: IntegrationProps) {
  return (
    <div
      className="flex items-center gap-3 p-3 rounded-lg transition-colors"
      style={{ background: "rgba(255,255,255,0.025)", opacity: comingSoon ? 0.5 : 1 }}
    >
      <div
        className={ICON_COL}
        style={{ background: comingSoon ? "rgba(255,255,255,0.03)" : `${color}18` }}
      >
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[12px] text-white/85">{name}</div>
        <div className="text-[10px] text-white/35">{desc}</div>
      </div>
      {comingSoon ? (
        <span
          className="text-[9px] text-white/20 px-2 py-1 rounded-md"
          style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}
        >
          Coming Soon
        </span>
      ) : (
        <button
          onClick={onToggle}
          disabled={isConnecting}
          className="px-3 py-1.5 rounded-md text-[11px] transition-all flex items-center gap-1 disabled:opacity-40"
          style={{
            background: connected ? `${color}18` : "rgba(255,255,255,0.04)",
            color: connected ? color : "rgba(255,255,255,0.4)",
            border: `1px solid ${connected ? `${color}30` : "rgba(255,255,255,0.06)"}`,
          }}
        >
          {isConnecting ? (
            <><Loader2 size={10} className="animate-spin" /> Connecting...</>
          ) : connected ? (
            <><Check size={10} /> Connected</>
          ) : (
            <><Plug size={10} /> Connect</>
          )}
        </button>
      )}
    </div>
  );
}

/* ─── Main Wizard ─── */
interface OnboardingWizardProps {
  onComplete: () => void;
}

export function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [step, setStep] = useState(0);

  // Permissions state
  const [micGranted, setMicGranted] = useState(false);
  const [sysAudioGranted, setSysAudioGranted] = useState(false);
  const [screenGranted, setScreenGranted] = useState(false);

  // AI config state
  const [aiProvider, setAiProvider] = useState<"openai" | "anthropic" | "local">("openai");
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);

  // Integrations (wired to backend OAuth)
  const oauthIntegrations = useIntegrations();
  const googleConnected = oauthIntegrations.status?.google?.connected ?? false;
  const microsoftConnected = oauthIntegrations.status?.microsoft?.connected ?? false;
  const connectedCount = [googleConnected, microsoftConnected].filter(Boolean).length;

  const canProceed = useCallback(() => {
    if (step === 0) return true;
    if (step === 1) return micGranted && sysAudioGranted;
    if (step === 2) return aiProvider === "local" || apiKey.length > 8;
    if (step === 3) return true;
    return true;
  }, [step, micGranted, sysAudioGranted, aiProvider, apiKey]);

  const next = () => {
    if (step < TOTAL_STEPS - 1) setStep(step + 1);
    else onComplete();
  };

  const prev = () => {
    if (step > 0) setStep(step - 1);
  };

  return (
    <div className="flex h-full">
      {/* ─── Left Rail: Progress & Context ─── */}
      <div
        className="w-[220px] shrink-0 flex flex-col p-4 pb-3"
        style={{
          background: "rgba(255,255,255,0.015)",
          borderRight: "1px solid rgba(255,255,255,0.04)",
        }}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 mb-6">
          <div className="w-7 h-7 rounded-lg overflow-hidden flex items-center justify-center">
            <img
              alt="NotSure"
              src={imgCanvas}
              className="w-full h-full object-contain"
            />
          </div>
          <div>
            <div className="text-[12px] text-white/80">NotSure</div>
            <div className="text-[9px] text-white/25">Setup Wizard</div>
          </div>
        </div>

        {/* Step List */}
        <nav className="flex-1 space-y-0.5">
          {[
            { icon: <Sparkles size={13} />, label: "Welcome" },
            { icon: <Shield size={13} />, label: "Permissions" },
            { icon: <KeyRound size={13} />, label: "AI Setup" },
            { icon: <Plug size={13} />, label: "Integrations" },
            { icon: <Rocket size={13} />, label: "Ready" },
          ].map((s, i) => {
            const isActive = i === step;
            const isDone = i < step;
            return (
              <button
                key={s.label}
                onClick={() => i <= step && setStep(i)}
                className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg transition-all text-left"
                style={{
                  background: isActive ? "rgba(39,116,174,0.1)" : "transparent",
                  cursor: i <= step ? "pointer" : "default",
                  opacity: i > step ? 0.3 : 1,
                }}
              >
                <div
                  className="w-6 h-6 rounded-md flex items-center justify-center shrink-0"
                  style={{
                    background: isDone
                      ? "rgba(109,213,140,0.15)"
                      : isActive
                      ? "rgba(39,116,174,0.2)"
                      : "rgba(255,255,255,0.04)",
                    color: isDone
                      ? "#6dd58c"
                      : isActive
                      ? "#2774AE"
                      : "rgba(255,255,255,0.25)",
                  }}
                >
                  {isDone ? <Check size={11} /> : s.icon}
                </div>
                <span
                  className="text-[11px]"
                  style={{
                    color: isDone
                      ? "rgba(255,255,255,0.5)"
                      : isActive
                      ? "#2774AE"
                      : "rgba(255,255,255,0.3)",
                  }}
                >
                  {s.label}
                </span>
                {isActive && (
                  <div className="ml-auto w-1 h-1 rounded-full bg-[#2774AE]" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Bottom info */}
        <div className="pt-3" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
          <div className="flex items-center gap-2 mb-2">
            <div className="flex-1 h-1 rounded-full bg-white/[0.06] overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-[#2774AE]"
                animate={{ width: `${((step + 1) / TOTAL_STEPS) * 100}%` }}
                transition={{ duration: 0.4, ease: "easeOut" }}
              />
            </div>
            <span className="text-[9px] text-white/25 font-mono shrink-0">
              {step + 1}/{TOTAL_STEPS}
            </span>
          </div>
          <div className="text-[9px] text-white/20 flex items-center gap-1">
            <Shield size={8} />
            All data stays on your device
          </div>
        </div>
      </div>

      {/* ─── Main Content ─── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Step Content */}
        <div className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -12 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="h-full"
            >
              {step === 0 && <StepWelcome />}
              {step === 1 && (
                <StepPermissions
                  micGranted={micGranted}
                  sysAudioGranted={sysAudioGranted}
                  screenGranted={screenGranted}
                  onMic={() => setMicGranted(true)}
                  onSysAudio={() => setSysAudioGranted(true)}
                  onScreen={() => setScreenGranted(true)}
                />
              )}
              {step === 2 && (
                <StepAI
                  provider={aiProvider}
                  setProvider={setAiProvider}
                  apiKey={apiKey}
                  setApiKey={setApiKey}
                  showKey={showKey}
                  setShowKey={setShowKey}
                />
              )}
              {step === 3 && (
                <StepIntegrations
                  integrations={oauthIntegrations}
                  connectedCount={connectedCount}
                />
              )}
              {step === 4 && (
                <StepReady
                  micGranted={micGranted}
                  sysAudioGranted={sysAudioGranted}
                  provider={aiProvider}
                  connectedCount={connectedCount}
                />
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* ─── Bottom Navigation ─── */}
        <div
          className="h-[54px] flex items-center justify-between px-6 shrink-0"
          style={{
            borderTop: "1px solid rgba(255,255,255,0.04)",
            background: "rgba(255,255,255,0.01)",
          }}
        >
          <div>
            {step > 0 ? (
              <button
                onClick={prev}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] text-white/40 hover:text-white/60 hover:bg-white/[0.04] transition-all"
              >
                <ChevronLeft size={12} />
                Back
              </button>
            ) : (
              <span className="text-[10px] text-white/15">Takes about 2 minutes</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {step < TOTAL_STEPS - 1 && step > 0 && (
              <button
                onClick={next}
                className="px-3 py-1.5 rounded-lg text-[11px] text-white/30 hover:text-white/50 transition-colors"
              >
                Skip
              </button>
            )}
            <button
              onClick={next}
              disabled={!canProceed()}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-[12px] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              style={{
                background: canProceed()
                  ? step === TOTAL_STEPS - 1
                    ? "linear-gradient(135deg, #2774AE, #1a5a8e)"
                    : "rgba(39,116,174,0.15)"
                  : "rgba(255,255,255,0.04)",
                color: canProceed() ? (step === TOTAL_STEPS - 1 ? "white" : "#2774AE") : "rgba(255,255,255,0.2)",
                border: `1px solid ${
                  canProceed()
                    ? step === TOTAL_STEPS - 1
                      ? "rgba(39,116,174,0.3)"
                      : "rgba(39,116,174,0.15)"
                    : "rgba(255,255,255,0.04)"
                }`,
              }}
            >
              {step === TOTAL_STEPS - 1 ? (
                <>
                  Launch Dashboard
                  <ArrowRight size={13} />
                </>
              ) : (
                <>
                  Continue
                  <ChevronRight size={13} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════
   STEP 0 — Welcome
   ══════════════════════════════════════════ */
function StepWelcome() {
  return (
    <div className="flex flex-col items-center justify-center h-full px-8">
      <div className="max-w-md text-center">
        {/* Animated logo — Liquid Glass Shader Sphere */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{
            scale: 1,
            opacity: 1,
            y: [0, -6, 0, 4, 0],
            x: [0, 3, 0, -3, 0],
            rotate: [0, 2, 0, -2, 0],
          }}
          transition={{
            scale: { duration: 0.6, ease: "easeOut" },
            opacity: { duration: 0.6, ease: "easeOut" },
            y: { duration: 6, ease: "easeInOut", repeat: Infinity, repeatType: "loop" },
            x: { duration: 8, ease: "easeInOut", repeat: Infinity, repeatType: "loop" },
            rotate: { duration: 7, ease: "easeInOut", repeat: Infinity, repeatType: "loop" },
          }}
          className="relative w-24 h-24 mx-auto mb-5"
        >
          <motion.div
            className="absolute inset-0 rounded-full overflow-hidden"
            animate={{ scale: [1, 1.03, 1, 0.97, 1] }}
            transition={{ duration: 5, ease: "easeInOut", repeat: Infinity, repeatType: "loop" }}
          >
            <img
              alt="NotSure"
              src={imgCanvas}
              className="w-full h-full object-contain pointer-events-none"
            />
          </motion.div>
          {/* Animated glow behind the sphere */}
          <motion.div
            className="absolute inset-[-16px] rounded-full pointer-events-none"
            animate={{
              opacity: [0.5, 0.8, 0.5],
              scale: [1, 1.1, 1],
            }}
            transition={{ duration: 4, ease: "easeInOut", repeat: Infinity, repeatType: "loop" }}
            style={{
              background: "radial-gradient(circle, rgba(39,116,174,0.2) 0%, rgba(255,209,0,0.05) 40%, transparent 70%)",
              filter: "blur(14px)",
              zIndex: -1,
            }}
          />
        </motion.div>

        <motion.div
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.15, duration: 0.4 }}
        >
          <h1 className="text-white/95 mb-1.5">Welcome to NotSure</h1>
          <p className="text-[13px] text-white/40 mb-6">
            Your AI-powered meeting companion. Record, transcribe, and extract insights from every conversation — all processed locally on your device.
          </p>
        </motion.div>

        {/* Feature pills */}
        <motion.div
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
          className="space-y-2 mb-6"
        >
          {[
            {
              icon: <Mic size={13} />,
              label: "One-click recording",
              detail: "Mic + system audio capture",
              color: "#2774AE",
            },
            {
              icon: <Sparkles size={13} />,
              label: "AI transcription",
              detail: "Real-time speech to text",
              color: "#FFD100",
            },
            {
              icon: <Zap size={13} />,
              label: "Smart summaries",
              detail: "Action items & key decisions",
              color: "#6dd58c",
            },
          ].map((f) => (
            <div
              key={f.label}
              className="flex items-center gap-3 p-2.5 rounded-lg text-left"
              style={{ background: "rgba(255,255,255,0.025)" }}
            >
              <div
                className={ICON_COL}
                style={{ background: `${f.color}15`, color: f.color }}
              >
                {f.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[12px] text-white/80">{f.label}</div>
                <div className="text-[10px] text-white/30">{f.detail}</div>
              </div>
              <Check size={11} style={{ color: f.color, opacity: 0.5 }} />
            </div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex items-center justify-center gap-1.5 text-[9px] text-white/20"
        >
          <Shield size={8} />
          Privacy-first — your recordings never leave your machine
        </motion.div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════
   STEP 1 — Permissions
   ══════════════════════════════════════════ */
function StepPermissions({
  micGranted,
  sysAudioGranted,
  screenGranted,
  onMic,
  onSysAudio,
  onScreen,
}: {
  micGranted: boolean;
  sysAudioGranted: boolean;
  screenGranted: boolean;
  onMic: () => void;
  onSysAudio: () => void;
  onScreen: () => void;
}) {
  const allGranted = micGranted && sysAudioGranted;
  return (
    <div className="flex flex-col justify-center h-full px-8">
      <div className="max-w-md mx-auto w-full">
        <div className="flex items-center gap-2.5 mb-1">
          <div
            className={ICON_COL}
            style={{ background: "rgba(39,116,174,0.12)", color: "#2774AE" }}
          >
            <Shield size={14} />
          </div>
          <div>
            <h2 className="text-white/90">System Permissions</h2>
            <p className="text-[11px] text-white/35">
              NotSure needs access to capture audio during meetings
            </p>
          </div>
        </div>

        {/* Status indicator */}
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg mb-4 mt-3"
          style={{
            background: allGranted
              ? "rgba(109,213,140,0.06)"
              : "rgba(255,209,0,0.06)",
            border: `1px solid ${allGranted ? "rgba(109,213,140,0.1)" : "rgba(255,209,0,0.1)"}`,
          }}
        >
          <div
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: allGranted ? "#6dd58c" : "#FFD100" }}
          />
          <span
            className="text-[10px]"
            style={{ color: allGranted ? "#6dd58c" : "#FFD100" }}
          >
            {allGranted
              ? "All required permissions granted"
              : `${[micGranted, sysAudioGranted].filter(Boolean).length} of 2 required permissions granted`}
          </span>
        </div>

        <div className="space-y-2">
          <PermItem
            icon={<Mic size={14} className={micGranted ? "text-[#6dd58c]" : "text-[#2774AE]"} />}
            title="Microphone Access"
            desc="Capture your voice during meetings"
            granted={micGranted}
            onGrant={onMic}
          />
          <PermItem
            icon={<Monitor size={14} className={sysAudioGranted ? "text-[#6dd58c]" : "text-[#2774AE]"} />}
            title="System Audio Capture"
            desc="Record audio from other participants"
            granted={sysAudioGranted}
            onGrant={onSysAudio}
          />
          <PermItem
            icon={<Monitor size={14} className={screenGranted ? "text-[#6dd58c]" : "text-white/30"} />}
            title="Screen Recording"
            desc="Optional — capture shared screens"
            granted={screenGranted}
            onGrant={onScreen}
          />
        </div>

        <div className="mt-4 flex items-start gap-2 text-[10px] text-white/20">
          <Shield size={9} className="mt-[2px] shrink-0" />
          <span>
            These permissions are required by macOS. Audio is processed locally and never uploaded without your consent.
          </span>
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════
   STEP 2 — AI Setup
   ══════════════════════════════════════════ */
function StepAI({
  provider,
  setProvider,
  apiKey,
  setApiKey,
  showKey,
  setShowKey,
}: {
  provider: "openai" | "anthropic" | "local";
  setProvider: (p: "openai" | "anthropic" | "local") => void;
  apiKey: string;
  setApiKey: (k: string) => void;
  showKey: boolean;
  setShowKey: (s: boolean) => void;
}) {
  const providers = [
    {
      id: "openai" as const,
      name: "OpenAI",
      desc: "GPT-4o / Whisper",
      color: "#10a37f",
      badge: "Recommended",
    },
    {
      id: "anthropic" as const,
      name: "Anthropic",
      desc: "Claude 3.5 Sonnet",
      color: "#d97706",
      badge: null,
    },
    {
      id: "local" as const,
      name: "Local Models",
      desc: "Whisper.cpp + Ollama",
      color: "#8b5cf6",
      badge: "No API key needed",
    },
  ];

  return (
    <div className="flex flex-col justify-center h-full px-8">
      <div className="max-w-md mx-auto w-full">
        <div className="flex items-center gap-2.5 mb-4">
          <div
            className={ICON_COL}
            style={{ background: "rgba(255,209,0,0.1)", color: "#FFD100" }}
          >
            <Sparkles size={14} />
          </div>
          <div>
            <h2 className="text-white/90">AI Configuration</h2>
            <p className="text-[11px] text-white/35">
              Choose how NotSure processes your recordings
            </p>
          </div>
        </div>

        {/* Provider selection */}
        <div className="space-y-1.5 mb-4">
          {providers.map((p) => {
            const isActive = provider === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setProvider(p.id)}
                className="w-full flex items-center gap-3 p-3 rounded-lg transition-all text-left"
                style={{
                  background: isActive ? `${p.color}10` : "rgba(255,255,255,0.02)",
                  border: `1px solid ${isActive ? `${p.color}25` : "rgba(255,255,255,0.04)"}`,
                }}
              >
                <div
                  className="w-6 h-6 rounded-md flex items-center justify-center shrink-0"
                  style={{
                    background: `${p.color}18`,
                    color: p.color,
                  }}
                >
                  <Zap size={12} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] text-white/80">{p.name}</span>
                    {p.badge && (
                      <span
                        className="text-[8px] px-1.5 py-[1px] rounded-full"
                        style={{
                          background: `${p.color}15`,
                          color: p.color,
                        }}
                      >
                        {p.badge}
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-white/30">{p.desc}</div>
                </div>
                <div
                  className="w-4 h-4 rounded-full border-2 flex items-center justify-center transition-colors"
                  style={{
                    borderColor: isActive ? p.color : "rgba(255,255,255,0.1)",
                  }}
                >
                  {isActive && (
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ background: p.color }}
                    />
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* API Key input */}
        <AnimatePresence>
          {provider !== "local" && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="space-y-2 pb-2">
                <label className="text-[11px] text-white/40 flex items-center gap-1.5">
                  <KeyRound size={10} />
                  API Key
                </label>
                <div className="relative">
                  <input
                    type={showKey ? "text" : "password"}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={
                      provider === "openai"
                        ? "sk-proj-..."
                        : "sk-ant-..."
                    }
                    className="w-full px-3 py-2.5 rounded-lg text-[12px] text-white/80 placeholder:text-white/15 outline-none font-mono pr-10"
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.06)",
                    }}
                  />
                  <button
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-white/25 hover:text-white/50 transition-colors"
                  >
                    {showKey ? <EyeOff size={13} /> : <Eye size={13} />}
                  </button>
                </div>
                <div className="flex items-center gap-1.5 text-[9px] text-white/20">
                  <Shield size={8} />
                  <span>Stored locally in your macOS Keychain — never transmitted</span>
                  <a
                    href="#"
                    className="ml-auto flex items-center gap-0.5 text-[#2774AE] hover:text-[#3a8fd4] transition-colors"
                  >
                    Get key <ExternalLink size={7} />
                  </a>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {provider === "local" && (
          <div
            className="flex items-center gap-2 p-2.5 rounded-lg text-[10px]"
            style={{
              background: "rgba(139,92,246,0.06)",
              border: "1px solid rgba(139,92,246,0.1)",
              color: "rgba(139,92,246,0.7)",
            }}
          >
            <Zap size={10} />
            <span>Local models will be downloaded on first use (~1.5 GB)</span>
          </div>
        )}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════
   STEP 3 — Integrations
   ══════════════════════════════════════════ */
function StepIntegrations({
  integrations,
  connectedCount,
}: {
  integrations: ReturnType<typeof useIntegrations>;
  connectedCount: number;
}) {
  const { status, connecting, error } = integrations;
  const googleConnected = status?.google?.connected ?? false;
  const microsoftConnected = status?.microsoft?.connected ?? false;

  return (
    <div className="flex flex-col justify-center h-full px-8">
      <div className="max-w-md mx-auto w-full">
        <div className="flex items-center gap-2.5 mb-1">
          <div
            className={ICON_COL}
            style={{ background: "rgba(109,213,140,0.1)", color: "#6dd58c" }}
          >
            <Plug size={14} />
          </div>
          <div>
            <h2 className="text-white/90">Integrations</h2>
            <p className="text-[11px] text-white/35">
              Connect your tools to auto-sync meeting notes
            </p>
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg mt-3" style={{ background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.12)" }}>
            <span className="text-[10px] text-red-400">{error}</span>
          </div>
        )}

        {/* Connected count */}
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg mb-4 mt-3"
          style={{
            background:
              connectedCount > 0
                ? "rgba(109,213,140,0.06)"
                : "rgba(255,255,255,0.02)",
            border: `1px solid ${
              connectedCount > 0
                ? "rgba(109,213,140,0.1)"
                : "rgba(255,255,255,0.04)"
            }`,
          }}
        >
          <div
            className="w-1.5 h-1.5 rounded-full"
            style={{
              background: connectedCount > 0 ? "#6dd58c" : "rgba(255,255,255,0.2)",
            }}
          />
          <span
            className="text-[10px]"
            style={{
              color: connectedCount > 0 ? "#6dd58c" : "rgba(255,255,255,0.3)",
            }}
          >
            {connectedCount > 0
              ? `${connectedCount} integration${connectedCount > 1 ? "s" : ""} connected`
              : "No integrations connected — you can add these later"}
          </span>
        </div>

        <div className="space-y-2">
          {/* Wired: Google & Microsoft */}
          <IntegrationCard
            icon={<Calendar size={14} style={{ color: "#3b82f6" }} />}
            name="Google Calendar"
            desc={googleConnected ? `Connected as ${status?.google?.email || "Google Account"}` : "Auto-detect meetings & attach recordings"}
            color="#3b82f6"
            connected={googleConnected}
            onToggle={googleConnected ? integrations.disconnectGoogle : integrations.connectGoogle}
            isConnecting={connecting === "google"}
          />
          <IntegrationCard
            icon={<CalendarDays size={14} style={{ color: "#0078d4" }} />}
            name="Outlook Calendar"
            desc={microsoftConnected ? `Connected as ${status?.microsoft?.email || "Microsoft Account"}` : "Sync meetings from Microsoft 365"}
            color="#0078d4"
            connected={microsoftConnected}
            onToggle={microsoftConnected ? integrations.disconnectMicrosoft : integrations.connectMicrosoft}
            isConnecting={connecting === "microsoft"}
          />

          {/* Coming Soon: Notion, Slack, Linear */}
          <IntegrationCard
            icon={<FileText size={14} style={{ color: "#ffffff" }} />}
            name="Notion"
            desc="Export summaries & action items as pages"
            color="#ffffff"
            connected={false}
            onToggle={() => {}}
            comingSoon
          />
          <IntegrationCard
            icon={<MessageSquare size={14} style={{ color: "#e01e5a" }} />}
            name="Slack"
            desc="Post meeting summaries to channels"
            color="#e01e5a"
            connected={false}
            onToggle={() => {}}
            comingSoon
          />
          <IntegrationCard
            icon={<Zap size={14} style={{ color: "#5e6ad2" }} />}
            name="Linear"
            desc="Create issues from action items"
            color="#5e6ad2"
            connected={false}
            onToggle={() => {}}
            comingSoon
          />
        </div>

        <div className="mt-4 flex items-center gap-1.5 text-[9px] text-white/20">
          <Plug size={8} />
          <span>You can manage integrations anytime from Settings</span>
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════
   STEP 4 — Ready
   ══════════════════════════════════════════ */
function StepReady({
  micGranted,
  sysAudioGranted,
  provider,
  connectedCount,
}: {
  micGranted: boolean;
  sysAudioGranted: boolean;
  provider: string;
  connectedCount: number;
}) {
  const items = [
    {
      label: "Microphone",
      ok: micGranted,
      detail: micGranted ? "Granted" : "Not granted",
      color: "#2774AE",
    },
    {
      label: "System Audio",
      ok: sysAudioGranted,
      detail: sysAudioGranted ? "Granted" : "Not granted",
      color: "#2774AE",
    },
    {
      label: "AI Provider",
      ok: true,
      detail:
        provider === "openai"
          ? "OpenAI"
          : provider === "anthropic"
          ? "Anthropic"
          : "Local Models",
      color: "#FFD100",
    },
    {
      label: "Integrations",
      ok: true,
      detail: connectedCount > 0 ? `${connectedCount} connected` : "None (skip for now)",
      color: "#6dd58c",
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full px-8">
      <div className="max-w-md text-center">
        <motion.div
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, type: "spring" }}
          className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#6dd58c] to-[#2d8f4e] flex items-center justify-center mx-auto mb-5"
          style={{ boxShadow: "0 8px 32px rgba(109,213,140,0.25)" }}
        >
          <Check size={28} className="text-white" />
        </motion.div>

        <motion.div
          initial={{ y: 8, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.15, duration: 0.4 }}
        >
          <h1 className="text-white/95 mb-1">You're All Set</h1>
          <p className="text-[13px] text-white/40 mb-5">
            NotSure is ready to record your first meeting.
          </p>
        </motion.div>

        {/* Config summary */}
        <motion.div
          initial={{ y: 8, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
          className="space-y-1.5 mb-5"
        >
          {items.map((item) => (
            <div
              key={item.label}
              className="flex items-center gap-3 p-2.5 rounded-lg text-left"
              style={{ background: "rgba(255,255,255,0.025)" }}
            >
              <div
                className="w-6 h-6 rounded-md flex items-center justify-center shrink-0"
                style={{
                  background: item.ok ? "rgba(109,213,140,0.15)" : "rgba(239,68,68,0.15)",
                }}
              >
                <Check
                  size={11}
                  style={{ color: item.ok ? "#6dd58c" : "#ef4444" }}
                />
              </div>
              <div className="flex-1">
                <span className="text-[11px] text-white/60">{item.label}</span>
              </div>
              <span className="text-[10px]" style={{ color: item.color }}>
                {item.detail}
              </span>
            </div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-[10px] text-white/20"
        >
          Tip: Use <span className="font-mono text-white/30 bg-white/[0.04] px-1 py-0.5 rounded">⌘R</span> to start recording from anywhere
        </motion.div>
      </div>
    </div>
  );
}