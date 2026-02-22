# Test Coverage Analysis

## Current State

### Existing Test Files

| File | Lines | Framework | CI-Ready | What It Tests |
|------|-------|-----------|----------|---------------|
| `test_backend.py` | 582 | unittest | Yes | LLM summarization, config loading, routing, helpers |
| `test_chaos_logic.py` | 62 | unittest | Yes | Chaos monkey injection, error monitor logging |
| `test_audio_recording.py` | 74 | None (script) | No | Real microphone recording (requires hardware) |
| `test_mic_permission.py` | 29 | None (script) | No | macOS-specific permission check |
| `.archive/test_macos.py` | 102 | None (script) | No | macOS dependency verification |

**Total test code: ~644 lines covering ~3,165 lines of production code (ratio: 0.20)**

### What IS Tested (test_backend.py)

- Config loading with defaults
- `auto_detect_llm()` priority logic (OpenAI > Gemini > Anthropic > Ollama)
- All four LLM summarizers: success and failure paths for Ollama, Gemini, OpenAI, Anthropic
- `generate_summary()` routing
- `_format_time()`, `set_mode()`, `error_summary()` helpers
- Markdown wrapper stripping (````json ... ```)

### What Is NOT Tested

Every module besides `backend.py` summarization logic has **zero unit tests**:

- **`api_server.py`** (1,034 lines) — 0 tests
- **`integrations/oauth_manager.py`** (154 lines) — 0 tests
- **`integrations/google_integration.py`** (226 lines) — 0 tests
- **`integrations/microsoft_integration.py`** (218 lines) — 0 tests
- **`app_logging.py`** (174 lines) — 0 tests

Within `backend.py` itself, the following are untested:

- Audio capture pipeline (`record_audio`, `start_recording`, `stop_recording`)
- Live transcription loop (FFmpeg subprocess integration)
- Live summary loop (real-time Gemini polling + context building)
- Device detection and fallback logic
- Thread synchronization and race conditions
- History/journal/session persistence (save, load, create, CRUD)
- Atomic file write/rename strategy
- Model preloading guard logic

### Infrastructure Issues

1. **Tests don't run** — Both `test_backend.py` and `test_chaos_logic.py` fail to import because `numpy` and `psutil` aren't installed. The test mocking strategy patches `sys.modules` for `whisper` and `sounddevice`, but `backend.py` imports `numpy` at module level before the mocks take effect.
2. **No test runner configuration** — No `pytest.ini`, `pyproject.toml [tool.pytest]`, `tox.ini`, or `conftest.py`.
3. **No CI pipeline** — No GitHub Actions, no Makefile test target.
4. **Utility scripts masquerade as tests** — `test_audio_recording.py` and `test_mic_permission.py` use `print()` instead of assertions and require real hardware.

---

## Proposed Improvements (Priority Order)

### P0 — Fix Existing Tests So They Actually Run

**Problem:** `test_backend.py` crashes on import because `numpy` isn't mocked before `backend.py` is imported.

**Fix:** Add `numpy` to the `sys.modules` mock block at the top of `test_backend.py`, or add a `conftest.py` that patches all heavy dependencies before any test module loads.

**Impact:** Unlocks the ~32 existing tests that currently provide zero value.

---

### P1 — API Server Endpoint Tests (`api_server.py`, 1,034 lines, 0 tests)

This is the largest untested module and serves as the primary interface between frontend and backend. Use FastAPI's built-in `TestClient` (from `starlette.testclient`).

**What to test:**
- `GET /api/health` — returns correct status when backend is/isn't initialized
- `GET /api/devices` — returns device list structure
- `POST /api/recordings/start` — rejects when already recording (409), rejects when backend uninitialized (503)
- `POST /api/recordings/stop` — rejects when not recording (409)
- `GET /api/meetings` — returns meetings list, handles empty history, handles malformed entries
- `GET /api/meetings/{id}` — returns meeting by ID, 404 for invalid, 400 for non-integer
- `PATCH /api/meetings/{id}/tags` — updates tags and persists
- `GET /api/meetings/search` — full-text search across fields, short query rejection
- `GET /api/tasks` — aggregates tasks from all meetings, handles both string and dict task formats
- `GET /api/people` — extracts and deduplicates speakers across meetings
- `GET/POST /api/journal` — CRUD operations
- `GET/PUT /api/settings` — reads and writes config
- `WebSocket /ws` — ping/pong, disconnect cleanup

**Why high priority:** These endpoints contain non-trivial data transformation logic (speaker info extraction, task aggregation, search snippet generation) that is easy to get wrong with different input shapes. The `speaker_info` handling alone appears in 5 different endpoints with the same dict-vs-list branching logic — a refactoring target that needs test coverage first.

---

### P2 — OAuth Manager Tests (`oauth_manager.py`, 154 lines, 0 tests)

This module handles sensitive credential and token storage. It's entirely mockable (file I/O only).

**What to test:**
- Token save/load/clear round-trip with temp files
- `is_connected()` — token present, token expired, token expired with refresh token
- `is_token_expired()` — not expired, expired, no expiry info, 5-minute buffer boundary
- `has_credentials()` — present, missing, partial (client_id only)
- `get_all_status()` — correct aggregation across providers
- File corruption handling (invalid JSON in tokens file)
- Concurrent access patterns (if applicable)

**Why high priority:** Incorrect token expiry logic causes silent auth failures in production. The 5-minute buffer logic at `oauth_manager.py:85` and `oauth_manager.py:98` has a subtle difference — `is_connected()` returns `True` if a refresh token exists even when expired, but `is_token_expired()` simply returns `True`. These need tests to verify the intended behavior.

---

### P3 — Backend Persistence Tests (history, journal, session)

These are pure file I/O operations that are straightforward to test with `tempfile.TemporaryDirectory`.

**What to test:**
- `save_to_history()` / `load_history()` — round-trip, empty file, corrupted JSON, missing file
- `save_journal()` / `load_journal()` / `create_journal_entry()` — CRUD, UUID generation
- `save_session()` / `load_session()` / `login()` / `logout()` / `is_logged_in()` — state transitions
- File permission errors (read-only directory)

---

### P4 — Integration Module Tests (Google + Microsoft, 444 lines combined, 0 tests)

Both modules follow identical patterns: OAuth flow, token refresh, calendar CRUD, email send. All external HTTP calls go through `requests`, making them easy to mock.

**What to test:**
- `get_auth_url()` — URL construction with correct scopes and params (pure function)
- `exchange_code()` — token parsing, expiry calculation, profile fetch
- `refresh_tokens()` — preserves refresh_token when not returned (Google-specific behavior)
- `get_calendar_events()` — response normalization, all-day event detection
- `create_calendar_event()` — request body construction
- `send_email()` — MIME encoding, base64 encoding (Google), JSON structure (Microsoft)
- HTTP error handling (4xx, 5xx, timeouts)

---

### P5 — Backend Audio Pipeline Tests (High Risk, Complex Mocking)

These are the hardest to test but cover the most critical functionality.

**What to test:**
- `detect_devices()` — mock `sounddevice.query_devices()` with various device lists, verify fallback when no devices found
- `start_recording()` — guard against recording while model loading, guard against double-start
- `record_audio()` — atomic `.part` file write strategy, rename-to-copy fallback
- `live_transcribe_loop()` — FFmpeg subprocess invocation, file cleanup, Whisper call
- `stop_recording()` + `_async_stop_and_process()` — thread join with timeout, state cleanup

**Why lower priority:** Requires careful thread mocking and subprocess patching. The risk/reward ratio is high but implementation cost is also high.

---

### P6 — JSON/String Parsing Edge Cases

The markdown stripping logic is duplicated across 4 summarizers with manual string slicing:

```python
# Repeated in _summarize_with_gemini, _summarize_with_ollama,
# _summarize_with_openai, _summarize_with_anthropic
if text.startswith("```json"): text = text[7:-3]
if text.startswith("```"): text = text[3:-3]
```

**What to test:**
- Empty string input
- Only backtick markers with no content
- Nested backticks
- Missing closing markers (slicing will corrupt output)
- Trailing newlines before closing markers

**Recommendation:** Extract this into a shared `_strip_markdown_wrapper()` function, then test the single function thoroughly. This eliminates the 4x duplication and makes the logic testable in isolation.

---

### P7 — Test Infrastructure Setup

**Recommended additions:**
1. **`conftest.py`** — Centralized mock setup for heavy imports (whisper, sounddevice, numpy, torch, pyaudio)
2. **`pytest.ini` or `pyproject.toml`** — Test discovery configuration, markers for slow/integration tests
3. **`Makefile` test target** — `make test` to run the suite
4. **GitHub Actions workflow** — CI pipeline that runs on PR

Example `conftest.py`:
```python
import sys
from unittest.mock import MagicMock

# Mock heavy dependencies before any test imports
for mod in ['whisper', 'sounddevice', 'numpy', 'torch', 'pyaudio',
            'psutil', 'customtkinter']:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()
```

---

## Coverage Estimate

| Module | Current Coverage | After P0-P4 |
|--------|-----------------|-------------|
| `backend.py` (summarization) | ~40% | ~40% |
| `backend.py` (audio/threading) | 0% | ~15% (P5) |
| `backend.py` (persistence) | 0% | ~80% (P3) |
| `api_server.py` | 0% | ~70% (P1) |
| `oauth_manager.py` | 0% | ~90% (P2) |
| `google_integration.py` | 0% | ~75% (P4) |
| `microsoft_integration.py` | 0% | ~75% (P4) |
| `app_logging.py` | 0% | 0% (low risk) |
| `chaos_engineering.py` | ~50% | ~50% |

**Implementing P0 through P4 would take overall coverage from ~10% to ~50%, focusing on the most testable and highest-risk code paths.**
