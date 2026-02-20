# NotSure — AI Meeting Assistant

> **I'm not a professional developer.** I'm just someone who realized too much of my life was slipping through the cracks — conversations I couldn't fully remember, action items that got lost, ideas that disappeared the moment a meeting ended. I built NotSure because I needed a tool that would help me stay organized without changing how I naturally work. If you feel the same way, maybe this helps you too.

---

## The Idea

Modern life is full of meetings, calls, and conversations — but most of what's said disappears the moment they end. Important details, commitments, and ideas get lost in the noise. Traditional note-taking forces you to split your attention between listening and writing, and you inevitably miss things.

**NotSure** solves this by sitting quietly in the background during your meetings, recording everything, and then using AI to give you:

- A full searchable **transcript** of what was said
- An intelligent **summary** with key takeaways, decisions, and action items
- A **meeting history** you can search, tag, and revisit anytime

The name "NotSure" comes from that feeling we all get — *"Wait, what did they say exactly?"* — and never having a good answer. Now you do.

## What It Does

🎙️ **Records** — Captures your microphone and/or system audio during meetings (works with Zoom, Teams, Google Meet, or any audio source)

📝 **Transcribes** — Converts speech to text locally using OpenAI's Whisper model — nothing leaves your machine

🧠 **Summarizes** — Uses AI (Google Gemini or local Ollama models) to extract the important parts: key points, decisions, action items, and a concise summary

📚 **Organizes** — Searchable meeting history with tags, date grouping, and full transcripts you can revisit anytime

📓 **Journal** — Built-in journal with AI-powered optimization to help you reflect and plan

📅 **Integrates** — Optional Google and Microsoft calendar/email integration to keep everything connected

🖥️ **Native Desktop App** — An Electron-based macOS application with a rich React frontend dashboard

⚙️ **Menu Bar Integration** — Quick access recording controls directly from the macOS menu bar via `rumps`

## Privacy First

**Everything runs locally on your machine.** Your audio never leaves your computer. Transcription happens on-device via Whisper. Summaries are generated either through a local LLM (Ollama) or via API calls you control. There's no cloud service, no account required, no data collection.

## Getting Started

### Prerequisites

- **macOS** (tested on Apple Silicon)
- **Python 3.10+** with a virtual environment
- **Node.js 18+** and npm
- **Ollama** (optional, for local LLM summaries) or a **Gemini API key**
- **ffmpeg** and **portaudio** (installed automatically by the setup script)

### Quick Setup

```bash
# Clone the repo
git clone https://github.com/mhopesd/NotSure.git
cd NotSure

# Run the macOS setup script (installs dependencies, creates venv)
./setup.sh

# Copy the example config and add your API key
cp audio_config.ini.example audio_config.ini
# Edit audio_config.ini to add your Gemini API key (or leave blank for Ollama)

# Install frontend dependencies
cd Personalassistantappmainpage-main
npm install
cd ..
```

### Running

**Option 1: Desktop App (Recommended)**

```bash
# Build and install the macOS app
cd desktop
bash build_app.sh

# Then launch NotSure from your Applications folder
```

**Option 2: Dev Mode**

```bash
# Terminal 1: Start the backend
source venv/bin/activate
python api_server.py

# Terminal 2: Start the frontend
cd Personalassistantappmainpage-main
npm run dev

# Open http://localhost:5173 in your browser
```

**Option 3: CLI Only**

```bash
source venv/bin/activate
python main_cli.py
```

### Using Ollama (Fully Local)

If you want everything to stay on your machine — including the AI summaries — install Ollama:

```bash
brew install ollama
ollama serve          # In a separate terminal
ollama pull llama3:8b # First time only
```

Then set `default_llm = ollama` in your `audio_config.ini`.

## Project Structure

```
├── api_server.py          # FastAPI backend (REST + WebSocket endpoints)
├── backend.py             # Core logic: recording, transcription, summarization
├── enhanced_recorder_v4.py# Audio capture engine
├── menubar_app.py         # Standalone rumps macOS menu bar app for quick access
├── integrations/          # Google & Microsoft calendar/email integrations
├── desktop/               # Electron desktop wrapper (`main.js`, `build_app.sh`)
│   └── frontend/          # Built React frontend output
├── Personalassistantappmainpage-main/  # React frontend source (Vite + TypeScript)
│   └── src/components/    # All UI sections (History, Recording, Journal, etc.)
├── audio_config.ini.example  # Template config (copy to audio_config.ini)
└── setup.sh               # macOS dependency installer
```

## A Note on the Code

This project was built by someone learning as they go, with generous help from AI coding assistants. The code isn't perfect — it's a working tool that solves a real problem in my life. If you're a developer and see ways to improve it, PRs are welcome. If you're not a developer and just want to use it, that's exactly who this was built for.

## License

MIT — do whatever you want with it.