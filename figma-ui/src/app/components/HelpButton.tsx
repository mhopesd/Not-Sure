import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  HelpCircle,
  Bug,
  MessageSquare,
  BookOpen,
  ExternalLink,
  X,
  Github,
  Keyboard,
} from "lucide-react";

const MENU_ITEMS = [
  {
    icon: <Bug size={13} />,
    label: "Report an Issue",
    desc: "File a bug on GitHub",
    color: "#ef4444",
    href: "https://github.com/mhopesd/Not-Sure/issues/new",
  },
  {
    icon: <MessageSquare size={13} />,
    label: "Send Feedback",
    desc: "Share ideas or suggestions",
    color: "#2774AE",
    href: "#",
  },
  {
    icon: <BookOpen size={13} />,
    label: "Documentation",
    desc: "Guides and API reference",
    color: "#6dd58c",
    href: "#",
  },
  {
    icon: <Keyboard size={13} />,
    label: "Keyboard Shortcuts",
    desc: "View all shortcuts",
    color: "#FFD100",
    href: "#",
  },
  {
    icon: <Github size={13} />,
    label: "GitHub Repo",
    desc: "mhopesd/Not-Sure",
    color: "#ffffff",
    href: "https://github.com/mhopesd/Not-Sure",
  },
];

export function HelpButton() {
  const [open, setOpen] = useState(false);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute bottom-12 right-0 w-[240px] rounded-xl overflow-hidden"
            style={{
              background: "rgba(22, 22, 26, 0.97)",
              border: "1px solid rgba(255,255,255,0.07)",
              boxShadow:
                "0 16px 48px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.03)",
              backdropFilter: "blur(20px)",
            }}
          >
            {/* Header */}
            <div
              className="flex items-center justify-between px-3 py-2.5"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
            >
              <span className="text-[11px] text-white/50">Help & Support</span>
              <button
                onClick={() => setOpen(false)}
                className="p-0.5 rounded hover:bg-white/[0.06] transition-colors"
              >
                <X size={11} className="text-white/25" />
              </button>
            </div>

            {/* Items */}
            <div className="p-1.5">
              {MENU_ITEMS.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-white/[0.04] transition-colors group"
                >
                  <div
                    className="w-7 h-7 rounded-md flex items-center justify-center shrink-0"
                    style={{ background: `${item.color}10`, color: item.color }}
                  >
                    {item.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[11px] text-white/70 group-hover:text-white/85 transition-colors">
                      {item.label}
                    </div>
                    <div className="text-[9px] text-white/20">{item.desc}</div>
                  </div>
                  <ExternalLink
                    size={9}
                    className="text-white/0 group-hover:text-white/20 transition-colors shrink-0"
                  />
                </a>
              ))}
            </div>

            {/* Footer */}
            <div
              className="px-3 py-2"
              style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}
            >
              <span className="text-[9px] text-white/15">
                NotSure v0.1.0 · Built by mhopesd
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Trigger */}
      <motion.button
        onClick={() => setOpen(!open)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="w-8 h-8 rounded-full flex items-center justify-center transition-colors"
        style={{
          background: open
            ? "rgba(39, 116, 174, 0.25)"
            : "rgba(255, 255, 255, 0.06)",
          border: `1px solid ${
            open ? "rgba(39, 116, 174, 0.3)" : "rgba(255, 255, 255, 0.08)"
          }`,
          boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        }}
      >
        {open ? (
          <X size={14} className="text-[#2774AE]" />
        ) : (
          <HelpCircle size={14} className="text-white/40" />
        )}
      </motion.button>
    </div>
  );
}
