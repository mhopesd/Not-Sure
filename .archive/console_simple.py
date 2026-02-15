#!/usr/bin/env python3
"""
Audio Summary App - Simple Console Version
Records audio, transcribes it locally with Whisper, and summarizes with Ollama
Includes chat history functionality
Uses Ctrl+C to stop recording
"""

import threading
import wave
import pyaudio
import json
import requests
import whisper
import os
import tempfile
from datetime import datetime
import sys


class SimpleConsoleApp:
    def __init__(self):
        # Audio recording variables
        self.is_recording = False
        self.recording_thread = None
        self.temp_audio_file = None
        
        # Whisper model
        self.whisper_model = None
        
        # History
        self.history_file = "audio_history.json"
        self.chat_history = []
        self.load_history()
        
        print("\n" + "="*60)
        print(" Audio Summary App - Console Version")
        print("="*60)
        
    def show_menu(self):
        """Show main menu"""
        while True:
            print("\n" + "="*60)
            print(" Audio Summary App")
            print("="*60)
            print("1. Start Recording")
            print("2. View History")
            print("3. Clear History")
            print("4. Exit")
            print("-"*60)
            print("\nNote: Press Ctrl+C to stop recording")
            
            try:
                choice = input("\nEnter your choice (1-4): ").strip()
                
                if choice == '1':
                    self.recording_workflow()
                elif choice == '2':
                    self.view_history()
                elif choice == '3':
                    self.clear_history()
                elif choice == '4':
                    print("\nGoodbye!")
                    break
                else:
                    print("\nInvalid choice. Please enter 1-4.")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
                
    def recording_workflow(self):
        """Handle the recording workflow"""
        print("\n" + "="*60)
        print(" Recording Mode")
        print("="*60)
        print("\nPress ENTER to start recording...")
        print("(Press Ctrl+C to stop recording)")
        
        try:
            input()
            self.start_recording()
            
            # Wait for Ctrl+C to stop
            print("\n● RECORDING... Press Ctrl+C to stop")
            
            # Wait until Ctrl+C is pressed
            while self.is_recording:
                import time
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n■ Stopping recording...")
            self.stop_recording()
            
    def start_recording(self):
        """Start recording audio"""
        self.is_recording = True
        
        # Clear current session
        self.current_transcript = ""
        self.current_summary = ""
        
        # Start recording in separate thread
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()
        
    def stop_recording(self):
        """Stop recording and process"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        print("\nProcessing recording...")
        
        # Wait for recording to finish
        if self.recording_thread:
            self.recording_thread.join()
            
        # Process the audio
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            self.process_audio()
            
    def record_audio(self):
        """Record audio from microphone"""
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.temp_audio_file = os.path.join(temp_dir, f"audio_recording_{timestamp}.wav")
        
        p = pyaudio.PyAudio()
        
        try:
            # Find input device
            device_info = None
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    device_info = info
                    break
                    
            input_device = device_info['index'] if device_info else None
            
            stream = p.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          input_device_index=input_device,
                          frames_per_buffer=CHUNK)
            
            frames = []
            while self.is_recording:
                data = stream.read(CHUNK)
                frames.append(data)
                
            stream.stop_stream()
            stream.close()
            
            # Save WAV file
            with wave.open(self.temp_audio_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                
        finally:
            p.terminate()
            
    def load_whisper_model(self):
        """Load Whisper model if not loaded"""
        if self.whisper_model is None:
            print("Loading Whisper model (this may take a moment)...")
            self.whisper_model = whisper.load_model("base")
            print("Whisper model loaded!")
            
    def process_audio(self):
        """Process the recorded audio"""
        try:
            # Load Whisper
            self.load_whisper_model()
            
            # Transcribe
            print("Transcribing audio...")
            result = self.whisper_model.transcribe(self.temp_audio_file)
            transcript = result["text"]
            self.current_transcript = transcript
            
            # Display transcript
            print("\n" + "="*60)
            print(" TRANSCRIPT")
            print("="*60)
            print(transcript)
            print("="*60)
            
            # Generate summary
            print("\nGenerating summary...")
            summary = self.generate_summary(transcript)
            self.current_summary = summary
            
            # Display summary
            print("\n" + "="*60)
            print(" SUMMARY")
            print("="*60)
            print(summary)
            print("="*60)
            
            # Save to history
            self.save_to_history(transcript, summary)
            print("\n✓ Recording saved to history!")
            
        except Exception as e:
            print(f"\nError processing audio: {e}")
            
        finally:
            # Clean up
            if self.temp_audio_file and os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)
                self.temp_audio_file = None
                
            # Pause before returning to menu
            input("\nPress ENTER to continue...")
            
    def generate_summary(self, transcript):
        """Generate summary using Ollama"""
        try:
            url = "http://localhost:11434/api/generate"
            
            prompt = f"""You are an expert assistant who summarizes conversations. Please provide a concise summary of the following transcript. Focus on key decisions, main topics, and any action items mentioned.

