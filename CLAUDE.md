# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

---

## Project Overview

This is a Python-based audio summarization application that records audio, transcribes it locally using OpenAI's Whisper model, and generates AI-powered summaries using either Ollama (local LLM) or Google Gemini API. The project emphasizes privacy-first design with all processing done locally when possible.

## Common Commands

### Setup and Installation
```bash
# Run automated setup (macOS only)
./setup.sh

# Manual setup
source venv/bin/activate
pip install -r requirements.txt
pip install dearpygui  # For desktop GUI
```

### Running the Application
```bash
# Activate virtual environment first
source venv/bin/activate

# Start Ollama (if using local LLM instead of Gemini)
ollama serve
ollama pull llama3:8b  # First time only

# Run desktop GUI (recommended)
python main_desktop.py

# Run CLI version
python main_cli.py

# Run legacy Tkinter version (requires tkinter)
python main.py
```

### Testing
```bash
# Test audio device detection and recording
python test_audio_recording.py

# Test microphone permissions
python test_mic_permission.py

# Test chaos engineering logic
python test_chaos_logic.py
```

## Architecture

### Core Components

**Backend Logic (`backend.py`)**
- `EnhancedAudioApp`: Main engine handling all audio processing, transcription, and summarization
- Uses callback pattern for UI updates: `status_callback`, `result_callback`, `transcript_callback`, `level_callback`
- Manages three recording modes: microphone, system audio (BlackHole), and hybrid (BBrew Hybrid)
- Implements atomic file writing strategy with `.part` files to avoid corruption during live transcription
- Preloads Whisper model in background thread to avoid blocking UI

**GUI Implementations**
- `main_desktop.py` → `gui_modern.py`: Modern CustomTkinter-based GUI with multiple views
- `main_cli.py`: Command-line interface for headless operation
- `main_app.py`: Legacy Tkinter version (not recommended on macOS with Homebrew Python)

**UI Architecture (`ui/` directory)**
- `styles.py`: Color constants and styling definitions
- `views/home_view.py`: Main landing page
- `views/live_view.py`: Real-time recording interface with live transcription
- `views/loading_view.py`: Splash screen during initialization
- `views/common_views.py`: Shared components (MeetingsView, TasksView, PeopleView, MeetingDetailView)

### Threading Model

The application uses threading extensively to keep UI responsive:
1. **Recording thread**: Captures audio stream via `sounddevice` callback
2. **Live transcription thread**: Periodically transcribes in-progress recording using FFmpeg to repair partial WAV headers
3. **Processing thread**: Handles final transcription and AI summarization after recording stops
4. **Model preload thread**: Loads Whisper model in background (1 second delay after init)

### Audio Pipeline

1. **Capture**: Records at 16kHz (Whisper's preferred rate) using `sounddevice` library
2. **Atomic writing**: Writes to `.part.wav` file, renames to `.wav` only when complete
3. **Live transcription**: Uses FFmpeg to copy/repair growing `.part` file for intermediate transcription
4. **Final transcription**: Whisper processes complete WAV file with timestamped segments
5. **Summarization**: Sends transcript (and optionally audio file) to LLM for structured summary

### Device Detection

- Auto-detects available audio input devices on startup and re-detects before each recording
- Looks for specific devices: default microphone, BlackHole (for system audio), BBrew Hybrid (aggregate device)
- Falls back gracefully if specialized devices not found
- On macOS, opens Audio MIDI Setup if hybrid device requested but not found

### Configuration System

**Config file**: `audio_config.ini`
- API keys for OpenAI, Anthropic, Gemini
- Default LLM selection (auto-detection or manual)
- Ollama model name (default: `llama3:8b`)
- Gemini model name (default: `gemini-2.0-flash-exp`)
- Recording history directory (default: `~/Documents/Audio Recordings`)

**History file**: `audio_history.json`
- Stores all recording sessions with transcripts, summaries, tasks, and metadata
- Loaded on app startup, updated after each recording

### LLM Integration

**Gemini API** (`_summarize_with_gemini` method):
- Uses Google GenAI v1 SDK (`google-genai` package)
- Supports audio file upload for cloud-based speaker diarization
- Returns structured JSON with: title, executive_summary, speaker_info, highlights, full_summary_sections, tasks
- Configurable "Deep Think" reasoning mode via `reasoning_level` setting
- Falls back to text-only if audio upload fails

**Ollama** (basic implementation in `generate_summary`):
- Currently shows placeholder messages
- Designed to work with local LLM at `http://localhost:11434`
- Model configurable in `audio_config.ini`

## Important Implementation Details

### Audio Recording Challenges
- **Atomic writes**: Always write to `.part` file first, then rename to avoid corrupting files that might be read mid-write
- **Live transcription**: Use FFmpeg to repair partial WAV headers since growing files have invalid header frame counts
- **Sample rate**: Always use 16kHz for Whisper compatibility
- **Device persistence**: Re-detect devices before each recording to handle plug/unplug events

### Model Loading
- Whisper model loads asynchronously on first use
- Preload triggered 1 second after backend init to avoid blocking UI startup
- Recording attempts during model load show warning status
- Set `model_loading` flag to prevent concurrent loads

### API Key Handling
- Config parser strips quotes from API keys (users sometimes add them manually)
- Gemini key validation: `raw_key.strip().replace('"', '').replace("'", "")`

### Error Handling
- Uses logging to `app_debug.log` (DEBUG level) and `app_verify.log`
- Backend returns error summaries on failure rather than raising exceptions
- UI callbacks are optional (checked before calling)

## Development Notes

- **Python version**: Uses Python 3 with virtual environment recommended
- **macOS specific**: Homebrew Python doesn't include tkinter; use `main_desktop.py` instead
- **Dependencies**: FFmpeg required for Whisper, PortAudio for PyAudio
- **Privacy**: All temp files created in system temp directory and deleted after processing
- **Chaos engineering**: `chaos_engineering.py` and `main_chaos.py` exist for testing system resilience

## Testing Approach

Tests are utility scripts rather than unit tests:
- `test_audio_recording.py`: Lists devices and attempts 5-second recording
- `test_mic_permission.py`: Validates microphone access
- `test_chaos_logic.py`: Tests chaos engineering features

No formal test runner (pytest/unittest) is currently used.
