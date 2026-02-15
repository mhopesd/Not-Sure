#!/bin/bash

echo "Audio Summary App - Setup Script"
echo "================================"
echo

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if Homebrew is installed (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install FFmpeg and PortAudio (for PyAudio)
    echo "Installing FFmpeg and PortAudio..."
    brew install ffmpeg portaudio
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        echo "Installing Ollama..."
        brew install ollama
        
        echo "NOTE: You may need to start Ollama manually after installation:"
        echo "      Run: ollama serve"
    fi
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip

# Install PyAudio
pip install PyAudio

# Install main dependencies
pip install -r requirements.txt

# Install Dear PyGui for desktop GUI
pip install dearpygui

echo
echo "Setup complete!"
echo
echo "To run the application:"
echo "1. Make sure Ollama is running: ollama serve"
echo "2. Pull the Llama 3 model (first time only): ollama pull llama3:8b"
echo "3. Activate virtual environment: source venv/bin/activate"
echo "4. Run the desktop app (recommended): python main_desktop.py"
echo "   Alternative - Command line version: python main_cli.py"