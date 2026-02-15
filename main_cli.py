#!/usr/bin/env python3
"""
Audio Summary App - Command Line Version
Records audio, transcribes it locally with Whisper, and summarizes with Ollama
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
import signal
import sys


class AudioSummaryCLI:
    def __init__(self):
        self.is_recording = False
        self.temp_audio_file = None
        self.whisper_model = None
        
    def record_audio(self):
        """Record audio from the microphone"""
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        # Create temporary file for audio
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.temp_audio_file = os.path.join(temp_dir, f"audio_recording_{timestamp}.wav")
        
        print(f"Recording to: {self.temp_audio_file}")
        print("(Press Ctrl+C to stop recording)")
        
        p = pyaudio.PyAudio()
        
        try:
            # Try to find the default input device
            device_info = None
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    device_info = info
                    break
            
            # Use default device settings if specific device not found
            input_device = device_info['index'] if device_info else None
            
            stream = p.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          input_device_index=input_device,
                          frames_per_buffer=CHUNK)
            
            print(f"Using input device: {device_info['name'] if device_info else 'Default'}")
            
            frames = []
            
            try:
                while self.is_recording:
                    data = stream.read(CHUNK)
                    frames.append(data)
            except KeyboardInterrupt:
                print("\nStopping recording...")
            
            stream.stop_stream()
            stream.close()
            
            # Save the recorded data as a WAV file
            with wave.open(self.temp_audio_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            
            print(f"Recording saved. Duration: {len(frames) * CHUNK / RATE:.2f} seconds")
                
        finally:
            p.terminate()
    
    def load_whisper_model(self):
        """Load Whisper model if not already loaded"""
        if self.whisper_model is None:
            print("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
            print("Whisper model loaded!")
    
    def transcribe_audio(self):
        """Transcribe the recorded audio"""
        self.load_whisper_model()
        
        print("Transcribing audio...")
        result = self.whisper_model.transcribe(self.temp_audio_file)
        transcript = result["text"]
        
        print("\n" + "="*50)
        print("TRANSCRIPT:")
        print("="*50)
        print(transcript)
        print("="*50)
        
        return transcript
    
    def generate_summary(self, transcript):
        """Generate summary using Ollama"""
        print("Generating summary...")
        
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
            summary = result.get("response", "No summary generated")
            
            print("\n" + "="*50)
            print("SUMMARY:")
            print("="*50)
            print(summary)
            print("="*50)
            
            return summary
            
        except requests.exceptions.ConnectionError:
            error_msg = "Error: Could not connect to Ollama. Please ensure Ollama is running on localhost:11434"
            print(f"\n{error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Error generating summary: {str(e)}"
            print(f"\n{error_msg}")
            return error_msg
    
    def run(self):
        """Run the CLI application"""
        print("Audio Summary App - Command Line Version")
        print("="*50)
        print("This app will record audio from your microphone,")
        print("transcribe it with Whisper, and summarize with Ollama.")
        print()
        
        # Check if Ollama is running
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
        except requests.exceptions.ConnectionError:
            print("WARNING: Could not connect to Ollama at localhost:11434")
            print("Please start Ollama with: ollama serve")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return
        
        print("Press Enter to start recording (or Ctrl+C to quit)...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nExiting...")
            return
        
        self.is_recording = True
        recording_thread = threading.Thread(target=self.record_audio)
        recording_thread.start()
        
        try:
            recording_thread.join()
        except KeyboardInterrupt:
            self.is_recording = False
            recording_thread.join()
            print("\nRecording stopped.")
            return
        
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            # Transcribe
            transcript = self.transcribe_audio()
            
            # Generate summary
            summary = self.generate_summary(transcript)
            
            # Clean up
            os.remove(self.temp_audio_file)
            self.temp_audio_file = None
            
            print(f"\nTemporary files cleaned up.")


if __name__ == "__main__":
    app = AudioSummaryCLI()
    app.run()