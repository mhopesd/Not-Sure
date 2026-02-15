#!/usr/bin/env python3
"""
Convenient launcher for the Audio Summary App
Automatically checks dependencies and launches the application
"""

import subprocess
import sys
import os


def check_ollama():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False


def main():
    print("Audio Summary App - Launcher")
    print("============================")
    print()
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Activating virtual environment...")
        if os.name == 'nt':  # Windows
            activate_cmd = os.path.join(os.getcwd(), "venv", "Scripts", "activate.bat")
            if os.path.exists(activate_cmd):
                os.system(f'call {activate_cmd} && python main.py')
                return
        else:  # Unix/macOS
            activate_cmd = os.path.join(os.getcwd(), "venv", "bin", "activate")
            if os.path.exists(activate_cmd):
                os.execv("/bin/bash", ["/bin/bash", "-c", f"source {activate_cmd} && python main.py"])
                return
    
    # Check if Ollama is running
    print("Checking Ollama...")
    if not check_ollama():
        print("WARNING: Ollama is not running!")
        print("Please start Ollama in a separate terminal:")
        print("  ollama serve")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Launch the main application
    print("Launching Audio Summary App...")
    print()
    try:
        from main import AudioSummaryApp
        import tkinter as tk
        root = tk.Tk()
        app = AudioSummaryApp(root)
        root.mainloop()
    except ImportError as e:
        print(f"Error: Missing dependencies - {e}")
        print("Please run setup.py or install requirements:")
        print("  pip install -r requirements.txt")
    except Exception as e:
        print(f"Error launching application: {e}")


if __name__ == "__main__":
    main()