Transcript:
"{transcript}"

Summary:"""
            
            payload = {
                "model": "llama3:8b",
                "stream": False,
                "prompt": prompt
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "No summary generated")
            
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to Ollama. Please ensure Ollama is running on localhost:11434"
        except Exception as e:
            return f"Error generating summary: {e}"
            
    def save_to_history(self, transcript, summary):
        """Save recording to history"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = {
            "timestamp": timestamp,
            "transcript": transcript,
            "summary": summary
        }
        
        self.chat_history.insert(0, entry)
        if len(self.chat_history) > 50:
            self.chat_history = self.chat_history[:50]
            
        self.save_history()
        
    def load_history(self):
        """Load history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.chat_history = json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            self.chat_history = []
            
    def save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
            
    def view_history(self):
        """View saved recordings"""
        if not self.chat_history:
            print("\nNo recording history found.")
            input("\nPress ENTER to continue...")
            return
            
        print("\n" + "="*60)
        print(" Recording History")
        print("="*60)
        
        for i, entry in enumerate(self.chat_history, 1):
            timestamp = entry.get('timestamp', 'Unknown')
            summary = entry.get('summary', 'No summary')
            
            print(f"\n{i}. {timestamp}")
            print(f"   Summary: {summary[:100]}...")
            
        print("\n" + "="*60)
        
        try:
            choice = input("\nEnter recording number to view details (or 0 to go back): ").strip()
            
            if choice.isdigit() and choice != '0':
                index = int(choice) - 1
                if 0 <= index < len(self.chat_history):
                    self.view_recording_details(index)
                else:
                    print("\nInvalid recording number.")
                    input("\nPress ENTER to continue...")
                    
        except ValueError:
            print("\nInvalid input.")
            input("\nPress ENTER to continue...")
            
    def view_recording_details(self, index):
        """View details of a specific recording"""
        entry = self.chat_history[index]
        
        print("\n" + "="*60)
        print(f" Recording from {entry.get('timestamp', 'Unknown')}")
        print("="*60)
        
        print("\nTRANSCRIPT:")
        print("-"*40)
        print(entry.get('transcript', 'No transcript'))
        
        print("\nSUMMARY:")
        print("-"*40)
        print(entry.get('summary', 'No summary'))
        print("="*60)
        
        input("\nPress ENTER to continue...")
        
    def clear_history(self):
        """Clear all history"""
        if not self.chat_history:
            print("\nNo history to clear.")
            input("\nPress ENTER to continue...")
            return
            
        confirm = input("\nAre you sure you want to delete all recording history? (y/N): ").strip().lower()
        
        if confirm == 'y':
            self.chat_history = []
            self.save_history()
            print("\n✓ History cleared!")
        else:
            print("\nHistory not cleared.")
            
        input("\nPress ENTER to continue...")
        
    def run(self):
        """Run the app"""
        try:
            self.show_menu()
        except KeyboardInterrupt:
            print("\n\nGoodbye!")


if __name__ == "__main__":
    app = SimpleConsoleApp()
    app.run()