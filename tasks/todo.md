# Continuous Mode + Local Speaker Diarization

**User goal:** Use this as a regular daily app — run for hours continuously, see live transcription, have the app auto-detect different speakers, and let me type a name for each detected speaker to label all their segments.

**Confirmed choices:** React/Electron UI · Local diarization (pyannote/diart) · BlackHole system-audio source.

## Architecture decisions

1. **Rolling-chunk pipeline, not single growing file.**
   Today [backend.py:535-600](backend.py:535) re-transcribes the entire `.part` file every 3s — O(n²) and unusable past ~30 min. Switch to fixed-size chunks (~20s with 2s overlap) that get ASR + diarization independently, then streamed to the UI.

2. **`faster-whisper` instead of `openai-whisper`.**
   ~4× faster on CPU/MPS, drop-in API. Critical for keeping live latency under chunk size on a multi-hour run.

3. **`pyannote-audio` for diarization + a speaker-embedding registry.**
   Pure pyannote (not `diart`) so we own the cross-chunk speaker matching: per session, keep `{speaker_id: centroid_embedding}`; for each new chunk, embed each diarized cluster and either match to an existing speaker (cosine > threshold) or mint a new one. This is what makes "Speaker_0" remain the same person an hour later.

4. **Speaker-label map is session-scoped, not per-chunk.**
   `Speaker_0 → "Alice"` is stored once on the session and applied to every segment in the UI. Renaming is a single HTTP call that retroactively rewrites display, never the underlying IDs.

5. **No new big UI surface — extend `RecordingInterface.tsx`.**
   It already owns the WebSocket; add a "Continuous mode" toggle, a live transcript pane that renders speaker-tagged segments, and a sidebar of detected speakers with inline name inputs.

