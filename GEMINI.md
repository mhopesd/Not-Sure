# GEMINI.md

## Project Overview

**NotSure** is a privacy-focused meeting assistant that records audio, transcribes it locally using OpenAI's Whisper, and generates AI-powered summaries and insights. It supports both Ollama (local) and Google Gemini as LLM providers.

### Architecture

The application uses a **client-server architecture**:

- **Python Backend** (`api_server.py`) — A FastAPI server that wraps the core `EnhancedAudioApp` class from `backend.py`. Provides REST and WebSocket endpoints for recording, transcription, summarization, meeting history, live insights, OAuth integrations, and more. Runs on `http://localhost:8000`.
- **React Frontend** (`Personalassistantappmainpage-main/`) — A Vite + React single-page application that provides the main dashboard UI. Connects to the backend via REST API and WebSockets for live updates.
- **Electron Desktop Wrapper** (`desktop/`) — An Electron app (`main.js`) that manages the Python backend as a child process, hosts the React frontend in a native window, and provides a macOS menu bar tray with recording controls, live insights, and meeting-app detection.
- **Menu Bar App** (`menubar_app.py`) — A standalone macOS menu bar app built with `rumps` that connects to the backend API for quick recording access.

### Key Features

- Audio recording with microphone, system audio (BlackHole), or hybrid (BBrew) capture
- Live transcription via Whisper during recording
- Real-time conversation intelligence (meeting type detection, action items, decisions, sentiment)
- AI summarization via Gemini or Ollama
- Meeting history with search, tags, and filtering
- Journal with AI optimization
- People/speaker tracking across meetings
- Microsoft and Google OAuth integrations (calendar, email)
- Automatic meeting app detection (Zoom, Teams, Webex, etc.)
- macOS native notifications for action items and decisions

## Building and Running

### 1. Setup

**macOS Setup:**
```bash
./setup.sh
```

This installs Homebrew, `ffmpeg`, `portaudio`, Ollama, creates a Python venv, and installs packages from `requirements.txt`.

### 2. Running (Development)

**Option A: Electron app (recommended)**
```bash
# Terminal 1: Start the React frontend dev server
cd Personalassistantappmainpage-main
npm run dev

# Terminal 2: Launch Electron (starts backend automatically)
cd desktop
npm start
```

**Option B: Backend + frontend separately**
```bash
# Terminal 1: Start the FastAPI backend
source venv/bin/activate
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000

# Terminal 2: Start the React frontend
cd Personalassistantappmainpage-main
npm run dev
# Open http://localhost:5173
```

**Option C: Menu bar app**
```bash
source venv/bin/activate
python menubar_app.py
```

**Option D: CLI**
```bash
source venv/bin/activate
python main_cli.py
```

### 3. Building for Production

The `desktop/build_app.sh` script handles the full build pipeline:
```bash
cd desktop
./build_app.sh
```

This will:
1. Build the React frontend (`npm run build`)
2. Copy the build output to `desktop/frontend/`
3. Install Electron dependencies
4. Generate the `.icns` icon from `icon.png`
5. Package as a macOS `.app` with `electron-builder`
6. Copy to `/Applications/NotSure.app`

### 4. Testing

```bash
python test_macos.py
```

## Project Structure

```
audio-summary-app/
├── api_server.py              # FastAPI backend (REST + WebSocket endpoints)
├── backend.py                 # Core EnhancedAudioApp class (recording, transcription, summarization)
├── audio_config.ini           # App configuration (API keys, LLM provider, model)
├── audio_history.json         # Persisted meeting history
├── requirements.txt           # Python dependencies
├── menubar_app.py             # Standalone rumps menu bar app
├── integrations/              # OAuth integrations
│   ├── oauth_manager.py       # Token management
│   ├── microsoft_integration.py
│   └── google_integration.py
├── desktop/                   # Electron wrapper
│   ├── main.js                # Electron main process (backend mgmt, tray, meeting detection)
│   ├── preload.js             # Context bridge for renderer
│   ├── package.json           # Electron + electron-builder config
│   ├── build_app.sh           # Full production build script
│   ├── icons/                 # App icons (icon.png, icon.icns)
│   └── frontend/              # Built React app (production)
├── Personalassistantappmainpage-main/  # React frontend source
│   ├── src/                   # React components, pages, hooks
│   ├── vite.config.ts         # Vite build configuration
│   └── package.json
├── main_cli.py                # CLI entry point
├── main_desktop.py            # Legacy tkinter launcher (deprecated)
└── gui_modern.py              # Legacy tkinter GUI (deprecated)
```

## Development Conventions

- **Python backend**: Core logic lives in `backend.py` (`EnhancedAudioApp` class). The API layer in `api_server.py` wraps it with FastAPI endpoints. Configuration is via `audio_config.ini`.
- **React frontend**: Uses Vite for dev/build. Components connect to `http://localhost:8000/api/*` endpoints. WebSockets at `/ws` provide live transcript, audio levels, and status updates.
- **Electron**: In dev mode, loads `http://localhost:5173` (Vite dev server). In production, loads built files from `desktop/frontend/`. Manages the Python backend as a child process.
- **LLM providers**: Gemini (`google-genai`) is the primary provider. Ollama (`http://localhost:11434`) is the local fallback. Configured via `audio_config.ini` under `[SETTINGS] default_llm` and `[API_KEYS] gemini`.
- **OAuth**: Microsoft (MSAL) and Google tokens are managed by `integrations/oauth_manager.py` and persisted locally.
- **Threading**: Audio recording and processing use background threads to keep servers and UI responsive.
