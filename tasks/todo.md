# Live Meeting Coach - Implementation Tasks

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
