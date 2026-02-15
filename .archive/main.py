#!/usr/bin/env python3
"""
Audio Summary App
Records audio, transcribes it locally with Whisper, and summarizes with Ollama
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import wave
import pyaudio
import json
import requests
import whisper
import os
import tempfile
from datetime import datetime


class AudioSummaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Summary App")
        self.root.geometry("800x600")
        
        # Audio recording variables
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.temp_audio_file = None
        
        # Load Whisper model (lazy loading)
        self.whisper_model = None
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Audio Summary App", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        self.record_button = ttk.Button(
            button_frame, 
            text="Start Recording", 
            command=self.toggle_recording
        )
        self.record_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_label = ttk.Label(button_frame, text="Ready to record")
        self.status_label.pack(side=tk.LEFT)
        
        # Text area for transcript and summary
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Transcript tab
        transcript_frame = ttk.Frame(notebook)
        notebook.add(transcript_frame, text="Transcript")
        
        self.transcript_text = scrolledtext.ScrolledText(
            transcript_frame,
            wrap=tk.WORD,
            width=70,
            height=20,
            state=tk.DISABLED
        )
        self.transcript_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Summary tab
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Summary")
        
        self.summary_text = scrolledtext.ScrolledText(
            summary_frame,
            wrap=tk.WORD,
            width=70,
            height=20,
            state=tk.DISABLED
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording audio from the microphone"""
        self.is_recording = True
        self.record_button.config(text="Stop & Process")
        self.status_label.config(text="Recording...")
        
        # Clear previous content
        self.update_text_widget(self.transcript_text, "")
        self.update_text_widget(self.summary_text, "")
        
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()
    
    def stop_recording(self):
        """Stop recording and process the audio"""
        self.is_recording = False
        self.record_button.config(text="Processing...", state=tk.DISABLED)
        self.status_label.config(text="Processing audio...")
        
        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join()
        
        # Process the recorded audio in a separate thread
        processing_thread = threading.Thread(target=self.process_audio)
        processing_thread.start()
    
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
            
            frames = []
            
            while self.is_recording:
                data = stream.read(CHUNK)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Save the recorded data as a WAV file
            with wave.open(self.temp_audio_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                
        finally:
            p.terminate()
    
    def load_whisper_model(self):
        """Load Whisper model if not already loaded"""
        if self.whisper_model is None:
            self.status_label.config(text="Loading Whisper model...")
            self.root.update()
            self.whisper_model = whisper.load_model("base")
    
    def process_audio(self):
        """Transcribe and summarize the recorded audio"""
        try:
            # Load Whisper model
            self.load_whisper_model()
            
            # Transcribe audio
            self.status_label.config(text="Transcribing audio...")
            self.root.update()
            
            result = self.whisper_model.transcribe(self.temp_audio_file)
            transcript = result["text"]
            
            # Display transcript
            self.update_text_widget(self.transcript_text, transcript)
            
            # Generate summary
            self.status_label.config(text="Generating summary...")
            self.root.update()
            
            summary = self.generate_summary(transcript)
            
            # Display summary
            self.update_text_widget(self.summary_text, summary)
            
        except Exception as e:
            error_message = f"Error processing audio: {str(e)}"
            self.update_text_widget(self.summary_text, error_message)
        
        finally:
            # Clean up temporary audio file
            if self.temp_audio_file and os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)
                self.temp_audio_file = None
            
            # Reset UI
            self.status_label.config(text="Ready to record")
            self.record_button.config(text="Start Recording", state=tk.NORMAL)
    
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
            return f"Error generating summary: {str(e)}"
    
    def update_text_widget(self, widget, text):
        """Update a text widget from any thread"""
        self.root.after(0, lambda: self._update_text_widget_safe(widget, text))
    
    def _update_text_widget_safe(self, widget, text):
        """Safely update a text widget"""
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(1.0, text)
        widget.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSummaryApp(root)
    root.mainloop()