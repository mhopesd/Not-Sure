@echo off
echo Audio Summary App - Setup Script
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3 from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Check if Ollama is installed
ollama --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Ollama is installed
) else (
    echo.
    echo WARNING: Ollama is not installed or not in PATH.
    echo Please download and install Ollama from https://ollama.com
)

echo.
echo Setup complete!
echo.
echo To run the application:
echo 1. Make sure Ollama is running: ollama serve
echo 2. Pull the Llama 3 model (first time only): ollama pull llama3:8b
echo 3. Activate virtual environment: venv\Scripts\activate
echo 4. Run the app: python main.py
echo.
pause