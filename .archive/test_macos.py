#!/usr/bin/env python3
"""
Test script to verify all dependencies are properly installed on macOS
"""

import sys
import subprocess
import platform


def test_import(import_name, package_name=None):
    """Test if a Python package can be imported"""
    try:
        __import__(import_name)
        print(f"✓ {package_name or import_name} is installed")
        return True
    except ImportError as e:
        print(f"✗ {package_name or import_name} is NOT installed: {e}")
        return False


def test_command(command):
    """Test if a command line tool is available"""
    try:
        result = subprocess.run([command, "--version"], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print(f"✓ {command} is installed ({version})")
            return True
        else:
            print(f"✗ {command} not found")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"✗ {command} is NOT installed or not in PATH")
        return False


def main():
    print("macOS Compatibility Test")
    print("=" * 40)
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print()
    
    print("Testing Python packages...")
    print("-" * 40)
    
    all_good = True
    
    # Test Python packages
    packages = [
        ("tkinter", None),
        ("whisper", "openai-whisper"),
        ("pyaudio", None),
        ("requests", None),
        ("torch", None),
        ("torchaudio", None),
        ("numpy", None),
    ]
    
    for import_name, package_name in packages:
        if not test_import(import_name, package_name):
            all_good = False
    
    print()
    print("Testing command line tools...")
    print("-" * 40)
    
    # Test command line tools
    commands = ["python3", "pip3"]
    
    if platform.system() == "Darwin":  # macOS
        commands.extend(["brew", "ffmpeg", "ollama"])
    
    for cmd in commands:
        if not test_command(cmd):
            all_good = False
    
    print()
    print("=" * 40)
    if all_good:
        print("✓ All dependencies are satisfied!")
        print()
        print("You can run the application with:")
        print("  python main.py")
        print()
        print("Don't forget to start Ollama first:")
        print("  ollama serve")
    else:
        print("✗ Some dependencies are missing.")
        print()
        print("Please run the setup script:")
        print("  ./setup.sh")
        print()
        print("Or install missing dependencies manually.")


if __name__ == "__main__":
    main()