## Phase 1 — Backend foundation ✅ COMPLETE
- [x] Add deps to `requirements.txt`: `faster-whisper`, `pyannote.audio>=3.1`, `scipy`.
- [x] New module `continuous_session.py` with `ContinuousSession`: lazy-loaded models, per-session speaker registry with cosine matching, ASR↔diarization overlap-based alignment, JSON serialize/restore.
- [x] In `backend.py`: added `continuous_mode` flag (kept short-clip path identical when off), `continuous_loop` thread, direct PCM byte-slicing of the growing `.part` file (avoids ffmpeg overhead), tail-chunk processing on stop, autosave every N chunks.
- [x] Hard-cap audio queue at 500 blocks with drop-oldest semantics (won't block sounddevice callback thread).
- [x] Add `[CONTINUOUS]` section to `audio_config.ini.example` with HF token setup steps + tunables.

**Verification done (worktree has no installed deps, so limited):** `py_compile` both files, AST check all 10 new methods present, manual diff review confirms continuous-mode is fully gated. Full test-suite run blocked here by missing `requests`/`fastapi`/`sounddevice` in this worktree (unrelated to my changes).

## Phase 2 — WebSocket & HTTP events ✅ COMPLETE
- [x] New WS events in `api_server.py`: `segment`, `speaker_added`, `speaker_renamed` (event types kept distinct so the React layer can branch cleanly).
- [x] REST: `RecordingStartRequest` gained `continuous: bool`; `GET /api/sessions/current` snapshot; `PATCH /api/sessions/{id}/speakers/{speaker_id}`; `/api/health` reports `continuous_ready` + reason so the UI can self-disable the toggle when prereqs missing.
- [x] Sync→async callbacks wired into lifespan (`segment_callback`, `continuous_speaker_callback`).

## Phase 3 — React UI ✅ COMPLETE
- [x] New `ContinuousModePanel.tsx`: live transcript pane (auto-scroll w/ "follow" detection — pauses scrolling if user reads back), speaker sidebar with inline rename inputs, deterministic per-speaker colors.
- [x] `RecordingInterface.tsx`: new state, toggle on idle view (gated by `/api/health` continuous_ready), WS handlers for `segment`/`speaker_added`/`speaker_renamed`, optimistic rename via PATCH, panel renders in place of scratchpad+insights when continuous mode is on (controls bar unchanged).

## Phase 4 — Persistence (partial — autosave done; history integration deferred)
- [x] Backend `_save_continuous_session()` writes `session_{id}.json` to `history_directory` after every N chunks and on stop. Atomic write via `.tmp` + `os.replace`.
- [ ] **Deferred:** surface continuous-session entries in `MeetingHistory.tsx` (would need `GET /api/sessions` listing endpoint + UI rendering). User said "everything else is optional"; the on-disk JSON is sufficient for now.

## Phase 5 — Verification (user-driven, requires real env)
- [x] `py_compile` passes for backend.py, continuous_session.py, api_server.py.
- [x] AST check: all 10 new backend methods present; all 3 new endpoints registered; all 3 new WS event types defined.
- [x] TypeScript syntax check: no real errors in modified TSX (only "module not found" noise from missing node_modules).
- [ ] **Needs your env:** `pip install -r requirements.txt`, accept HF licenses, set `[CONTINUOUS] hf_token`, run for ~5 min to validate end-to-end (segments arrive, speakers labelable). 2-hour soak is the real test.
- [ ] **Needs your env:** rerun `pytest tests/` to confirm no regression (worktree can't run them — missing deps).

## Files changed (Phases 1–3)
| File | Change |
|---|---|
| `requirements.txt` | +3 deps: `faster-whisper`, `pyannote.audio>=3.1`, `scipy` |
| `audio_config.ini.example` | New `[CONTINUOUS]` section with HF token setup walkthrough |
| `continuous_session.py` | **NEW** — `ContinuousSession` class (lazy models, speaker registry, cosine matching, overlap-based ASR↔diar alignment, JSON serialize) |
| `backend.py` | continuous_mode flag + 10 methods; bounded audio queue (drop-oldest); preserved short-clip path verbatim when flag off |
| `api_server.py` | 2 new broadcasts, 2 callbacks, 1 modified + 2 new endpoints, /api/health extended |
| `Personalassistantappmainpage-main/src/app/components/ContinuousModePanel.tsx` | **NEW** — live transcript + speaker sidebar |
| `Personalassistantappmainpage-main/src/app/components/RecordingInterface.tsx` | Continuous-mode state, toggle, WS handlers, panel integration |

## Open questions to flag before implementing
- HuggingFace token: pyannote models are gated. User will need to accept the model license once and put a token in `audio_config.ini` (`[CONTINUOUS] hf_token=...`). I'll add a clear setup note + a `/api/health` field that reports if diarization is ready.
- Should pause/resume preserve the speaker registry? Recommend yes — same session, same map.
- Final summary at session end (Gemini call on the whole transcript) — keep or drop? User said "everything else is optional"; I'll keep it but only run when session ends, not continuously.

---

# Live Meeting Coach - Implementation Tasks (previous work, reference)

## Completed
- [x] Phase 1a-b: Coach state + public methods in backend.py
- [x] Phase 1c: `_call_llm_json()` shared LLM helper (refactored from live_summary_loop)
- [x] Phase 1d-f: `live_coach_loop()`, `_build_coach_prompt()`, `_check_time_warnings()`
- [x] Phase 1g: `[COACH]` config section defaults
- [x] Phase 2: Pre-recording context UI (agenda, notes, duration fields + coach toggle)
- [x] Phase 3: CoachAlertsPanel side panel + split layout during recording
- [x] Phase 4: RSS feed fetcher (`feed_fetcher.py`) + settings UI + `feedparser` dep
- [x] Phase 5: Polish — state cleanup in reset(), config example, fragile ref fix

## Review Notes
- Verified all 8 modified/new files pass `py_compile`
- Fixed: reset() now clears agenda/notes/duration fields and coach toggle
- Fixed: backend clears `_coach_enabled` after threads join in `_async_stop_and_process`
- Fixed: replaced fragile `winfo_children()[0]` with stored `self.content` reference

## Files Changed
| File | Action |
|------|--------|
| `backend.py` | Modified — coach state, `_call_llm_json`, `live_coach_loop`, config |
| `gui_modern.py` | Modified — coach callback wiring |
| `ui/views/record_view.py` | Modified — coach toggle, context fields, split layout |
| `ui/components/coach_panel.py` | **New** — `CoachAlertsPanel` widget |
| `ui/components/__init__.py` | Modified — export `CoachAlertsPanel` |
| `ui/styles.py` | Modified — coach severity colors |
| `ui/views/settings_view.py` | Modified — coach settings section |
| `feed_fetcher.py` | **New** — RSS feed caching |
| `requirements.txt` | Modified — added `feedparser>=6.0.0` |
| `audio_config.ini.example` | Modified — added `[COACH]` section |
