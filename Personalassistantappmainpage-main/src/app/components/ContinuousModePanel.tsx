import { useEffect, useRef, useState } from 'react';
import { Users, Mic2 } from 'lucide-react';
import { getApiUrl, getApiHeaders } from '../config/api';

export interface Segment {
  speaker_id: string;
  start: number;
  end: number;
  text: string;
}

interface Props {
  sessionId: string | null;
  segments: Segment[];
  speakers: Record<string, string | null>;  // speaker_id -> human name (null = unlabeled)
  onSpeakerRenamed: (speakerId: string, name: string) => void;
}

// Deterministic color per speaker so the same person stays the same color
const SPEAKER_COLORS = [
  '#2774AE', '#FFD100', '#22c55e', '#f97316',
  '#a855f7', '#ec4899', '#06b6d4', '#84cc16',
];

function speakerColor(speakerId: string): string {
  // Hash the id to a stable color index
  let hash = 0;
  for (let i = 0; i < speakerId.length; i++) {
    hash = (hash * 31 + speakerId.charCodeAt(i)) >>> 0;
  }
  return SPEAKER_COLORS[hash % SPEAKER_COLORS.length];
}

function displayName(speakerId: string, name: string | null | undefined): string {
  if (name && name.trim()) return name;
  // "Speaker_3" → "Speaker 3" for nicer display
  return speakerId.replace('_', ' ');
}

export function ContinuousModePanel({ sessionId, segments, speakers, onSpeakerRenamed }: Props) {
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const userScrolledRef = useRef(false);
  const [drafts, setDrafts] = useState<Record<string, string>>({});  // in-progress rename input
  const [savingId, setSavingId] = useState<string | null>(null);

  // Auto-scroll to bottom on new segment unless the user has scrolled up.
  useEffect(() => {
    const el = transcriptRef.current;
    if (!el) return;
    if (!userScrolledRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [segments.length]);

  const handleScroll = () => {
    const el = transcriptRef.current;
    if (!el) return;
    // If user is within 40px of bottom, treat as "following along".
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    userScrolledRef.current = !atBottom;
  };

  const saveSpeakerName = async (speakerId: string) => {
    if (!sessionId) return;
    const name = (drafts[speakerId] ?? '').trim();
    if (!name) return;
    setSavingId(speakerId);
    try {
      const resp = await fetch(
        getApiUrl(`/api/sessions/${sessionId}/speakers/${speakerId}`),
        {
          method: 'PATCH',
          headers: { ...getApiHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({ name }),
        }
      );
      if (resp.ok) {
        onSpeakerRenamed(speakerId, name);
        setDrafts(prev => {
          const next = { ...prev };
          delete next[speakerId];
          return next;
        });
      } else {
        console.error('Rename failed', await resp.text());
      }
    } catch (e) {
      console.error('Rename request failed', e);
    } finally {
      setSavingId(null);
    }
  };

  const speakerIds = Object.keys(speakers);

  return (
    <div className="flex-1 flex gap-4 min-h-0">
      {/* Live transcript pane (~70% width) */}
      <div className="flex-1 flex flex-col bg-white/5 border border-white/10 rounded-xl min-h-0">
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/10">
          <Mic2 className="w-4 h-4 text-[#FFD100]" />
          <span className="text-sm font-semibold text-white">Live transcript</span>
          <span className="ml-auto text-xs text-gray-500">
            {segments.length} segment{segments.length === 1 ? '' : 's'}
          </span>
        </div>
        <div
          ref={transcriptRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto px-4 py-3 space-y-2"
        >
          {segments.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-500 text-sm italic">
              Listening… first chunk will appear in ~20s.
            </div>
          ) : (
            segments.map((seg, idx) => {
              const color = speakerColor(seg.speaker_id);
              const label = displayName(seg.speaker_id, speakers[seg.speaker_id]);
              return (
                <div key={idx} className="flex gap-2 text-sm">
                  <span
                    className="shrink-0 px-2 py-0.5 rounded-full text-xs font-medium"
                    style={{ backgroundColor: `${color}22`, color }}
                  >
                    {label}
                  </span>
                  <span className="text-gray-200 leading-relaxed">{seg.text}</span>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Speaker sidebar (~30% width) */}
      <div className="w-72 flex flex-col bg-white/5 border border-white/10 rounded-xl">
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/10">
          <Users className="w-4 h-4 text-[#2774AE]" />
          <span className="text-sm font-semibold text-white">Speakers</span>
          <span className="ml-auto text-xs text-gray-500">{speakerIds.length}</span>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {speakerIds.length === 0 ? (
            <p className="text-xs text-gray-500 italic p-2">
              Speakers will appear here as they're detected.
            </p>
          ) : (
            speakerIds.map(sid => {
              const name = speakers[sid];
              const draft = drafts[sid] ?? '';
              const color = speakerColor(sid);
              return (
                <div key={sid} className="p-2 bg-white/[0.03] rounded-lg">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-xs text-gray-400">{sid.replace('_', ' ')}</span>
                    {name && (
                      <span className="ml-auto text-xs text-green-400">✓</span>
                    )}
                  </div>
                  <input
                    type="text"
                    value={draft !== '' ? draft : (name ?? '')}
                    onChange={e => setDrafts(prev => ({ ...prev, [sid]: e.target.value }))}
                    onKeyDown={e => {
                      if (e.key === 'Enter') saveSpeakerName(sid);
                    }}
                    onBlur={() => {
                      if ((drafts[sid] ?? '').trim() && drafts[sid] !== name) {
                        saveSpeakerName(sid);
                      }
                    }}
                    placeholder="Type a name…"
                    disabled={savingId === sid}
                    className="w-full bg-white/5 border border-white/10 rounded-md px-2 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#2774AE] disabled:opacity-50"
                  />
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
