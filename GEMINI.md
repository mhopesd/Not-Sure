# GEMINI.md

## Project Overview

This is a Python-based desktop application for audio summarization. It allows users to record audio, which is then transcribed locally using OpenAI's Whisper model. The resulting transcript is summarized by a locally running Large Language Model (LLM) via Ollama.

The project is designed with privacy in mind, as all processing is done locally on the user's machine.

The application has three main versions:
- A modern graphical user interface (GUI) built with `dearpygui` (`main_desktop.py`).
- A command-line interface (CLI) version (`main_cli.py`).
- An older GUI version built with `tkinter` (`main.py`).

## Building and Running

### 1. Setup

The project includes a setup script (`setup.sh`) for macOS that automates the installation of dependencies. For other operating systems, the `README.md` provides manual setup instructions.

**macOS Setup:**
```bash
./setup.sh
```

This script will:
- Install Homebrew (if not present).
- Install `ffmpeg` and `portaudio` using Homebrew.
- Install Ollama using Homebrew.
- Create a Python virtual environment in `venv/`.
- Install all required Python packages from `requirements.txt` and `dearpygui`.

### 2. Running the Application

Before running the application, ensure that the Ollama server is running in a separate terminal:

```bash
ollama serve
```

If it's the first time, you also need to pull the LLM model:

```bash
ollama pull llama3:8b
```

To run the application, first activate the virtual environment:

```bash
source venv/bin/activate
```

Then, choose one of the following options:

**Recommended Desktop GUI:**
```bash
python main_desktop.py
```

**Command-Line Version:**
```bash
python main_cli.py
```

**Original Tkinter Version:**
```bash
python main.py
```

### 3. Testing

A test script is provided to verify that all dependencies are correctly installed:

```bash
python test_macos.py
```

## Development Conventions

- The project is written in Python.
- It uses a `requirements.txt` file to manage Python dependencies.
- The application is structured with different entry points for the GUI and CLI versions.
- The core logic for audio recording, transcription, and summarization is shared across the different versions.
- Temporary audio files are created in the system's temporary directory and are deleted after processing.
- The application interacts with the Ollama API at `http://localhost:11434`.
- The default LLM model is `llama3:8b`, but this can be changed in the `generate_summary` function in the respective `main` files.
- Threading is used to keep the UI responsive during long-running tasks like audio recording and processing.
