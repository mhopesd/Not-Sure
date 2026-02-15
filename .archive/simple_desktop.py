#!/usr/bin/env python3
"""
Audio Summary App - Simple Desktop Version with History
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
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


class SimpleAudioSummaryApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audio Summary App")
        self.root.geometry("900x700")
        
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
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        # Title
        title = ttk.Label(self.root, text="Audio Summary App", font=("Arial", 18, "bold"))
        title.pack(pady=10)
        
        # Recording controls
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10)
        
        self.start_button = ttk.Button(
            control_frame, 
            text="Start Recording", 
            command=self.start_recording,
            width=15
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            control_frame, 
            text="Stop Recording", 
            command=self.stop_recording,
            width=15,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="Ready to record", foreground="green")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Current session tab
        current_frame = ttk.Frame(notebook)
        notebook.add(current_frame, text="Current Recording")
        
        # Transcript section
        ttk.Label(current_frame, text="Transcript:", font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.transcript_text = scrolledtext.ScrolledText(
            current_frame,
            wrap=tk.WORD,
            height=12
        )
        self.transcript_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Summary section
        ttk.Label(current_frame, text="Summary:", font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=5, pady=(10, 0))
        self.summary_text = scrolledtext.ScrolledText(
            current_frame,
            wrap=tk.WORD,
            height=8
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # History tab
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="History")
        
        # History controls
        history_controls = ttk.Frame(history_frame)
        history_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(history_controls, text="Previous Recordings:", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(history_controls, text="Clear History", command=self.clear_history).pack(side=tk.RIGHT)
        
        # History listbox and details frame
        history_container = ttk.Frame(history_frame)
        history_container.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Left side - history list
        list_frame = ttk.LabelFrame(history_container, text="Recordings", width=300)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        list_frame.pack_propagate(False)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=20)
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_select)
        scrollbar.config(command=self.history_listbox.yview)
        
        # Right side - recording details
        details_frame = ttk.LabelFrame(history_container, text="Recording Details")
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.details_label = ttk.Label(details_frame, text="Select a recording to view details")
        self.details_label.pack(anchor=tk.W, padx=5, pady=5)
        
        ttk.Label(details_frame, text="Transcript:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.history_transcript = scrolledtext.ScrolledText(
            details_frame,
            wrap=tk.WORD,
            height=10
        )
        self.history_transcript.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(details_frame, text="Summary:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.history_summary = scrolledtext.ScrolledText(
            details_frame,
            wrap=tk.WORD,
            height=6
        )
        self.history_summary.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Update history list
        self.update_history_list()
        
    def start_recording(self):
        """Start recording audio"""
        self.is_recording = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Recording...", foreground="red")
        
        # Clear current transcript and summary
        self.transcript_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        
        # Start recording in separate thread
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()
        
    def stop_recording(self):
        """Stop recording and process"""
        self.is_recording = False
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Processing...", foreground="blue")
        
        # Wait for recording to finish
        if self.recording_thread:
            self.recording_thread.join()
        
        # Start processing
        processing_thread = threading.Thread(target=self.process_audio)
        processing_thread.start()
        
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
            self.status_label.config(text="Loading Whisper model...", foreground="blue")
            self.root.update()
            self.whisper_model = whisper.load_model("base")
            
    def process_audio(self):
        """Process the recorded audio"""
        try:
            # Load Whisper
            self.load_whisper_model()
            
            # Transcribe
            self.status_label.config(text="Transcribing audio...", foreground="blue")
            self.root.update()
            
            result = self.whisper_model.transcribe(self.temp_audio_file)
            transcript = result["text"]
            
            # Display transcript
            self.transcript_text.insert(tk.END, transcript)
            self.transcript_text.see(tk.END)
            
            # Generate summary
            self.status_label.config(text="Generating summary...", foreground="blue")
            self.root.update()
            
            summary = self.generate_summary(transcript)
            
            # Display summary
            self.summary_text.insert(tk.END, summary)
            self.summary_text.see(tk.END)
            
            # Save to history
            self.save_to_history(transcript, summary)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process audio: {e}")
            
        finally:
            # Clean up
            if self.temp_audio_file and os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)
                self.temp_audio_file = None
            
            # Reset UI
            self.status_label.config(text="Ready to record", foreground="green")
            self.start_button.config(state=tk.NORMAL)
            
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
        self.update_history_list()
        
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
            
    def update_history_list(self):
        """Update the history listbox"""
        self.history_listbox.delete(0, tk.END)
        
        for entry in self.chat_history:
            timestamp = entry.get('timestamp', 'Unknown')
            summary_preview = entry.get('summary', 'No summary')[:50]
            if len(summary_preview) == 50:
                summary_preview += "..."
            self.history_listbox.insert(tk.END, f"{timestamp} - {summary_preview}")
            
    def on_history_select(self, event):
        """Handle history selection"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index < len(self.chat_history):
            entry = self.chat_history[index]
            
            timestamp = entry.get('timestamp', 'Unknown')
            self.details_label.config(text=f"Recording from {timestamp}")
            
            # Update transcript
            self.history_transcript.delete(1.0, tk.END)
            self.history_transcript.insert(tk.END, entry.get('transcript', ''))
            
            # Update summary
            self.history_summary.delete(1.0, tk.END)
            self.history_summary.insert(tk.END, entry.get('summary', ''))
            
    def clear_history(self):
        """Clear all history"""
        if messagebox.askyesno("Clear History", "Are you sure you want to delete all recording history?"):
            self.chat_history = []
            self.save_history()
            self.update_history_list()
            
            self.details_label.config(text="Select a recording to view details")
            self.history_transcript.delete(1.0, tk.END)
            self.history_summary.delete(1.0, tk.END)
            
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = SimpleAudioSummaryApp()
    app.run()